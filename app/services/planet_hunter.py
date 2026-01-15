"""
Planet Hunter Service - Exoplanet detection via BLS transit analysis.

Uses NASA's lightkurve library to analyze TESS light curves and detect
periodic transit signals consistent with exoplanets.

Algorithm:
    1. Fetch TESS light curve data for target star (TIC ID)
    2. Preprocess: normalize, remove outliers, flatten stellar variability
    3. Run Box Least Squares (BLS) periodogram to detect transit signals
    4. Extract best period, transit time, depth, duration
    5. Fold light curve at detected period for visualization
    6. Save candidate to database with visualization JSON
"""

import json
import logging
from typing import Optional, Dict, Any, List
import warnings

import numpy as np
from sqlalchemy.orm import Session

# Suppress lightkurve warnings about data gaps (common in TESS)
warnings.filterwarnings('ignore', category=UserWarning, module='lightkurve')

try:
    import lightkurve as lk
except ImportError:
    raise ImportError(
        "lightkurve not installed. Run: pip install lightkurve"
    )

from app.models_exoplanet import ExoplanetCandidate

logger = logging.getLogger(__name__)


class PlanetHunterService:
    """
    Exoplanet detection service using TESS light curves and BLS.
    
    Typical workflow:
        service = PlanetHunterService(db_session)
        candidate = service.analyze_tic_target("261136679")  # Known planet host
        if candidate:
            print(f"Found planet! Period: {candidate.period:.3f} days")
    """
    
    def __init__(self, db: Session):
        """
        Initialize the Planet Hunter service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def analyze_tic_target(
        self,
        tic_id: str,
        min_period: float = 0.5,
        max_period: float = 20.0,
        num_periods: int = 10000,
        save_to_db: bool = True
    ) -> Optional[ExoplanetCandidate]:
        """
        Analyze a TESS target for exoplanet transits using BLS.
        
        Args:
            tic_id: TESS Input Catalog ID (e.g., "261136679")
            min_period: Minimum orbital period to search (days)
            max_period: Maximum orbital period to search (days)
            num_periods: Number of trial periods for BLS
            save_to_db: Whether to save candidate to database
            
        Returns:
            ExoplanetCandidate object if detection found, None otherwise
            
        Example:
            >>> service = PlanetHunterService(db)
            >>> candidate = service.analyze_tic_target("261136679")
            >>> if candidate:
            >>>     print(f"Period: {candidate.period} days")
            >>>     print(f"Depth: {candidate.depth * 100}%")
        """
        logger.info(f"Starting planet hunt for TIC {tic_id}")
        
        try:
            # Step 1: Search for TESS light curve data
            logger.info(f"Searching MAST archive for TIC {tic_id}...")
            search_result = lk.search_lightcurve(
                f"TIC {tic_id}",
                mission="TESS",
                author="SPOC"  # Science Processing Operations Center
            )
            
            if len(search_result) == 0:
                logger.warning(f"No TESS data found for TIC {tic_id}")
                return None
            
            logger.info(f"Found {len(search_result)} TESS sectors for TIC {tic_id}")
            
            # Step 2: Download the first available sector
            logger.info("Downloading light curve data...")
            lc_collection = search_result.download()
            
            # If multiple sectors, use the first one (could also stitch)
            lc = lc_collection[0] if hasattr(lc_collection, '__getitem__') else lc_collection
            sector = search_result.table['observation'][0] if len(search_result) > 0 else None
            
            logger.info(f"Downloaded sector {sector}: {len(lc)} data points")
            
            # Step 3: Preprocess light curve
            logger.info("Preprocessing light curve...")
            lc = lc.normalize()  # Normalize flux to mean = 1
            lc = lc.remove_nans()  # Remove invalid data points
            lc = lc.remove_outliers(sigma=5)  # Remove 5-sigma outliers
            
            # Flatten to remove stellar variability (critical for transit detection)
            lc = lc.flatten(window_length=101)  # 101-point Savitzky-Golay filter
            
            logger.info(f"Cleaned light curve: {len(lc)} points remaining")
            
            if len(lc) < 100:
                logger.warning(f"Too few data points after cleaning: {len(lc)}")
                return None
            
            # Step 4: Run BLS periodogram
            logger.info(f"Running BLS periodogram (period range: {min_period}-{max_period} days)...")
            period_array = np.linspace(min_period, max_period, num_periods)
            
            periodogram = lc.to_periodogram(
                method='bls',
                period=period_array,
                frequency_factor=1.0
            )
            
            # Extract best-fit parameters
            best_period = periodogram.period_at_max_power.value
            max_power = periodogram.max_power.value
            
            # Get transit parameters
            transit_params = periodogram.get_transit_parameters()
            transit_time = transit_params['transit_time'].value
            duration_hours = transit_params['duration'].to('hour').value
            depth = transit_params['depth'].value
            
            logger.info(f"BLS Detection - Period: {best_period:.4f} days, "
                       f"Depth: {depth*100:.3f}%, Power: {max_power:.3f}")
            
            # Step 5: Fold light curve at detected period
            logger.info("Folding light curve for visualization...")
            folded_lc = lc.fold(period=best_period, epoch_time=transit_time)
            
            # Step 6: Extract visualization data (binned for smaller JSON)
            # Full resolution data
            phase_full = folded_lc.phase.value
            flux_full = folded_lc.flux.value
            
            # Bin to 500 points for cleaner visualization
            binned_lc = folded_lc.bin(bins=500)
            phase_binned = binned_lc.phase.value.tolist()
            flux_binned = binned_lc.flux.value.tolist()
            
            # Sort by phase for proper plotting
            sort_idx = np.argsort(phase_binned)
            phase_binned = [phase_binned[i] for i in sort_idx]
            flux_binned = [flux_binned[i] for i in sort_idx]
            
            # Calculate SNR (simple estimate: power / median absolute deviation)
            snr = max_power / np.median(np.abs(periodogram.power.value - np.median(periodogram.power.value)))
            
            # Count number of transits
            time_span = (lc.time.value[-1] - lc.time.value[0])
            num_transits = int(time_span / best_period)
            
            # Create visualization JSON
            visualization_data = {
                "phase_full": phase_full.tolist()[:1000],  # Limit to 1000 points
                "flux_full": flux_full.tolist()[:1000],
                "phase_binned": phase_binned,
                "flux_binned": flux_binned,
                "period": best_period,
                "epoch": transit_time,
                "depth": depth,
                "duration_hours": duration_hours
            }
            
            # Step 7: Create database record
            candidate = ExoplanetCandidate(
                source_id=tic_id,
                period=float(best_period),
                transit_time=float(transit_time),
                duration=float(duration_hours),
                depth=float(depth),
                power=float(max_power),
                snr=float(snr),
                num_transits=num_transits,
                visualization_json=json.dumps(visualization_data),
                mission="TESS",
                sector=int(sector.split()[-1]) if sector and 'Sector' in sector else None,
                status="candidate"
            )
            
            if save_to_db:
                self.db.add(candidate)
                self.db.commit()
                self.db.refresh(candidate)
                logger.info(f"Saved candidate to database (ID: {candidate.id})")
            
            logger.info(f"✓ Planet hunt complete for TIC {tic_id}")
            return candidate
            
        except Exception as e:
            logger.error(f"Error analyzing TIC {tic_id}: {str(e)}", exc_info=True)
            self.db.rollback()
            raise
    
    def get_candidates_by_tic(self, tic_id: str) -> List[ExoplanetCandidate]:
        """
        Retrieve all candidates for a given TIC ID.
        
        Args:
            tic_id: TESS Input Catalog ID
            
        Returns:
            List of ExoplanetCandidate objects
        """
        return (
            self.db.query(ExoplanetCandidate)
            .filter(ExoplanetCandidate.source_id == tic_id)
            .order_by(ExoplanetCandidate.power.desc())
            .all()
        )
    
    def get_all_candidates(
        self,
        status: Optional[str] = None,
        min_power: Optional[float] = None,
        limit: int = 100
    ) -> List[ExoplanetCandidate]:
        """
        Retrieve exoplanet candidates with optional filters.
        
        Args:
            status: Filter by status (candidate, confirmed, false_positive)
            min_power: Minimum BLS power threshold
            limit: Maximum number of results
            
        Returns:
            List of ExoplanetCandidate objects
        """
        query = self.db.query(ExoplanetCandidate)
        
        if status:
            query = query.filter(ExoplanetCandidate.status == status)
        
        if min_power is not None:
            query = query.filter(ExoplanetCandidate.power >= min_power)
        
        return (
            query
            .order_by(ExoplanetCandidate.power.desc())
            .limit(limit)
            .all()
        )
    
    def update_candidate_status(
        self,
        candidate_id: int,
        status: str,
        notes: Optional[str] = None
    ) -> Optional[ExoplanetCandidate]:
        """
        Update the validation status of a candidate.
        
        Args:
            candidate_id: Database ID of candidate
            status: New status (candidate, confirmed, false_positive)
            notes: Optional notes about validation
            
        Returns:
            Updated ExoplanetCandidate object
        """
        candidate = self.db.query(ExoplanetCandidate).get(candidate_id)
        
        if not candidate:
            return None
        
        candidate.status = status
        if notes:
            candidate.notes = notes
        
        self.db.commit()
        self.db.refresh(candidate)
        
        logger.info(f"Updated candidate {candidate_id} status to {status}")
        return candidate
