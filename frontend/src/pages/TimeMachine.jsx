import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import Plot from 'react-plotly.js';
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
import historicalFacts from '../data/historicalFacts.json';
import './TimeMachine.css';


const API_BASE_URL = 'http://localhost:8000';

function TimeMachine() {
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
        raMin: 50,
        raMax: 65,
        decMin: 20,
        decMax: 30,
        maxMagnitude: 15,
        limit: 500
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

    // Region Selection for Query Builder integration
    const [selectionMode, setSelectionMode] = useState(false); // Toggle selection mode
    const [selectedStars, setSelectedStars] = useState(null); // Selected region object {raMin, raMax, decMin, decMax, stars[]}
    const [selectionCount, setSelectionCount] = useState(0); // Count of selected stars


    // URL parameters for integration with NL Chat
    const [searchParams, setSearchParams] = useSearchParams();
    const navigate = useNavigate(); // For navigation to Query Builder

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
        if (epochDiff > 500 && !isWarping) {
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

        const timer = setTimeout(() => {
            fetchStarsAtEpoch(currentEpoch);
        }, 300);

        return () => clearTimeout(timer);
    }, [currentEpoch, fetchStarsAtEpoch]);


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

    // Navigation items
    const navItems = [
        { id: 'overview', icon: LayoutDashboard, label: 'Dashboard', link: '/dashboard' },
        { id: 'timemachine', icon: Clock, label: 'Time Machine', link: '/timemachine' },
        { id: 'query', icon: Search, label: 'Query Builder', link: '/query' },
        { id: 'results', icon: Database, label: 'Data Table', link: '/dashboard' },
        { id: 'upload', icon: UploadCloud, label: 'Ingest Data', link: '/dashboard' },
        { id: 'skymap', icon: Map, label: 'Sky Map', link: '/dashboard' },
        { id: 'anomaly', icon: Brain, label: 'AI Lab', link: '/dashboard' },
        { id: 'harmonize', icon: Link2, label: 'Harmonizer', link: '/dashboard' },
        { id: 'export', icon: Download, label: 'Export', link: '/dashboard' },
    ];

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

            <div className={`dashboard ${isWarping ? 'warping' : ''} ${isFullscreen ? 'fullscreen-mode' : ''}`}>
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
                <aside className="dashboard-sidebar">
                    {/* Logo */}
                    <div className="sidebar-logo">
                        <div className="logo-mark">C</div>
                        <span className="logo-text">COSMIC</span>
                    </div>

                    {/* Navigation */}
                    <nav className="sidebar-nav">
                        <div className="nav-section-label">Navigation</div>
                        {navItems.map((item) => (
                            item.link ? (
                                <Link
                                    key={item.id}
                                    to={item.link}
                                    className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                                >
                                    <item.icon size={18} strokeWidth={1.5} />
                                    <span>{item.label}</span>
                                </Link>
                            ) : (
                                <button
                                    key={item.id}
                                    className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                                    onClick={() => setActiveTab(item.id)}
                                >
                                    <item.icon size={18} strokeWidth={1.5} />
                                    <span>{item.label}</span>
                                </button>
                            )
                        ))}
                    </nav>

                    {/* Filters */}
                    <div className="sidebar-filters">
                        <div className="nav-section-label">
                            <Filter size={14} strokeWidth={1.5} />
                            Region Filters
                        </div>
                        <div className="filter-controls">
                            <div className="filter-group">
                                <label>Right Ascension (°)</label>
                                <div className="range-inputs">
                                    <input
                                        type="number"
                                        value={filters.raMin}
                                        onChange={(e) => setFilters({ ...filters, raMin: parseFloat(e.target.value) })}
                                        placeholder="Min RA"
                                    />
                                    <span>to</span>
                                    <input
                                        type="number"
                                        value={filters.raMax}
                                        onChange={(e) => setFilters({ ...filters, raMax: parseFloat(e.target.value) })}
                                        placeholder="Max RA"
                                    />
                                </div>
                            </div>

                            <div className="filter-group">
                                <label>Declination (°)</label>
                                <div className="range-inputs">
                                    <input
                                        type="number"
                                        value={filters.decMin}
                                        onChange={(e) => setFilters({ ...filters, decMin: parseFloat(e.target.value) })}
                                        placeholder="Min Dec"
                                    />
                                    <span>to</span>
                                    <input
                                        type="number"
                                        value={filters.decMax}
                                        onChange={(e) => setFilters({ ...filters, decMax: parseFloat(e.target.value) })}
                                        placeholder="Max Dec"
                                    />
                                </div>
                            </div>

                            <div className="filter-group">
                                <label>Max Magnitude</label>
                                <input
                                    type="number"
                                    value={filters.maxMagnitude}
                                    onChange={(e) => setFilters({ ...filters, maxMagnitude: parseFloat(e.target.value) })}
                                    step="0.1"
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
                            <User size={18} />
                        </div>
                        <div className="user-info">
                            <div className="user-name">Researcher</div>
                            <div className="user-role">Temporal Analysis</div>
                        </div>
                        <button className="logout-btn">
                            <LogOut size={18} />
                        </button>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="dashboard-main">
                    {/* Header */}
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

                    {/* Stats Row */}
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

                    {/* Historical Context Card */}
                    {historicalContext && (
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

                    <div className="skymap-container">
                        <div className="skymap-header">
                            <h2>
                                <Map size={18} />
                                Temporal Star Map
                            </h2>
                            <div className="skymap-info">
                                <div className="skymap-toggles">
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
                                                // Clear selection when turning off selection mode
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
                                </div>


                                {isLoading && <span className="loading-indicator">Calculating positions...</span>}
                                {!isLoading && <span className="star-count">{stats.totalStars} stars visible</span>}
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
                            ) : (
                                <div style={{ position: 'relative' }}>
                                    {/* Confidence Heatmap Background */}
                                    {showHeatmap && (
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
                                        data={[
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
                                                    `Uncertainty: ${s.uncertainty_arcsec?.toFixed(2) || 'N/A'}″`
                                                ),
                                                hovertemplate: '%{text}<extra></extra>'
                                            },
                                            // Highlight ring for selected star
                                            ...(selectedStarId ? (() => {
                                                // Try to find in loaded stars first
                                                let selectedStar = stars.find(s => s.id === selectedStarId);

                                                // If not found, try fast movers list
                                                if (!selectedStar) {
                                                    const fastMover = fastMoversList.find(s => s.id === selectedStarId);
                                                    if (fastMover) {
                                                        selectedStar = {
                                                            ra_at_epoch: fastMover.ra_deg,
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

                                            // Star trails - lines showing movement from 2016 to current epoch
                                            ...(showTrails ? (() => {
                                                // Only show trails for stars with PM data
                                                const starsWithPM = stars.filter(s => s.pmra && s.pmdec);
                                                const topMovers = starsWithPM
                                                    .sort((a, b) => (b.total_pm || 0) - (a.total_pm || 0))
                                                    .slice(0, 50); // Top 50 movers

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

                                            // Movement vectors - arrows showing direction
                                            ...(showVectors ? (() => {
                                                const starsWithPM = stars.filter(s => s.pmra && s.pmdec && s.total_pm > 20);
                                                const topMovers = starsWithPM.slice(0, 30);

                                                return topMovers.map(s => {
                                                    // Calculate arrow endpoint (exaggerated for visibility)
                                                    const scale = 0.5; // Degrees per 1000 years approx
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

                                            // Comparison overlay - ancient epoch positions
                                            ...(compareMode ? (() => {
                                                // Calculate ancient positions (3000 BC)
                                                const ancientStars = stars.filter(s => s.pmra && s.pmdec).map(s => {
                                                    const yearsBack = currentEpoch - compareEpoch;
                                                    const pmraPerYear = s.pmra / 3600000; // deg/yr
                                                    const pmdecPerYear = s.pmdec / 3600000;
                                                    const ancient_ra = s.ra_at_epoch - pmraPerYear * yearsBack;
                                                    const ancient_dec = s.dec_at_epoch - pmdecPerYear * yearsBack;
                                                    // Calculate distance moved
                                                    const distance = Math.sqrt(
                                                        Math.pow(s.ra_at_epoch - ancient_ra, 2) +
                                                        Math.pow(s.dec_at_epoch - ancient_dec, 2)
                                                    );
                                                    return { ...s, ancient_ra, ancient_dec, distance };
                                                });

                                                // Only show top 20 with significant movement
                                                const topMovers = ancientStars
                                                    .filter(s => s.distance > 0.01) // Minimum visible movement
                                                    .sort((a, b) => b.distance - a.distance)
                                                    .slice(0, 20);

                                                // Color gradient based on rank
                                                const colors = topMovers.map((_, i) =>
                                                    `hsl(${35 + i * 5}, 100%, ${70 - i * 2}%)`
                                                );

                                                return [
                                                    // Ancient positions (amber markers with size based on rank)
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
                                                    // Gradient connecting lines
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

                                            // Uncertainty visualization - semi-transparent circles showing prediction confidence
                                            ...(showUncertainty ? (() => {
                                                try {
                                                    // Get uncertainty color based on class
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

                                                    // Filter stars with valid uncertainty data
                                                    const starsWithUncertainty = stars.filter(s =>
                                                        s.uncertainty_deg !== undefined &&
                                                        s.uncertainty_deg !== null &&
                                                        s.uncertainty_arcsec !== undefined &&
                                                        s.uncertainty_arcsec < 999999 &&
                                                        s.ra_at_epoch !== undefined &&
                                                        s.dec_at_epoch !== undefined &&
                                                        !isNaN(s.uncertainty_deg)
                                                    );

                                                    // Limit to 50 stars to prevent performance issues
                                                    const limitedStars = starsWithUncertainty.slice(0, 50);

                                                    // Create circle traces for each star
                                                    return limitedStars.map((star, idx) => {
                                                        // Calculate circle size (convert degrees to plot units)
                                                        // Scale factor to make circles visible but not overwhelming
                                                        const radius = Math.max(0.01, star.uncertainty_deg * 2); // Ensure minimum radius

                                                        // Create circle points (approximation with 20 points for performance)
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
                                                                color: getUncertaintyColor(star.uncertainty_class).replace('0.15', '0.4').replace('0.2', '0.5').replace('0.25', '0.6').replace('0.3', '0.7'),
                                                                width: 1
                                                            },
                                                            hoverinfo: 'skip',
                                                            showlegend: false,
                                                            name: `Uncertainty ${idx}`
                                                        };
                                                    });
                                                } catch (error) {
                                                    console.error('Error rendering uncertainty circles:', error);
                                                    return []; // Return empty array on error to prevent graph crash
                                                }
                                            })() : [])

                                        ]}


                                        layout={{
                                            title: null,
                                            xaxis: {
                                                title: 'Right Ascension (°)',
                                                gridcolor: 'rgba(255, 255, 255, 0.1)',
                                                color: '#888888',
                                                autorange: 'reversed'
                                            },
                                            yaxis: {
                                                title: 'Declination (°)',
                                                gridcolor: 'rgba(255, 255, 255, 0.1)',
                                                color: '#888888'
                                            },
                                            paper_bgcolor: 'transparent',
                                            plot_bgcolor: 'rgba(15, 15, 15, 0.5)',
                                            font: { family: 'Inter, sans-serif', color: '#e5e5e5' },
                                            margin: { l: 60, r: 20, t: 20, b: 60 },
                                            hovermode: 'closest',
                                            dragmode: selectionMode ? 'select' : 'pan' // Enable box select when selection mode is on
                                        }}
                                        config={{
                                            displayModeBar: true,
                                            displaylogo: false,
                                            responsive: true
                                        }}
                                        onSelected={handleStarSelection}
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
                </main>
            </div>
        </>
    );
}

export default TimeMachine;
