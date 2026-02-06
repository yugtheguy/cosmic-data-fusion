import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import Plot from 'react-plotly.js';
import { useAuth } from '../context/AuthContext';
import {
    Clock,
    FastForward,
    Map,
    Star,
    AlertCircle,
    Filter,
    RefreshCw,
    Zap,
    User,
    LogOut,
    LayoutDashboard,
    Search,
    Database,
    UploadCloud,
    Brain,
    Link2,
    Download,
    BookOpen,
    Maximize2,
    Minimize2,
    Play,
    Pause,
    Square,
    SkipBack,
    SkipForward,
    Target,
    MapPin,
    Layers,
    ChevronDown,
    ChevronRight
} from 'lucide-react';
import TimelineController from '../components/TimelineController';
import UncertaintyCone from '../components/UncertaintyCone';
import ConfidenceHeatmap from '../components/ConfidenceHeatmap';
import CelestialSphere3D from '../components/CelestialSphere3D';
import historicalFacts from '../data/historicalFacts.json';
import './TimeMachine.css';


const API_BASE_URL = 'http://localhost:8000';

function TimeMachine() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    // State
    const [currentEpoch, setCurrentEpoch] = useState(2016);
    const [isPlaying, setIsPlaying] = useState(false);
    const [stars, setStars] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('timemachine');

    // Comparison mode
    const [compareMode, setCompareMode] = useState(false);
    const [compareEpoch, setCompareEpoch] = useState(-3000); // Ancient epoch for comparison

    // Time Warp Effect
    const [isWarping, setIsWarping] = useState(false);
    const [warpMessage, setWarpMessage] = useState('');
    const [previousEpoch, setPreviousEpoch] = useState(2016);

    // Fullscreen Study Mode
    const [isFullscreen, setIsFullscreen] = useState(false);

    // Export state
    const [isExporting, setIsExporting] = useState(false);

    // Animation playback state
    const [animationFrames, setAnimationFrames] = useState([]);
    const [isAnimating, setIsAnimating] = useState(false);
    const [animationSpeed, setAnimationSpeed] = useState(1);
    const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
    const [isLoadingAnimation, setIsLoadingAnimation] = useState(false);
    const animationRef = useRef(null);
    const starPositionsRef = useRef({}); // Track current star positions for delta decoding

    // Filters
    const [filters, setFilters] = useState({
        raMin: 0,
        raMax: 180,
        decMin: -20,
        decMax: 40,
        maxMagnitude: 13,
        limit: 2000
    });

    // Stats
    const [stats, setStats] = useState({
        totalStars: 0,
        avgUncertainty: 0,
        fastMovers: 0,
        deltaYears: 0
    });

    // Fast movers list
    const [fastMoversList, setFastMoversList] = useState([]);
    const [showFastMovers, setShowFastMovers] = useState(false);
    const [selectedStarId, setSelectedStarId] = useState(null);

    // Visual options
    const [showTrails, setShowTrails] = useState(false);
    const [showVectors, setShowVectors] = useState(false);
    const [showUncertainty, setShowUncertainty] = useState(true); // NEW: Show uncertainty cones
    const [showHeatmap, setShowHeatmap] = useState(true); // NEW: Show confidence heatmap
    const [hoveredStar, setHoveredStar] = useState(null); // NEW: Track hovered star for tooltip
    const [view3D, setView3D] = useState(false); // Toggle between 2D and 3D view
    const [showFilters, setShowFilters] = useState(true); // Show/hide filter panel in 3D mode

    // Region Selection for Query Builder integration
    const [selectionMode, setSelectionMode] = useState(false); // Toggle selection mode
    const [selectedStars, setSelectedStars] = useState(null); // Selected region object {raMin, raMax, decMin, decMax, stars[]}
    const [selectionCount, setSelectionCount] = useState(0); // Count of selected stars


    // URL parameters for integration with NL Chat
    const [searchParams, setSearchParams] = useSearchParams();

    // Parse URL parameters on mount
    useEffect(() => {
        const raMin = searchParams.get('raMin');
        const raMax = searchParams.get('raMax');
        const decMin = searchParams.get('decMin');
        const decMax = searchParams.get('decMax');
        const maxMag = searchParams.get('maxMagnitude');
        const limit = searchParams.get('limit');
        const autoLoad = searchParams.get('autoLoad');

        if (raMin || raMax || decMin || decMax || maxMag || limit) {
            const newFilters = { ...filters };
            if (raMin) newFilters.raMin = parseFloat(raMin);
            if (raMax) newFilters.raMax = parseFloat(raMax);
            if (decMin) newFilters.decMin = parseFloat(decMin);
            if (decMax) newFilters.decMax = parseFloat(decMax);
            if (maxMag) newFilters.maxMagnitude = parseFloat(maxMag);
            if (limit) newFilters.limit = parseInt(limit);

            setFilters(newFilters);

            // Auto-load stars if autoLoad=true
            if (autoLoad === 'true') {
                setTimeout(() => fetchStarsAtEpoch(currentEpoch), 500);
            }
        }
    }, [searchParams]);

    // Get historical context for current epoch
    const historicalContext = useMemo(() => {
        // Find the closest event within ±1000 years
        const closest = historicalFacts.events
            .map(e => ({ ...e, diff: Math.abs(e.year - currentEpoch) }))
            .filter(e => e.diff <= 1000)
            .sort((a, b) => a.diff - b.diff)[0];
        return closest || null;
    }, [currentEpoch]);

    // Fetch fast movers from API
    const fetchFastMovers = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/temporal/fast-movers?min_pm=30&limit=10`);
            if (response.ok) {
                const data = await response.json();
                setFastMoversList(data.stars || []);
            }
        } catch (err) {
            console.error('Failed to fetch fast movers:', err);
        }
    }, []);

    // Load fast movers on mount
    useEffect(() => {
        fetchFastMovers();
    }, [fetchFastMovers]);

    // Fetch stars at current epoch
    const fetchStarsAtEpoch = useCallback(async (epoch) => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/temporal/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target_epoch: epoch,
                    ra_min: filters.raMin,
                    ra_max: filters.raMax,
                    dec_min: filters.decMin,
                    dec_max: filters.decMax,
                    max_magnitude: filters.maxMagnitude,
                    limit: filters.limit
                })
            });

            if (!response.ok) throw new Error('Failed to fetch temporal data');

            const data = await response.json();
            setStars(data.stars || []);

            // Calculate stats - exclude stars without PM data (uncertainty=999999)
            const starsWithPM = data.stars.filter(s => s.uncertainty_arcsec < 999999);
            const avgUnc = starsWithPM.length > 0
                ? starsWithPM.reduce((sum, s) => sum + s.uncertainty_arcsec, 0) / starsWithPM.length
                : 0;

            const fastMovers = data.stars.filter(s => s.total_pm && s.total_pm > 50).length;

            setStats({
                totalStars: data.stars.length,
                avgUncertainty: avgUnc,
                fastMovers: fastMovers,
                deltaYears: epoch - 2016
            });
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    }, [filters]);

    // Load initial data
    useEffect(() => {
        fetchStarsAtEpoch(currentEpoch);
    }, []);

    // Handle epoch change (debounced) with TIME WARP effect
    useEffect(() => {
        const epochDiff = Math.abs(currentEpoch - previousEpoch);

        // Trigger time warp effect for jumps > 500 years
        // BUT skip warp effect if timeline is playing (continuous animation)
        if (epochDiff > 500 && !isWarping && !isPlaying && !isAnimating) {
            const direction = currentEpoch > previousEpoch ? 'FUTURE' : 'PAST';
            const message = direction === 'FUTURE'
                ? `WARPING ${epochDiff.toLocaleString()} YEARS INTO THE FUTURE`
                : `TRAVELING ${epochDiff.toLocaleString()} YEARS INTO THE PAST`;

            setWarpMessage(message);
            setIsWarping(true);

            // End warp effect after animation
            setTimeout(() => {
                setIsWarping(false);
                setPreviousEpoch(currentEpoch);
            }, 1500);
        } else if (epochDiff <= 500) {
            setPreviousEpoch(currentEpoch);
        }

        // CRITICAL FIX: Skip API calls entirely during animation to prevent flickering
        // Only fetch data when timeline is NOT playing AND NOT animating frames
        if (!isPlaying && !isAnimating) {
            const timer = setTimeout(() => {
                fetchStarsAtEpoch(currentEpoch);
            }, 300);

            return () => clearTimeout(timer);
        }
    }, [currentEpoch, fetchStarsAtEpoch, isPlaying, isAnimating, isWarping, previousEpoch]);

    // Fetch data when animation stops to show final epoch
    useEffect(() => {
        if (!isPlaying && !isAnimating) {
            // Small delay to let the final epoch settle
            const timer = setTimeout(() => {
                fetchStarsAtEpoch(currentEpoch);
            }, 100);
            return () => clearTimeout(timer);
        }
    }, [isPlaying, isAnimating, currentEpoch, fetchStarsAtEpoch]);


    // Handle filter apply
    const handleApplyFilters = () => {
        fetchStarsAtEpoch(currentEpoch);
    };

    // Handle export
    const handleExport = async (format = 'csv') => {
        setIsExporting(true);
        try {
            const params = new URLSearchParams({
                target_epoch: currentEpoch,
                format: format,
                ra_min: filters.raMin,
                ra_max: filters.raMax,
                dec_min: filters.decMin,
                dec_max: filters.decMax,
                max_magnitude: filters.maxMagnitude,
                limit: Math.min(filters.limit, 10000) // Cap at 10K for performance
            });

            if (format === 'csv') {
                // Download CSV
                const url = `${API_BASE_URL}/temporal/export?${params}`;
                const link = document.createElement('a');
                link.href = url;
                link.download = `temporal_export_${currentEpoch}_AD.csv`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } else {
                // Fetch JSON
                const response = await fetch(`${API_BASE_URL}/temporal/export?${params}`);
                const data = await response.json();

                // Download as JSON file
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `temporal_export_${currentEpoch}_AD.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            }
        } catch (err) {
            console.error('Export failed:', err);
            setError('Failed to export data');
        } finally {
            setIsExporting(false);
        }
    };

    // Handle star selection from Plotly box select (using range, not points)
    const handleStarSelection = (eventData) => {
        if (!eventData || !eventData.range || !selectionMode) {
            return;
        }

        try {
            // Get the selection box coordinates (same approach as Dashboard.jsx)
            const raMin = Math.min(eventData.range.x[0], eventData.range.x[1]);
            const raMax = Math.max(eventData.range.x[0], eventData.range.x[1]);
            const decMin = Math.min(eventData.range.y[0], eventData.range.y[1]);
            const decMax = Math.max(eventData.range.y[0], eventData.range.y[1]);

            // Count how many stars fall within the selected region
            const starsInRegion = stars.filter(star =>
                star.ra_at_epoch >= raMin &&
                star.ra_at_epoch <= raMax &&
                star.dec_at_epoch >= decMin &&
                star.dec_at_epoch <= decMax
            );

            // Store the selection region and stars
            setSelectedStars({
                raMin,
                raMax,
                decMin,
                decMax,
                stars: starsInRegion
            });
            setSelectionCount(starsInRegion.length);

            console.log(`✅ Selected region: RA [${raMin.toFixed(2)}, ${raMax.toFixed(2)}], Dec [${decMin.toFixed(2)}, ${decMax.toFixed(2)}]`);
            console.log(`✅ ${starsInRegion.length} stars in selected region`);
        } catch (err) {
            console.error('Selection error:', err);
        }
    };

    // Navigate to Query Builder with selected region
    const handleQuerySelection = () => {
        if (!selectedStars || selectionCount === 0) {
            console.warn('No region selected');
            return;
        }

        try {
            // Prepare selection data for Query Builder (with region bounds)
            const selectionData = {
                star_ids: selectedStars.stars.map(s => s.source_id),
                epoch: currentEpoch,
                ra_range: [selectedStars.raMin, selectedStars.raMax],
                dec_range: [selectedStars.decMin, selectedStars.decMax],
                selection_count: selectionCount,
                source: "time_machine",
                timestamp: new Date().toISOString()
            };

            // Store in session storage for Query Builder to read
            sessionStorage.setItem('tm_region_selection', JSON.stringify(selectionData));

            console.log('Navigating to Query Builder with selection:', selectionData);

            // Navigate to Query Builder
            navigate('/query');
        } catch (err) {
            console.error('Navigation error:', err);
            setError('Failed to navigate to Query Builder');
        }
    };

    // Animation: Load frames from API
    const loadAnimationFrames = async (startEpoch, endEpoch, frameCount = 100) => {
        setIsLoadingAnimation(true);
        try {
            const params = new URLSearchParams({
                start_epoch: startEpoch,
                end_epoch: endEpoch,
                frame_count: frameCount,
                ra_min: filters.raMin,
                ra_max: filters.raMax,
                dec_min: filters.decMin,
                dec_max: filters.decMax,
                max_magnitude: filters.maxMagnitude,
                limit: Math.min(filters.limit, 500),
                delta_encoding: true
            });

            const response = await fetch(`${API_BASE_URL}/temporal/animation?${params}`);
            const data = await response.json();

            if (data.frames && data.frames.length > 0) {
                setAnimationFrames(data.frames);
                setCurrentFrameIndex(0);

                // Initialize star positions from first frame
                const initialPositions = {};
                data.frames[0].positions.forEach(pos => {
                    initialPositions[pos.id] = { ra: pos.ra, dec: pos.dec, mag: pos.mag };
                });
                starPositionsRef.current = initialPositions;

                return data;
            }
        } catch (err) {
            console.error('Failed to load animation frames:', err);
            setError('Failed to load animation');
        } finally {
            setIsLoadingAnimation(false);
        }
    };

    // Animation: Decode delta frame and update positions
    const decodeFrame = (frame) => {
        const positions = starPositionsRef.current;
        const decodedStars = [];

        frame.positions.forEach(pos => {
            if ('dra' in pos) {
                // Delta encoded - apply change
                if (positions[pos.id]) {
                    positions[pos.id].ra += pos.dra;
                    positions[pos.id].dec += pos.ddec;
                }
            } else {
                // Full position
                positions[pos.id] = { ra: pos.ra, dec: pos.dec, mag: pos.mag };
            }

            if (positions[pos.id]) {
                decodedStars.push({
                    id: pos.id,
                    ra_at_epoch: positions[pos.id].ra,
                    dec_at_epoch: positions[pos.id].dec,
                    brightness_mag: positions[pos.id].mag || 10
                });
            }
        });

        return decodedStars;
    };

    // Animation: Play
    const playAnimation = () => {
        if (animationFrames.length === 0) return;

        // Prevent starting multiple animations
        if (animationRef.current) {
            console.warn('Animation already running');
            return;
        }

        setIsAnimating(true);

        const frameInterval = 1000 / (30 * animationSpeed); // 30 FPS base

        animationRef.current = setInterval(() => {
            setCurrentFrameIndex(prev => {
                const nextIndex = prev + 1;
                if (nextIndex >= animationFrames.length) {
                    // Loop back to start
                    return 0;
                }
                return nextIndex;
            });
        }, frameInterval);
    };

    // Animation: Pause
    const pauseAnimation = () => {
        setIsAnimating(false);
        if (animationRef.current) {
            clearInterval(animationRef.current);
            animationRef.current = null;
        }
    };

    // Animation: Stop and reset
    const stopAnimation = () => {
        pauseAnimation();
        setCurrentFrameIndex(0);
        setAnimationFrames([]);
    };

    // Update stars when animation frame changes
    useEffect(() => {
        if (animationFrames.length > 0 && currentFrameIndex < animationFrames.length) {
            const frame = animationFrames[currentFrameIndex];
            const decodedStars = decodeFrame(frame);
            setStars(decodedStars);
            setCurrentEpoch(frame.epoch);
        }
    }, [currentFrameIndex, animationFrames]);

    // Cleanup animation on unmount
    useEffect(() => {
        return () => {
            if (animationRef.current) {
                clearInterval(animationRef.current);
            }
        };
    }, []);

    // Restart animation when speed changes (if currently playing)
    useEffect(() => {
        if (isAnimating && animationRef.current) {
            // Clear old interval
            clearInterval(animationRef.current);

            // Start new interval with updated speed
            const frameInterval = 1000 / (30 * animationSpeed);
            animationRef.current = setInterval(() => {
                setCurrentFrameIndex(prev => {
                    const nextIndex = prev + 1;
                    if (nextIndex >= animationFrames.length) {
                        return 0;
                    }
                    return nextIndex;
                });
            }, frameInterval);
        }
    }, [animationSpeed, isAnimating, animationFrames.length]);

    // Memoize plot data to prevent re-renders
    const plotData = useMemo(() => {
        // Derived fast movers list (in case it's not defined elsewhere)
        const fastMoversList = stars.filter(s => s.total_pm && s.total_pm > 50).slice(0, 50);

        // Helper for uncertainty colors
        const getUncertaintyColor = (uncertaintyClass) => {
            const colors = {
                'high_confidence': 'rgba(0, 255, 136, 0.15)',
                'acceptable': 'rgba(255, 235, 59, 0.15)',
                'approximate': 'rgba(255, 152, 0, 0.2)',
                'extreme_range': 'rgba(244, 67, 54, 0.25)',
                'unreliable': 'rgba(183, 28, 28, 0.3)'
            };
            return colors[uncertaintyClass] || 'rgba(150, 150, 150, 0.15)';
        };

        const traces = [
            // Main stars trace
            {
                type: 'scatter',
                mode: 'markers',
                name: 'Stars',
                x: stars.map(s => s.ra_at_epoch),
                y: stars.map(s => s.dec_at_epoch),
                marker: {
                    size: stars.map(s => Math.max(2, 15 - s.brightness_mag)),
                    color: stars.map(s =>
                        s.uncertainty_class === 'high_confidence' ? '#4a9f6e' :
                            s.uncertainty_class === 'acceptable' ? '#e8a87c' :
                                s.uncertainty_class === 'approximate' ? '#f59e0b' :
                                    '#ef4444'
                    ),
                    opacity: 0.8,
                    line: { width: 0 }
                },
                text: stars.map(s =>
                    `ID: ${s.id}<br>` +
                    `RA: ${s.ra_at_epoch?.toFixed(4) || 'N/A'}°<br>` +
                    `Dec: ${s.dec_at_epoch?.toFixed(4) || 'N/A'}°<br>` +
                    `Mag: ${s.brightness_mag?.toFixed(2) || 'N/A'}<br>` +
                    `PM: ${s.total_pm?.toFixed(2) || 'N/A'} mas/yr<br>` +
                    `Uncertainty: ${s.uncertainty_arcsec?.toFixed(2) || 'N/A'}″<br>` +
                    `<i>Click to view details</i>`
                ),
                hovertemplate: '%{text}<extra></extra>',
                customdata: stars.map(s => s.id)
            },
            // Highlight ring for selected star
            ...(selectedStarId ? (() => {
                // Try to find in loaded stars first
                let selectedStar = stars.find(s => s.id === selectedStarId);

                // If not found, try quick derived list
                if (!selectedStar) {
                    const fastMover = fastMoversList.find(s => s.id === selectedStarId);
                    if (fastMover) {
                        selectedStar = {
                            ra_at_epoch: fastMover.ra_deg, // Use original coords if unavailable, or maybe derived?
                            dec_at_epoch: fastMover.dec_deg
                        };
                    }
                }

                if (selectedStar) {
                    return [{
                        type: 'scatter',
                        mode: 'markers',
                        name: 'Selected',
                        x: [selectedStar.ra_at_epoch],
                        y: [selectedStar.dec_at_epoch],
                        marker: {
                            size: 35,
                            color: 'rgba(255, 215, 0, 0.3)',
                            line: {
                                color: '#ffd700',
                                width: 3
                            },
                            symbol: 'circle-open'
                        },
                        hoverinfo: 'skip',
                        showlegend: false
                    }];
                }
                return [];
            })() : []),

            // Star trails
            ...(showTrails ? (() => {
                const starsWithPM = stars.filter(s => s.pmra && s.pmdec);
                const topMovers = starsWithPM
                    .sort((a, b) => (b.total_pm || 0) - (a.total_pm || 0))
                    .slice(0, 50);

                return topMovers.map((s, idx) => ({
                    type: 'scatter',
                    mode: 'lines',
                    x: [s.ra_deg, s.ra_at_epoch],
                    y: [s.dec_deg, s.dec_at_epoch],
                    line: {
                        color: `rgba(212, 104, 58, ${0.6 - idx * 0.01})`,
                        width: 1.5
                    },
                    hoverinfo: 'skip',
                    showlegend: false
                }));
            })() : []),

            // Movement vectors
            ...(showVectors ? (() => {
                const starsWithPM = stars.filter(s => s.pmra && s.pmdec && s.total_pm > 20);
                const topMovers = starsWithPM.slice(0, 30);

                return topMovers.map(s => {
                    const scale = 0.5;
                    const arrowEndRA = s.ra_at_epoch + (s.pmra / 3600000) * 1000 * scale;
                    const arrowEndDec = s.dec_at_epoch + (s.pmdec / 3600000) * 1000 * scale;

                    return {
                        type: 'scatter',
                        mode: 'lines+markers',
                        x: [s.ra_at_epoch, arrowEndRA],
                        y: [s.dec_at_epoch, arrowEndDec],
                        line: { color: '#00bfff', width: 2 },
                        marker: {
                            size: [0, 8],
                            color: '#00bfff',
                            symbol: 'triangle-up'
                        },
                        hoverinfo: 'skip',
                        showlegend: false
                    };
                });
            })() : []),

            // Comparison overlay
            ...(compareMode ? (() => {
                const ancientStars = stars.filter(s => s.pmra && s.pmdec).map(s => {
                    const yearsBack = currentEpoch - compareEpoch;
                    const pmraPerYear = s.pmra / 3600000;
                    const pmdecPerYear = s.pmdec / 3600000;
                    const ancient_ra = s.ra_at_epoch - pmraPerYear * yearsBack;
                    const ancient_dec = s.dec_at_epoch - pmdecPerYear * yearsBack;
                    const distance = Math.sqrt(
                        Math.pow(s.ra_at_epoch - ancient_ra, 2) +
                        Math.pow(s.dec_at_epoch - ancient_dec, 2)
                    );
                    return { ...s, ancient_ra, ancient_dec, distance };
                });

                const topMovers = ancientStars
                    .filter(s => s.distance > 0.01)
                    .sort((a, b) => b.distance - a.distance)
                    .slice(0, 20);

                const colors = topMovers.map((_, i) =>
                    `hsl(${35 + i * 5}, 100%, ${70 - i * 2}%)`
                );

                return [
                    {
                        type: 'scatter',
                        mode: 'markers+text',
                        name: `${Math.abs(compareEpoch)} ${compareEpoch < 0 ? 'BC' : 'AD'}`,
                        x: topMovers.map(s => s.ancient_ra),
                        y: topMovers.map(s => s.ancient_dec),
                        text: topMovers.map((_, i) => `${i + 1}`),
                        textposition: 'top center',
                        textfont: { size: 9, color: '#fff' },
                        marker: {
                            size: topMovers.map((_, i) => 18 - i * 0.5),
                            color: colors,
                            line: { color: '#fff', width: 1.5 },
                            symbol: 'diamond'
                        },
                        hovertemplate: '<b>Ancient Position</b><br>RA: %{x:.4f}°<br>Dec: %{y:.4f}°<extra></extra>'
                    },
                    ...topMovers.map((s, i) => ({
                        type: 'scatter',
                        mode: 'lines',
                        x: [s.ancient_ra, s.ra_at_epoch],
                        y: [s.ancient_dec, s.dec_at_epoch],
                        line: {
                            color: colors[i],
                            width: Math.max(1.5, 3 - i * 0.1)
                        },
                        hoverinfo: 'skip',
                        showlegend: false
                    }))
                ];
            })() : []),

            // Uncertainty visualization
            ...(showUncertainty ? (() => {
                try {
                    const starsWithUncertainty = stars.filter(s =>
                        s.uncertainty_deg !== undefined &&
                        s.uncertainty_deg !== null &&
                        s.uncertainty_arcsec < 999999 &&
                        !isNaN(s.uncertainty_deg)
                    );
                    const limitedStars = starsWithUncertainty.slice(0, 50);

                    return limitedStars.map((star, idx) => {
                        const radius = Math.max(0.01, star.uncertainty_deg * 2);
                        const numPoints = 20;
                        const angles = Array.from({ length: numPoints + 1 }, (_, i) => (i / numPoints) * 2 * Math.PI);
                        const circleX = angles.map(a => star.ra_at_epoch + radius * Math.cos(a));
                        const circleY = angles.map(a => star.dec_at_epoch + radius * Math.sin(a));

                        return {
                            type: 'scatter',
                            mode: 'lines',
                            x: circleX,
                            y: circleY,
                            fill: 'toself',
                            fillcolor: getUncertaintyColor(star.uncertainty_class),
                            line: {
                                color: getUncertaintyColor(star.uncertainty_class).replace('0.15', '0.4'),
                                width: 1
                            },
                            hoverinfo: 'skip',
                            showlegend: false,
                            name: `Uncertainty ${idx}`
                        };
                    });
                } catch (error) {
                    console.error('Error rendering uncertainty circles:', error);
                    return [];
                }
            })() : [])
        ];

        return traces.flat();
    }, [stars, selectedStarId, showTrails, showVectors, compareMode, compareEpoch, currentEpoch, showUncertainty]);

    // Memoize layout
    // Memoize layout
    const plotLayout = useMemo(() => ({
        title: null,
        xaxis: {
            title: 'Right Ascension (°)',
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            color: '#888888',
            range: [filters.raMax, filters.raMin], // Reversed for astronomy
            autorange: false
        },
        yaxis: {
            title: 'Declination (°)',
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            color: '#888888',
            range: [filters.decMin, filters.decMax],
            autorange: false
        },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'rgba(15, 15, 15, 0.5)',
        font: { family: 'Inter, sans-serif', color: '#e5e5e5' },
        margin: { l: 60, r: 20, t: 20, b: 60 },
        hovermode: 'closest',
        dragmode: selectionMode ? 'select' : 'pan',
        // Preserve user zoom if interaction occurred (optional, but good practice specific to Plotly interactions)
        uirevision: 'true'
    }), [selectionMode, filters.raMin, filters.raMax, filters.decMin, filters.decMax]);

    return (
        <>
            {/* TIME WARP OVERLAY - Full screen immersive effect */}
            {isWarping && (
                <div className="time-warp-overlay">
                    <div className="warp-stars">
                        {[...Array(50)].map((_, i) => (
                            <div
                                key={i}
                                className="warp-streak"
                                style={{
                                    left: `${Math.random() * 100}%`,
                                    top: `${Math.random() * 100}%`,
                                    animationDelay: `${Math.random() * 0.5}s`,
                                    animationDuration: `${0.5 + Math.random() * 0.5}s`
                                }}
                            />
                        ))}
                    </div>
                    <div className="warp-content">
                        <div className="warp-message">{warpMessage}</div>
                        <div className="warp-destination">
                            <span className="destination-label">DESTINATION</span>
                            <span className="destination-year">
                                {Math.abs(currentEpoch).toLocaleString()} {currentEpoch < 0 ? 'BC' : 'AD'}
                            </span>
                        </div>
                        {historicalContext && (
                            <div className="warp-context">"{historicalContext.title}"</div>
                        )}
                    </div>
                    <div className="warp-vignette" />
                </div>
            )}

            <div className={`dashboard ${isWarping ? 'warping' : ''} ${isFullscreen ? 'fullscreen-mode' : ''} ${view3D ? 'view-3d-fullscreen' : ''}`}>
                {/* Ambient Starfield Background */}
                <div className="ambient-starfield">
                    {[...Array(30)].map((_, i) => (
                        <div
                            key={i}
                            className={`ambient-star ambient-star-${(i % 3) + 1}`}
                            style={{
                                left: `${Math.random() * 100}%`,
                                top: `${Math.random() * 100}%`,
                                animationDelay: `${Math.random() * 10}s`
                            }}
                        />
                    ))}
                </div>

                {/* Sidebar */}
                {!view3D && (
                <aside className="dashboard-sidebar">
                    {/* Logo */}
                    <div className="sidebar-logo">
                        <div className="logo-mark">C</div>
                        <span className="logo-text">COSMIC</span>
                    </div>

                    {/* Navigation */}
                    <nav className="sidebar-nav">
                        <div className="nav-section-label">Navigation</div>
                        <button
                            className="nav-item"
                            onClick={() => navigate('/dashboard?tab=overview')}
                        >
                            <LayoutDashboard size={18} strokeWidth={1.5} />
                            <span>Overview</span>
                        </button>
                        <button
                            className="nav-item"
                            onClick={() => navigate('/dashboard?tab=coordinate-resolver')}
                        >
                            <Target size={18} strokeWidth={1.5} />
                            <span>Coordinate Finder</span>
                        </button>
                        <button
                            className="nav-item active"
                        >
                            <Clock size={18} strokeWidth={1.5} />
                            <span>Time Machine</span>
                        </button>
                        <button
                            className="nav-item"
                            onClick={() => navigate('/query')}
                        >
                            <Search size={18} strokeWidth={1.5} />
                            <span>Query Builder</span>
                        </button>
                        <button
                            className="nav-item"
                            onClick={() => navigate('/dashboard?tab=results')}
                        >
                            <Database size={18} strokeWidth={1.5} />
                            <span>Data Table</span>
                        </button>
                        <button
                            className="nav-item"
                            onClick={() => navigate('/dashboard?tab=upload')}
                        >
                            <UploadCloud size={18} strokeWidth={1.5} />
                            <span>Ingest Data</span>
                        </button>
                        <button
                            className="nav-item"
                            onClick={() => navigate('/dashboard?tab=skymap')}
                        >
                            <Map size={18} strokeWidth={1.5} />
                            <span>Sky Map</span>
                        </button>
                        <button
                            className="nav-item"
                            onClick={() => navigate('/dashboard?tab=anomaly')}
                        >
                            <Brain size={18} strokeWidth={1.5} />
                            <span>AI Lab</span>
                        </button>
                        <button
                            className="nav-item"
                            onClick={() => navigate('/dashboard?tab=harmonize')}
                        >
                            <Link2 size={18} strokeWidth={1.5} />
                            <span>Harmonizer</span>
                        </button>
                        <button
                            className="nav-item"
                            onClick={() => navigate('/dashboard?tab=export')}
                        >
                            <Download size={18} strokeWidth={1.5} />
                            <span>Export</span>
                        </button>
                        <button
                            className="nav-item"
                            onClick={() => navigate('/planet-hunter')}
                        >
                            <Target size={18} strokeWidth={1.5} />
                            <span>Planet Hunter</span>
                        </button>
                    </nav>

                    {/* Filters */}
                    <div className="sidebar-filters">
                        <div className="nav-section-label">
                            <Filter size={14} strokeWidth={1.5} />
                            Region Filters
                        </div>
                        <div className="filter-controls">
                            <div className="filter-group">
                                <label>RA Min (°)</label>
                                <div className="range-display">
                                    <span>{filters.raMin}</span>
                                </div>
                                <input
                                    type="range"
                                    min="0"
                                    max="360"
                                    value={filters.raMin}
                                    onChange={(e) => setFilters({ ...filters, raMin: Number(e.target.value) })}
                                    className="range-slider"
                                />
                            </div>
                            <div className="filter-group">
                                <label>RA Max (°)</label>
                                <div className="range-display">
                                    <span>{filters.raMax}</span>
                                </div>
                                <input
                                    type="range"
                                    min="0"
                                    max="360"
                                    value={filters.raMax}
                                    onChange={(e) => setFilters({ ...filters, raMax: Number(e.target.value) })}
                                    className="range-slider"
                                />
                            </div>
                            <div className="filter-group">
                                <label>Dec Min (°)</label>
                                <div className="range-display">
                                    <span>{filters.decMin}</span>
                                </div>
                                <input
                                    type="range"
                                    min="-90"
                                    max="90"
                                    value={filters.decMin}
                                    onChange={(e) => setFilters({ ...filters, decMin: Number(e.target.value) })}
                                    className="range-slider"
                                />
                            </div>
                            <div className="filter-group">
                                <label>Dec Max (°)</label>
                                <div className="range-display">
                                    <span>{filters.decMax}</span>
                                </div>
                                <input
                                    type="range"
                                    min="-90"
                                    max="90"
                                    value={filters.decMax}
                                    onChange={(e) => setFilters({ ...filters, decMax: Number(e.target.value) })}
                                    className="range-slider"
                                />
                            </div>
                            <div className="filter-group">
                                <label>Mag Max</label>
                                <div className="range-display">
                                    <span>{filters.maxMagnitude}</span>
                                </div>
                                <input
                                    type="range"
                                    min="0"
                                    max="20"
                                    step="0.5"
                                    value={filters.maxMagnitude}
                                    onChange={(e) => setFilters({ ...filters, maxMagnitude: parseFloat(e.target.value) })}
                                    className="range-slider"
                                />
                            </div>
                            <button
                                className="apply-filters-btn"
                                onClick={handleApplyFilters}
                                disabled={isLoading}
                            >
                                <RefreshCw size={14} />
                                Apply Filters
                            </button>
                        </div>
                    </div>

                    {/* Fast Movers Panel */}
                    <div className="sidebar-fast-movers">
                        <button
                            className="nav-section-label clickable"
                            onClick={() => setShowFastMovers(!showFastMovers)}
                        >
                            <Zap size={14} strokeWidth={1.5} />
                            Fast Movers ({fastMoversList.length})
                            <span className="toggle-arrow">{showFastMovers ? <ChevronDown size={14} /> : <ChevronRight size={14} />}</span>
                        </button>
                        {showFastMovers && (
                            <div className="fast-movers-list">
                                {fastMoversList.slice(0, 8).map((star, idx) => (
                                    <div
                                        key={star.id}
                                        className={`fast-mover-item ${selectedStarId === star.id ? 'selected' : ''}`}
                                        onClick={() => {
                                            // Select this star (store full object for highlight)
                                            setSelectedStarId(star.id);
                                            // Store the star data for immediate highlight
                                            window.__selectedFastMover = star;
                                            // Update filters to center on star
                                            const newFilters = {
                                                ...filters,
                                                raMin: Math.max(0, star.ra_deg - 3),
                                                raMax: Math.min(360, star.ra_deg + 3),
                                                decMin: Math.max(-90, star.dec_deg - 3),
                                                decMax: Math.min(90, star.dec_deg + 3)
                                            };
                                            setFilters(newFilters);
                                            // Trigger immediate fetch with new filters
                                            setTimeout(() => handleApplyFilters(), 50);
                                        }}
                                        title={`Click to focus on this star`}
                                    >
                                        <span className="fm-rank">#{idx + 1}</span>
                                        <div className="fm-info">
                                            <span className="fm-id">{star.source_id.slice(-8)}</span>
                                            <span className="fm-pm">{star.total_pm?.toFixed(1)} mas/yr</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* User Section */}
                    <div className="sidebar-user">
                        <div className="user-avatar">
                            <User size={16} strokeWidth={1.5} />
                        </div>
                        <div className="user-info">
                            <span className="user-name">{user?.full_name || user?.email || 'Researcher'}</span>
                            <span className="user-role">Astronomer</span>
                        </div>
                        <button
                            className="logout-btn"
                            title="Logout"
                            onClick={() => {
                                logout();
                                navigate('/login');
                            }}
                        >
                            <LogOut size={16} strokeWidth={1.5} />
                        </button>
                    </div>
                </aside>
                )}

                {/* Main Content */}
                <main className={`dashboard-main ${view3D ? 'fullscreen-3d' : ''}`}>
                    {/* Header */}
                    {!view3D && (
                    <header className="dashboard-header">
                        <h1 className="page-title">
                            <Clock size={24} />
                            Time Machine
                        </h1>
                        <div className="header-actions">
                            <div className="epoch-badge">
                                {currentEpoch >= 1 ? `${Math.floor(currentEpoch)} AD` : `${Math.abs(Math.floor(currentEpoch))} BC`}
                            </div>
                        </div>
                    </header>
                    )}

                    {/* Stats Row */}
                    {!view3D && (
                    <div className="stats-row">
                        <div className="stat-card">
                            <div className="stat-icon">
                                <Star />
                            </div>
                            <div className="stat-content">
                                <div className="stat-label">Stars Tracked</div>
                                <div className="stat-value">{stats.totalStars.toLocaleString()}</div>
                            </div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-icon">
                                <Clock />
                            </div>
                            <div className="stat-content">
                                <div className="stat-label">Time Delta</div>
                                <div className="stat-value">
                                    {stats.deltaYears > 0 ? '+' : ''}{stats.deltaYears.toLocaleString()} yr
                                </div>
                            </div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-icon">
                                <Zap />
                            </div>
                            <div className="stat-content">
                                <div className="stat-label">Fast Movers</div>
                                <div className="stat-value">{stats.fastMovers}</div>
                            </div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-icon">
                                <AlertCircle />
                            </div>
                            <div className="stat-content">
                                <div className="stat-label">Avg Uncertainty</div>
                                <div className="stat-value">{stats.avgUncertainty.toFixed(2)}″</div>
                            </div>
                        </div>
                    </div>
                    )}

                    {/* Historical Context Card */}
                    {historicalContext && !view3D && (
                        <div className="historical-context-card" key={historicalContext.year}>
                            <div className="context-icon">
                                <BookOpen size={24} />
                            </div>
                            <div className="context-content">
                                <div className="context-title">{historicalContext.title}</div>
                                <div className="context-fact">{historicalContext.fact}</div>
                                <div className="context-year">
                                    {Math.abs(historicalContext.year)} {historicalContext.year < 0 ? 'BC' : 'AD'}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Sky Map */}

                    <div className={`skymap-container ${view3D ? 'immersive-3d' : ''}`}>
                        <div className={`skymap-header ${view3D ? 'minimal' : ''}`}>
                            {!view3D && (
                                <h2>
                                    <Map size={18} />
                                    Temporal Star Map
                                </h2>
                            )}
                            <div className="skymap-info">
                                <div className="skymap-toggles">
                                    <button
                                        className={`toggle-btn ${view3D ? 'active' : ''}`}
                                        onClick={() => setView3D(!view3D)}
                                        title="Toggle 3D celestial sphere view"
                                        style={{
                                            background: view3D ? 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)' : '',
                                            fontWeight: view3D ? '600' : '500',
                                            position: view3D ? 'absolute' : 'relative',
                                            top: view3D ? '1rem' : 'auto',
                                            right: view3D ? '1rem' : 'auto',
                                            zIndex: view3D ? '100' : 'auto'
                                        }}
                                    >
                                        <Layers size={14} /> {view3D ? 'Exit 3D' : '2D'}
                                    </button>
                                    {!view3D && (
                                        <>
                                            <button
                                                className={`toggle-btn ${showTrails ? 'active' : ''}`}
                                                onClick={() => setShowTrails(!showTrails)}
                                                title="Show star trails over time"
                                            >
                                                Trails
                                            </button>
                                            <button
                                                className={`toggle-btn ${showVectors ? 'active' : ''}`}
                                                onClick={() => setShowVectors(!showVectors)}
                                                title="Show movement vectors"
                                            >
                                                Vectors
                                            </button>
                                            <button
                                                className={`toggle-btn ${showUncertainty ? 'active' : ''}`}
                                                onClick={() => setShowUncertainty(!showUncertainty)}
                                                title="Show uncertainty cones (prediction confidence)"
                                            >
                                                <Target size={14} /> Uncertainty
                                            </button>
                                            <button
                                                className={`toggle-btn ${showHeatmap ? 'active' : ''}`}
                                                onClick={() => setShowHeatmap(!showHeatmap)}
                                                title="Show confidence heatmap background"
                                            >
                                                <Layers size={14} /> Heatmap
                                            </button>
                                            <button
                                                className={`toggle-btn ${selectionMode ? 'active' : ''}`}
                                                onClick={() => {
                                                    setSelectionMode(!selectionMode);
                                                    if (selectionMode) {
                                                        setSelectedStars(null);
                                                        setSelectionCount(0);
                                                    }
                                                }}
                                                title="Select stars to query in Query Builder"
                                            >
                                                <MapPin size={14} /> Select Region
                                            </button>
                                            <button
                                                className={`toggle-btn compare ${compareMode ? 'active' : ''}`}
                                                onClick={() => setCompareMode(!compareMode)}
                                                title="Compare with ancient epoch (3000 BC)"
                                            >
                                                Compare
                                            </button>
                                            <button
                                                className={`toggle-btn fullscreen ${isFullscreen ? 'active' : ''}`}
                                                onClick={() => setIsFullscreen(!isFullscreen)}
                                                title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen study mode'}
                                            >
                                                {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                                            </button>
                                            <button
                                                className={`toggle-btn export ${isExporting ? 'loading' : ''}`}
                                                onClick={() => handleExport('csv')}
                                                disabled={isExporting || stars.length === 0}
                                                title="Export current view as CSV"
                                            >
                                                {isExporting ? <RefreshCw size={14} className="spin" /> : <Download size={14} />}
                                            </button>
                                        </>
                                    )}
                                </div>


                                {!view3D && isLoading && <span className="loading-indicator">Calculating positions...</span>}
                                {!view3D && !isLoading && <span className="star-count">{stats.totalStars} stars visible</span>}
                            </div>
                        </div>

                        <div className="skymap-plot">
                            {isLoading ? (
                                <div className="skymap-loading">
                                    <RefreshCw className="spin" size={32} />
                                    <span>Computing stellar positions...</span>
                                </div>
                            ) : error ? (
                                <div className="skymap-loading">
                                    <AlertCircle size={32} style={{ color: 'var(--accent-primary)' }} />
                                    <span>Error: {error}</span>
                                </div>
                            ) : view3D ? (
                                <>
                                    {/* 3D Celestial Sphere View */}
                                    <CelestialSphere3D
                                        stars={stars}
                                        currentEpoch={currentEpoch}
                                        showUncertainty={showUncertainty}
                                        showGrid={true}
                                        selectedStarId={selectedStarId}
                                        onStarClick={(star) => {
                                            setSelectedStarId(star.id);
                                            // Navigate to star detail page
                                            navigate(`/star/${star.id}`);
                                        }}
                                        showTrails={showTrails}
                                        showVectors={showVectors}
                                        isWarping={isWarping}
                                        className="celestial-sphere-3d"
                                    />
                                    
                                    {/* Stellarium-Style Interface */}
                                    
                                    {/* Top Control Bar - Stellarium Style */}
                                    <div style={{
                                        position: 'absolute',
                                        top: '0',
                                        left: '0',
                                        right: '0',
                                        height: '60px',
                                        background: 'linear-gradient(180deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.4) 100%)',
                                        backdropFilter: 'blur(10px)',
                                        borderBottom: '1px solid rgba(212, 104, 58, 0.2)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        padding: '0 1rem',
                                        zIndex: 200
                                    }}>
                                        {/* Left Side - View Controls */}
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                            <span style={{ 
                                                color: '#e8a87c', 
                                                fontSize: '0.9rem', 
                                                fontWeight: '600',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '0.5rem'
                                            }}>
                                                <span>🌟</span>
                                                {stats.totalStars} stars visible
                                            </span>
                                            
                                            <div style={{ width: '1px', height: '30px', background: 'rgba(212, 104, 58, 0.3)' }} />
                                            
                                            {/* Magnitude Filter */}
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <span style={{ color: '#a89888', fontSize: '0.8rem' }}>Mag limit:</span>
                                                <input
                                                    type="range"
                                                    min="6"
                                                    max="15"
                                                    step="0.5"
                                                    defaultValue="12"
                                                    style={{
                                                        width: '80px',
                                                        height: '3px',
                                                        background: 'rgba(212, 104, 58, 0.3)',
                                                        borderRadius: '2px',
                                                        outline: 'none',
                                                        cursor: 'pointer',
                                                        WebkitAppearance: 'none'
                                                    }}
                                                />
                                                <span style={{ color: '#d4683a', fontSize: '0.75rem', minWidth: '25px' }}>12.0</span>
                                            </div>
                                        </div>
                                        
                                        {/* Center - Main Time Display */}
                                        <div style={{ flex: 1, textAlign: 'center' }}>
                                            <div style={{ 
                                                color: '#f8f5f0', 
                                                fontSize: '1.1rem', 
                                                fontWeight: '700',
                                                fontFamily: 'Space Grotesk'
                                            }}>
                                                {currentEpoch < 0 
                                                    ? `${Math.abs(currentEpoch).toLocaleString()} BC` 
                                                    : `${currentEpoch.toLocaleString()} AD`
                                                }
                                            </div>
                                        </div>
                                        
                                        {/* Right Side - Display Options */}
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                            <button
                                                onClick={() => setShowTrails(!showTrails)}
                                                style={{
                                                    background: showTrails ? 'rgba(212, 104, 58, 0.8)' : 'rgba(212, 104, 58, 0.2)',
                                                    border: '1px solid rgba(212, 104, 58, 0.4)',
                                                    borderRadius: '6px',
                                                    padding: '0.4rem 0.6rem',
                                                    color: showTrails ? 'white' : '#d4683a',
                                                    fontSize: '0.75rem',
                                                    fontWeight: '600',
                                                    cursor: 'pointer',
                                                    transition: 'all 0.2s ease',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '0.3rem'
                                                }}
                                                title="Toggle Motion Trails"
                                            >
                                                <Layers size={14} />
                                                Trails
                                            </button>
                                            
                                            <button
                                                onClick={() => setShowVectors(!showVectors)}
                                                style={{
                                                    background: showVectors ? 'rgba(212, 104, 58, 0.8)' : 'rgba(212, 104, 58, 0.2)',
                                                    border: '1px solid rgba(212, 104, 58, 0.4)',
                                                    borderRadius: '6px',
                                                    padding: '0.4rem 0.6rem',
                                                    color: showVectors ? 'white' : '#d4683a',
                                                    fontSize: '0.75rem',
                                                    fontWeight: '600',
                                                    cursor: 'pointer',
                                                    transition: 'all 0.2s ease',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '0.3rem'
                                                }}
                                                title="Show Proper Motion Vectors"
                                            >
                                                <span>→</span>
                                                Motion
                                            </button>
                                        </div>
                                    </div>

                                    {/* Bottom Control Bar - Timeline */}
                                    <div style={{
                                        position: 'absolute',
                                        bottom: '0',
                                        left: '0',
                                        right: '0',
                                        height: '80px',
                                        background: 'linear-gradient(0deg, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.4) 100%)',
                                        backdropFilter: 'blur(10px)',
                                        borderTop: '1px solid rgba(212, 104, 58, 0.2)',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        justifyContent: 'center',
                                        padding: '0 2rem',
                                        zIndex: 200
                                    }}>
                                        {/* Timeline Controls */}
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                                            {/* Play Controls */}
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <button
                                                    onClick={() => setCurrentEpoch(currentEpoch - 1000)}
                                                    style={{
                                                        background: 'rgba(212, 104, 58, 0.2)',
                                                        border: '1px solid rgba(212, 104, 58, 0.4)',
                                                        borderRadius: '6px',
                                                        width: '36px',
                                                        height: '36px',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        cursor: 'pointer',
                                                        transition: 'all 0.2s ease'
                                                    }}
                                                    title="Back 1000 years"
                                                >
                                                    <span style={{ color: '#d4683a', fontSize: '1.2rem' }}>⏮</span>
                                                </button>
                                                
                                                <button
                                                    onClick={() => setIsPlaying(!isPlaying)}
                                                    style={{
                                                        background: 'linear-gradient(135deg, #d4683a 0%, #e8a87c 100%)',
                                                        border: 'none',
                                                        borderRadius: '8px',
                                                        width: '44px',
                                                        height: '44px',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        cursor: 'pointer',
                                                        transition: 'all 0.2s ease',
                                                        boxShadow: '0 4px 12px rgba(212, 104, 58, 0.4)'
                                                    }}
                                                >
                                                    {isPlaying ? <Pause size={20} color="white" fill="white" /> : <Play size={20} color="white" fill="white" />}
                                                </button>
                                                
                                                <button
                                                    onClick={() => setCurrentEpoch(currentEpoch + 1000)}
                                                    style={{
                                                        background: 'rgba(212, 104, 58, 0.2)',
                                                        border: '1px solid rgba(212, 104, 58, 0.4)',
                                                        borderRadius: '6px',
                                                        width: '36px',
                                                        height: '36px',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        cursor: 'pointer',
                                                        transition: 'all 0.2s ease'
                                                    }}
                                                    title="Forward 1000 years"
                                                >
                                                    <span style={{ color: '#d4683a', fontSize: '1.2rem' }}>⏭</span>
                                                </button>
                                            </div>
                                            
                                            {/* Timeline Slider */}
                                            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                                <input
                                                    type="range"
                                                    min="-10000"
                                                    max="10000"
                                                    step="10"
                                                    value={currentEpoch}
                                                    onChange={(e) => setCurrentEpoch(parseInt(e.target.value))}
                                                    style={{
                                                        width: '100%',
                                                        height: '6px',
                                                        background: 'linear-gradient(90deg, #d4683a 0%, #e8a87c 50%, #d4683a 100%)',
                                                        borderRadius: '3px',
                                                        outline: 'none',
                                                        cursor: 'pointer',
                                                        WebkitAppearance: 'none'
                                                    }}
                                                />
                                                <div style={{ 
                                                    display: 'flex', 
                                                    justifyContent: 'space-between', 
                                                    fontSize: '0.7rem', 
                                                    color: '#a89888',
                                                    marginTop: '0.25rem'
                                                }}>
                                                    <span>10,000 BC</span>
                                                    <span>Present</span>
                                                    <span>10,000 AD</span>
                                                </div>
                                            </div>
                                            
                                            {/* Quick Jump */}
                                            <button
                                                onClick={() => setCurrentEpoch(2016)}
                                                style={{
                                                    background: 'rgba(232, 168, 124, 0.3)',
                                                    border: '1px solid rgba(232, 168, 124, 0.4)',
                                                    borderRadius: '6px',
                                                    padding: '0.5rem 1rem',
                                                    color: '#e8a87c',
                                                    fontSize: '0.75rem',
                                                    fontWeight: '600',
                                                    cursor: 'pointer',
                                                    transition: 'all 0.2s ease'
                                                }}
                                                title="Jump to present day (2016)"
                                            >
                                                Today
                                            </button>
                                        </div>
                                    </div>

                                    {/* Compact Filter Panel for 3D View */}
                                    <div style={{
                                        position: 'absolute',
                                        bottom: '1rem',
                                        left: '1rem',
                                        zIndex: 100,
                                        transition: 'all 0.3s ease'
                                    }}>
                                        {/* Toggle Button */}
                                        <button
                                            onClick={() => setShowFilters(!showFilters)}
                                            style={{
                                                background: 'rgba(10, 10, 15, 0.9)',
                                                backdropFilter: 'blur(12px)',
                                                border: '1px solid rgba(212, 104, 58, 0.4)',
                                                borderRadius: '8px',
                                                padding: '0.5rem 0.75rem',
                                                color: '#d4683a',
                                                fontWeight: '600',
                                                fontSize: '0.75rem',
                                                cursor: 'pointer',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '0.375rem',
                                                transition: 'all 0.2s ease',
                                                boxShadow: showFilters ? '0 0 15px rgba(212, 104, 58, 0.4)' : 'none',
                                                marginBottom: showFilters ? '0.5rem' : '0'
                                            }}
                                            onMouseEnter={(e) => {
                                                e.currentTarget.style.borderColor = '#d4683a';
                                                e.currentTarget.style.boxShadow = '0 0 20px rgba(212, 104, 58, 0.6)';
                                            }}
                                            onMouseLeave={(e) => {
                                                e.currentTarget.style.borderColor = 'rgba(212, 104, 58, 0.4)';
                                                e.currentTarget.style.boxShadow = showFilters ? '0 0 15px rgba(212, 104, 58, 0.4)' : 'none';
                                            }}
                                        >
                                            <Filter size={12} />
                                            {showFilters ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                                        </button>

                                        {/* Compact Filter Panel */}
                                        <div style={{
                                            background: 'rgba(10, 10, 15, 0.95)',
                                            backdropFilter: 'blur(16px)',
                                            border: '1px solid rgba(212, 104, 58, 0.3)',
                                            borderRadius: '10px',
                                            padding: showFilters ? '0.75rem' : '0',
                                            width: showFilters ? '200px' : '0',
                                            maxHeight: showFilters ? '400px' : '0',
                                            overflow: showFilters ? 'auto' : 'hidden',
                                            opacity: showFilters ? 1 : 0,
                                            transition: 'all 0.3s ease',
                                            boxShadow: showFilters ? '0 4px 16px rgba(0, 0, 0, 0.7), 0 0 20px rgba(212, 104, 58, 0.2)' : 'none'
                                        }}>
                                            {/* Compact Controls */}
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
                                                {/* Magnitude Slider */}
                                                <div>
                                                    <label style={{
                                                        fontSize: '0.625rem',
                                                        color: '#e8a87c',
                                                        marginBottom: '0.25rem',
                                                        display: 'block',
                                                        fontWeight: '600'
                                                    }}>Mag: {filters.maxMagnitude}</label>
                                                    <input
                                                        type="range"
                                                        min="6"
                                                        max="20"
                                                        step="0.5"
                                                        value={filters.maxMagnitude}
                                                        onChange={(e) => setFilters({ ...filters, maxMagnitude: parseFloat(e.target.value) })}
                                                        style={{
                                                            width: '100%',
                                                            height: '3px',
                                                            background: 'linear-gradient(90deg, #d4683a 0%, #e8a87c 100%)',
                                                            borderRadius: '2px',
                                                            outline: 'none',
                                                            cursor: 'pointer'
                                                        }}
                                                    />
                                                </div>

                                                {/* Star Limit Slider */}
                                                <div>
                                                    <label style={{
                                                        fontSize: '0.625rem',
                                                        color: '#e8a87c',
                                                        marginBottom: '0.25rem',
                                                        display: 'block',
                                                        fontWeight: '600'
                                                    }}>Stars: {filters.limit}</label>
                                                    <input
                                                        type="range"
                                                        min="500"
                                                        max="5000"
                                                        step="500"
                                                        value={filters.limit}
                                                        onChange={(e) => setFilters({ ...filters, limit: parseInt(e.target.value) })}
                                                        style={{
                                                            width: '100%',
                                                            height: '3px',
                                                            background: 'linear-gradient(90deg, #d4683a 0%, #e8a87c 100%)',
                                                            borderRadius: '2px',
                                                            outline: 'none',
                                                            cursor: 'pointer'
                                                        }}
                                                    />
                                                </div>

                                                {/* Quick Presets */}
                                                <div style={{ paddingTop: '0.25rem', borderTop: '1px solid rgba(212, 104, 58, 0.2)' }}>
                                                    <button
                                                        onClick={() => {
                                                            setFilters({
                                                                raMin: 0,
                                                                raMax: 180,
                                                                decMin: -90,
                                                                decMax: 90,
                                                                maxMagnitude: 10,
                                                                limit: 3000
                                                            });
                                                            setTimeout(() => fetchStarsAtEpoch(currentEpoch), 100);
                                                        }}
                                                        disabled={isLoading}
                                                        style={{
                                                            width: '100%',
                                                            padding: '0.375rem',
                                                            background: isLoading ? 'rgba(212, 104, 58, 0.2)' : 'linear-gradient(135deg, #d4683a 0%, #e8a87c 100%)',
                                                            border: 'none',
                                                            borderRadius: '6px',
                                                            color: 'white',
                                                            fontSize: '0.625rem',
                                                            fontWeight: '700',
                                                            cursor: isLoading ? 'not-allowed' : 'pointer',
                                                            marginBottom: '0.375rem',
                                                            transition: 'all 0.2s ease'
                                                        }}
                                                        onMouseEnter={(e) => !isLoading && (e.currentTarget.style.opacity = '0.9')}
                                                        onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
                                                    >
                                                        {isLoading ? '...' : '180° Hemisphere'}
                                                    </button>
                                                    <button
                                                        onClick={() => {
                                                            setFilters({
                                                                raMin: 0,
                                                                raMax: 180,
                                                                decMin: -90,
                                                                decMax: 90,
                                                                maxMagnitude: 9,
                                                                limit: 5000
                                                            });
                                                            setTimeout(() => fetchStarsAtEpoch(currentEpoch), 100);
                                                        }}
                                                        disabled={isLoading}
                                                        style={{
                                                            width: '100%',
                                                            padding: '0.375rem',
                                                            background: isLoading ? 'rgba(232, 168, 124, 0.2)' : 'rgba(232, 168, 124, 0.15)',
                                                            border: '1px solid rgba(232, 168, 124, 0.4)',
                                                            borderRadius: '6px',
                                                            color: '#e8a87c',
                                                            fontSize: '0.625rem',
                                                            fontWeight: '700',
                                                            cursor: isLoading ? 'not-allowed' : 'pointer',
                                                            transition: 'all 0.2s ease'
                                                        }}
                                                        onMouseEnter={(e) => {
                                                            if (!isLoading) {
                                                                e.currentTarget.style.background = 'rgba(232, 168, 124, 0.25)';
                                                                e.currentTarget.style.borderColor = '#e8a87c';
                                                            }
                                                        }}
                                                        onMouseLeave={(e) => {
                                                            e.currentTarget.style.background = isLoading ? 'rgba(232, 168, 124, 0.2)' : 'rgba(232, 168, 124, 0.15)';
                                                            e.currentTarget.style.borderColor = 'rgba(232, 168, 124, 0.4)';
                                                        }}
                                                    >
                                                        Full Sky (180°×180°)
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div style={{ position: 'relative' }}>
                                    {/* Confidence Heatmap Background */}
                                    {/* CRITICAL FIX: Hide heatmap during animation to prevent canvas re-draw flickering */}
                                    {showHeatmap && !isPlaying && (
                                        <div style={{
                                            position: 'absolute',
                                            top: 0,
                                            left: 0,
                                            width: '100%',
                                            height: '100%',
                                            pointerEvents: 'none',
                                            zIndex: 0
                                        }}>
                                            <ConfidenceHeatmap
                                                currentEpoch={currentEpoch}
                                                width={800}
                                                height={400}
                                                opacity={0.25}
                                            />
                                        </div>
                                    )}

                                    {/* Star Map Plot */}
                                    <Plot
                                        data={plotData}
                                        layout={plotLayout}
                                        config={{
                                            displayModeBar: true,
                                            displaylogo: false,
                                            responsive: true
                                        }}
                                        onSelected={handleStarSelection}
                                        onClick={(data) => {
                                            // Handle single star click to navigate to detail page
                                            if (data.points && data.points.length === 1) {
                                                const point = data.points[0];
                                                const starId = point.customdata;
                                                if (starId) {
                                                    navigate(`/star/${starId}`);
                                                }
                                            }
                                        }}
                                        style={{ width: '100%', height: '100%' }}
                                    />
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Selection Feedback & Query Button */}
                    {selectionMode && selectionCount > 0 && (
                        <div style={{
                            margin: '1rem 1.5rem 0',
                            padding: '1rem',
                            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
                            border: '1px solid rgba(99, 102, 241, 0.3)',
                            borderRadius: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            gap: '1rem'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <div style={{
                                    background: 'rgba(99, 102, 241, 0.2)',
                                    padding: '0.5rem 0.75rem',
                                    borderRadius: '6px',
                                    fontFamily: 'Orbitron, monospace',
                                    fontSize: '1.25rem',
                                    fontWeight: 700,
                                    color: 'var(--accent-primary)'
                                }}>
                                    {selectionCount}
                                </div>
                                <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                                    {selectionCount === 1 ? 'star selected' : 'stars selected'}
                                </span>
                            </div>

                            <div style={{ display: 'flex', gap: '0.75rem' }}>
                                <button
                                    className="toggle-btn"
                                    onClick={() => {
                                        setSelectedStars(null);
                                        setSelectionCount(0);
                                    }}
                                    style={{ padding: '0.5rem 1rem' }}
                                >
                                    Clear Selection
                                </button>
                                <button
                                    className="toggle-btn active"
                                    onClick={handleQuerySelection}
                                    style={{
                                        padding: '0.5rem 1.5rem',
                                        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                                        fontWeight: 600
                                    }}
                                >
                                    Query {selectionCount} {selectionCount === 1 ? 'Star' : 'Stars'} →
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Uncertainty Legend */}
                    {showUncertainty && stars.length > 0 && (
                        <div className="uncertainty-legend" style={{
                            margin: '1rem 1.5rem',
                            padding: '1rem',
                            background: 'var(--bg-surface)',
                            backdropFilter: 'blur(12px)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '8px',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            flexWrap: 'wrap',
                            gap: '1rem'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <span style={{
                                    fontSize: '0.875rem',
                                    fontWeight: 600,
                                    color: 'var(--text-primary)',
                                    fontFamily: 'Space Grotesk, monospace',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem'
                                }}>
                                    <Target size={16} /> Uncertainty Classes:
                                </span>
                            </div>

                            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                                {[
                                    { name: 'High Confidence', color: '#00ff88', range: '<0.1°' },
                                    { name: 'Acceptable', color: '#ffeb3b', range: '<0.5°' },
                                    { name: 'Approximate', color: '#ff9800', range: '<2°' },
                                    { name: 'Extreme Range', color: '#f44336', range: '<10°' },
                                    { name: 'Unreliable', color: '#b71c1c', range: '>10°' }
                                ].map(item => (
                                    <div key={item.name} style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.5rem'
                                    }}>
                                        <div style={{
                                            width: '12px',
                                            height: '12px',
                                            borderRadius: '50%',
                                            background: item.color,
                                            boxShadow: `0 0 8px ${item.color}40`
                                        }} />
                                        <span style={{
                                            fontSize: '0.75rem',
                                            color: 'var(--text-secondary)',
                                            fontFamily: 'JetBrains Mono, monospace'
                                        }}>
                                            {item.name} <span style={{ color: 'var(--text-muted)' }}>({item.range})</span>
                                        </span>
                                    </div>
                                ))}
                            </div>

                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '1rem',
                                paddingLeft: '1rem',
                                borderLeft: '1px solid var(--border-color)'
                            }}>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{
                                        fontSize: '0.75rem',
                                        color: 'var(--text-muted)',
                                        marginBottom: '0.25rem'
                                    }}>
                                        Avg Uncertainty
                                    </div>
                                    <div style={{
                                        fontSize: '1rem',
                                        fontWeight: 600,
                                        color: 'var(--accent-primary)',
                                        fontFamily: 'Orbitron, monospace'
                                    }}>
                                        {stats.avgUncertainty.toFixed(2)}″
                                    </div>
                                </div>

                                <div style={{ textAlign: 'center' }}>
                                    <div style={{
                                        fontSize: '0.75rem',
                                        color: 'var(--text-muted)',
                                        marginBottom: '0.25rem'
                                    }}>
                                        Time Delta
                                    </div>
                                    <div style={{
                                        fontSize: '1rem',
                                        fontWeight: 600,
                                        color: stats.deltaYears === 0 ? '#4a9f6e' :
                                            Math.abs(stats.deltaYears) < 10000 ? '#e8a87c' :
                                                Math.abs(stats.deltaYears) < 20000 ? '#f59e0b' : '#ef4444',
                                        fontFamily: 'Orbitron, monospace'
                                    }}>
                                        {stats.deltaYears > 0 ? '+' : ''}{stats.deltaYears.toLocaleString()} yr
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Timeline Controller Footer */}
                    {!view3D && (
                    <div className="timeline-footer">
                        {/* Animation Control Panel */}
                        <div className="animation-controls">
                            <div className="animation-controls-row">
                                {/* Load Animation Button */}
                                <button
                                    className={`anim-btn load ${isLoadingAnimation ? 'loading' : ''}`}
                                    onClick={() => loadAnimationFrames(-3000, 2000, 100)}
                                    disabled={isLoadingAnimation || isAnimating}
                                    title="Load 100 frames from 3000 BC to 2000 AD"
                                >
                                    {isLoadingAnimation ? <RefreshCw size={14} className="spin" /> : <FastForward size={14} />}
                                    <span>{isLoadingAnimation ? 'Loading...' : 'Load Animation'}</span>
                                </button>

                                {/* Playback Controls */}
                                <div className="playback-controls">
                                    <button
                                        className="anim-btn"
                                        onClick={stopAnimation}
                                        disabled={animationFrames.length === 0}
                                        title="Stop"
                                    >
                                        <Square size={14} />
                                    </button>
                                    <button
                                        className="anim-btn primary"
                                        onClick={isAnimating ? pauseAnimation : playAnimation}
                                        disabled={animationFrames.length === 0}
                                        title={isAnimating ? "Pause" : "Play"}
                                    >
                                        {isAnimating ? <Pause size={16} /> : <Play size={16} />}
                                    </button>
                                </div>

                                {/* Speed Control */}
                                <div className="speed-control">
                                    <label>Speed: {animationSpeed}x</label>
                                    <input
                                        type="range"
                                        min="0.5"
                                        max="4"
                                        step="0.5"
                                        value={animationSpeed}
                                        onChange={(e) => setAnimationSpeed(parseFloat(e.target.value))}
                                    />
                                </div>

                                {/* Frame Counter */}
                                {animationFrames.length > 0 && (
                                    <div className="frame-counter">
                                        <span>Frame: {currentFrameIndex + 1}/{animationFrames.length}</span>
                                    </div>
                                )}
                            </div>

                            {/* Progress Bar */}
                            {animationFrames.length > 0 && (
                                <div className="animation-progress">
                                    <div
                                        className="progress-fill"
                                        style={{ width: `${((currentFrameIndex + 1) / animationFrames.length) * 100}%` }}
                                    />
                                </div>
                            )}
                        </div>

                        <TimelineController
                            currentEpoch={currentEpoch}
                            onEpochChange={setCurrentEpoch}
                            isPlaying={isPlaying}
                            onPlayPauseToggle={() => setIsPlaying(!isPlaying)}
                        />
                    </div>
                    )}
                </main>
            </div>
        </>
    );
}

export default TimeMachine;
