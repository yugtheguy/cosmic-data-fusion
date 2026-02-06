import { useState, useEffect, useCallback, useRef } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import Plot from 'react-plotly.js';
import { useDataCache } from '../hooks/useDataCache';
import { useAuth } from '../context/AuthContext';
import {
    LayoutDashboard,
    Map,
    Brain,
    Link2,
    Download,
    Search,
    User,
    ChevronDown,
    Star,
    GitMerge,
    AlertTriangle,
    Database,
    Filter,
    RefreshCw,
    LogOut,
    UploadCloud,
    FileText,
    CheckCircle,
    XCircle,
    AlertCircle,
    Target,
    Clock,
    Eye,
    BookOpen,
    Sparkles
} from 'lucide-react';
import {
    searchStars,
    detectAnomalies,
    getHarmonizationStats,
    downloadExport,
    checkHealth,
    loadGaiaData,
    uploadData,
    previewData,
    getDatasets,

    deleteDataset
} from '../services/api';
import SchemaMapper from '../components/SchemaMapper';
import AILab from '../components/AILab';
import Harmonizer from '../components/Harmonizer';
import ResultsTable from '../components/ResultsTable';
import CoordinateResolver from '../components/CoordinateResolver';
import SkyMap from '../components/SkyMap';
import UploadView from '../components/UploadView';
import './Dashboard.css';
import Sidebar from '../components/Sidebar';

// Header Component
function Header({ onExport, onRefresh, cacheStatus }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [showExportMenu, setShowExportMenu] = useState(false);

    return (
        <header className="dashboard-header">
            <div className="header-search">
                <Search size={18} className="search-icon" />
                <input
                    type="text"
                    placeholder="Search stars (ID, Coordinates)..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            <div className="header-actions">
                <div className="cache-status">
                    {cacheStatus === 'loading' ? (
                        <span className="status-indicator loading">
                            <span className="dot"></span> Syncing
                        </span>
                    ) : (
                        <span className="status-indicator active">
                            <span className="dot"></span> Live
                        </span>
                    )}
                </div>

                <div className="action-group">
                    <button className="icon-btn" title="Refresh Data" onClick={onRefresh}>
                        <RefreshCw size={18} />
                    </button>
                    <div className="dropdown-container">
                        <button
                            className="icon-btn"
                            title="Export Data"
                            onClick={() => setShowExportMenu(!showExportMenu)}
                        >
                            <Download size={18} />
                        </button>
                        {showExportMenu && (
                            <div className="dropdown-menu">
                                <button onClick={() => { onExport('csv'); setShowExportMenu(false); }}>Export as CSV</button>
                                <button onClick={() => { onExport('json'); setShowExportMenu(false); }}>Export as JSON</button>
                                <button onClick={() => { onExport('votable'); setShowExportMenu(false); }}>Export as VOTable</button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}

// Stats Card Component
function StatCard({ icon: Icon, label, value, trend, isLoading }) {
    return (
        <div className="stat-card">
            <div className="stat-icon">
                <Icon size={24} />
            </div>
            <div className="stat-content">
                <span className="stat-label">{label}</span>
                {isLoading ? (
                    <div className="skeleton-text"></div>
                ) : (
                    <div className="stat-value-container">
                        <span className="stat-value">{value}</span>
                        {trend && (
                            <span className={`stat-trend ${trend >= 0 ? 'positive' : 'negative'}`}>
                                {trend >= 0 ? '+' : ''}{trend}%
                            </span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

// Anomaly List Component
function AnomalyList({ anomalies, isLoading }) {
    const navigate = useNavigate();

    if (isLoading) return <div className="loading-state">Loading anomalies...</div>;

    return (
        <div className="anomaly-list">
            <div className="list-header">
                <h3>Recent Anomalies</h3>
                <span className="anomaly-count">{anomalies?.length || 0} detected</span>
            </div>
            <div className="list-content">
                {anomalies.length === 0 ? (
                    <div className="empty-state">No anomalies detected</div>
                ) : (
                    anomalies.slice(0, 5).map((anomaly, index) => (
                        <div key={index} className="anomaly-item clickable" onClick={() => navigate(`/star/${anomaly.id}`)}>
                            <div className="anomaly-icon">
                                <AlertTriangle size={16} />
                            </div>
                            <div className="anomaly-info">
                                <span className="anomaly-id">{anomaly.source_id}</span>
                                <span className="anomaly-score">Score: {anomaly.score?.toFixed(3)}</span>
                            </div>
                            <div className="view-btn">
                                <ChevronDown size={16} style={{ transform: 'rotate(-90deg)' }} />
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}





// Main Dashboard Component
function Dashboard() {
    const [searchParams, setSearchParams] = useSearchParams();
    const navigate = useNavigate();
    const { user, logout, isAuthenticated, loading } = useAuth();

    // Redirect to login if not authenticated
    useEffect(() => {
        if (!loading && !isAuthenticated) {
            navigate('/login');
        }
    }, [isAuthenticated, loading, navigate]);

    // Cache integration
    const { getCached, updateCache, cacheMetadata, invalidateCache, CACHE_KEYS } = useDataCache();

    // Initialize state from URL or defaults
    const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'overview');

    // Filter state initialized from URL
    const [filters, setFilters] = useState({
        ra_min: Number(searchParams.get('ra_min')) || 0,
        ra_max: Number(searchParams.get('ra_max')) || 360,
        dec_min: Number(searchParams.get('dec_min')) || -90,
        dec_max: Number(searchParams.get('dec_max')) || 90,
        max_mag: Number(searchParams.get('max_mag')) || 25, // Match UI slider max
        dataset_ids: []
    });

    // Debug: Log when filters change
    useEffect(() => {
        console.log('🔧 Filters changed:', filters);
    }, [filters]);

    const [datasets, setDatasets] = useState([]);

    const [stars, setStars] = useState([]);
    const [anomalies, setAnomalies] = useState([]);
    const [stats, setStats] = useState({});
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [cacheStatus, setCacheStatus] = useState(null);

    // Debug: Log when stars change
    useEffect(() => {
        console.log('⭐ Stars state changed:', stars.length, 'stars');
    }, [stars]);

    // Sync state changes to URL
    useEffect(() => {
        const params = {};
        if (activeTab) params.tab = activeTab;

        // Add filters only if non-default (optional, but cleaner URL)
        // For now, simple sync
        params.ra_min = filters.ra_min;
        params.ra_max = filters.ra_max;
        params.dec_min = filters.dec_min;
        params.dec_max = filters.dec_max;
        params.max_mag = filters.max_mag;

        setSearchParams(params, { replace: true });
    }, [activeTab, filters, setSearchParams]);

    // Unified fetch logic
    const fetchStarsData = useCallback(async () => {
        console.log('🔄 fetchStarsData callback (re)created');
        setIsLoading(true);
        try {
            // Build query params - only include non-default filters
            const queryParams = {
                limit: 10000, // Increase to ensure we get all stars
            };

            // Only add spatial filters if they're not the full sky defaults
            if (filters.ra_min !== 0 || filters.ra_max !== 360) {
                queryParams.ra_min = Number(filters.ra_min);
                queryParams.ra_max = Number(filters.ra_max);
            }
            if (filters.dec_min !== -90 || filters.dec_max !== 90) {
                queryParams.dec_min = Number(filters.dec_min);
                queryParams.dec_max = Number(filters.dec_max);
            }

            // Only add magnitude filter if user explicitly set it (not default 20)
            // The UI magnitude slider goes from -30 to 25, so only filter if it's actually constrained
            if (filters.max_mag && filters.max_mag < 25) {
                queryParams.max_mag = Number(filters.max_mag);
            }

            if (filters.dataset_ids && filters.dataset_ids.length > 0) {
                queryParams.dataset_ids = filters.dataset_ids;
            }

            console.log('🔍 fetchStarsData called with filters:', filters);
            console.log('📊 Query params being sent:', queryParams);

            const starsResponse = await searchStars(queryParams);
            console.log('✅ Received stars response:', starsResponse.total_count, 'total,', starsResponse.returned_count, 'returned');

            setStars(starsResponse.records || []);
            setStats(prev => ({
                ...prev,
                totalStars: starsResponse.total_count || starsResponse.records?.length || 0
            }));
        } catch (err) {
            console.error('Failed to apply filters:', err);
            setError('Failed to update filters. Check server connection.');
        } finally {
            setIsLoading(false);
        }
    }, [filters]);

    // Manual apply (for the button) - Kept for safety against stale HMR/Cache
    const handleApplyFilters = () => {
        fetchStarsData();
    };

    // Reset filters to defaults
    const handleResetFilters = () => {
        const defaults = {
            ra_min: 0,
            ra_max: 360,
            dec_min: -90,
            dec_max: 90,
            max_mag: 25, // Match UI slider max
            dataset_ids: []
        };
        setFilters(defaults);
        // The useEffect will pick up the change and auto-fetch
    };

    const fetchDatasets = useCallback(async () => {
        try {
            const data = await getDatasets();
            setDatasets(data.datasets || []);
        } catch (err) {
            console.error('Failed to fetch datasets:', err);
        }
    }, []);

    const handleDeleteDataset = async (datasetId) => {
        if (!window.confirm('Are you sure you want to delete this dataset? This cannot be undone.')) return;

        try {
            await deleteDataset(datasetId);
            // Invalidate caches since data has changed
            invalidateCache(CACHE_KEYS.STARS);
            invalidateCache(CACHE_KEYS.DATASETS);
            invalidateCache(CACHE_KEYS.ANOMALIES);
            // Refresh datasets
            fetchDatasets();
            // Clear from filters if selected
            if (filters.dataset_ids.includes(datasetId)) {
                setFilters(prev => ({
                    ...prev,
                    dataset_ids: prev.dataset_ids.filter(id => id !== datasetId)
                }));
            } else {
                // If not selected, we still might want to refresh stars if they were visible?
                // Actually stars might be deleted. So refresh stars.
                fetchStarsData();
            }
        } catch (err) {
            console.error('Failed to delete dataset:', err);
            setError('Failed to delete dataset.');
        }
    };

    // Handle upload success - invalidate caches and refresh datasets
    const handleUploadSuccess = useCallback(() => {
        console.log('📤 Upload successful - invalidating caches');
        // Invalidate all caches since new data has been uploaded
        invalidateCache(CACHE_KEYS.STARS);
        invalidateCache(CACHE_KEYS.ANOMALIES);
        invalidateCache(CACHE_KEYS.DATASETS);
        invalidateCache(CACHE_KEYS.HARMONIZE_STATS);
        // Fetch updated datasets list
        fetchDatasets();
        // Optionally refresh stars data
        fetchStarsData();
    }, [invalidateCache, CACHE_KEYS, fetchDatasets, fetchStarsData]);

    // Manual refresh handler
    const handleManualRefresh = useCallback(() => {
        console.log('🔄 Manual refresh triggered');
        // Invalidate all caches
        invalidateCache(CACHE_KEYS.STARS);
        invalidateCache(CACHE_KEYS.ANOMALIES);
        invalidateCache(CACHE_KEYS.DATASETS);
        invalidateCache(CACHE_KEYS.HARMONIZE_STATS);
        // Reset cache status
        setCacheStatus(null);
        // Reload the page to fetch fresh data
        window.location.reload();
    }, [invalidateCache, CACHE_KEYS]);

    // Track if initial load is complete
    const [initialLoadComplete, setInitialLoadComplete] = useState(false);
    const skipNextAutoApply = useRef(false);

    // Auto-apply filters with debounce (skip on initial mount)
    useEffect(() => {
        // Don't auto-apply on initial mount - let the mount effect handle it
        if (!initialLoadComplete) {
            console.log('⏭️ Skipping auto-apply: initial load not complete');
            return;
        }

        // Skip the first auto-apply after initial load completes
        if (skipNextAutoApply.current) {
            console.log('⏭️ Skipping auto-apply: just completed initial load');
            skipNextAutoApply.current = false;
            return;
        }

        console.log('⏰ Auto-apply filter triggered, will fetch in 800ms');
        const timer = setTimeout(() => {
            console.log('🚀 Auto-apply executing fetchStarsData');
            fetchStarsData();
        }, 800);

        return () => {
            clearTimeout(timer);
        };
    }, [filters, initialLoadComplete, fetchStarsData]);



    // Fetch data on mount
    useEffect(() => {
        const fetchData = async () => {
            console.log('🎬 Initial mount effect starting');
            setIsLoading(true);
            setError(null);

            try {
                // Check cache first
                const cachedStars = getCached(CACHE_KEYS.STARS);
                const cachedAnomalies = getCached(CACHE_KEYS.ANOMALIES);
                const cachedDatasets = getCached(CACHE_KEYS.DATASETS);
                const cachedStats = getCached(CACHE_KEYS.HARMONIZE_STATS);

                // If we have fresh cached data, use it
                if (cachedStars && cachedStars.fresh) {
                    console.log('✅ Using cached stars data');
                    console.log('💾 Setting stars state from cache:', cachedStars.data.records?.length || 0, 'records');
                    setStars(cachedStars.data.records || []);
                    setCacheStatus(cacheMetadata[CACHE_KEYS.STARS]);

                    if (cachedAnomalies && cachedAnomalies.fresh) {
                        setAnomalies(cachedAnomalies.data || []);
                    }

                    if (cachedDatasets && cachedDatasets.fresh) {
                        setDatasets(cachedDatasets.data || []);
                    }

                    if (cachedStats && cachedStats.fresh) {
                        const cachedStatsData = cachedStats.data;
                        setStats({
                            totalStars: cachedStars.data.total_count || cachedStars.data.records?.length || 0,
                            fusionGroups: cachedStatsData.unique_fusion_groups || 0,
                            anomalyCount: cachedAnomalies?.data?.length || 0,
                            sources: 2,
                        });
                    }

                    setIsLoading(false);
                    skipNextAutoApply.current = true; // Skip auto-apply after using cache
                    setInitialLoadComplete(true); // Mark initial load as complete
                    return; // Skip API calls
                }

                console.log('🔄 Fetching fresh data from API');

                // Check health first
                await checkHealth();

                // Load datasets
                await fetchDatasets();

                // Try to fetch stars first
                let starsResponse;
                try {
                    starsResponse = await searchStars({ limit: 10000 });
                    console.log('📥 Initial mount received:', starsResponse.total_count, 'total,', starsResponse.returned_count, 'returned');
                    // Cache the response
                    updateCache(CACHE_KEYS.STARS, starsResponse);
                } catch (starErr) {
                    console.error('Failed to fetch stars:', starErr);
                    starsResponse = { records: [], total_count: 0 };
                }

                // If no stars, just show empty message (bundled data is disabled)
                if (!starsResponse.records?.length || starsResponse.total_count === 0) {
                    console.log('No star data found. Upload your own datasets to get started!');
                }

                console.log('💾 Setting stars state with', starsResponse.records?.length || 0, 'records');
                setStars(starsResponse.records || []);

                // Try to detect anomalies (may fail if not enough data)
                let anomaliesResponse = { anomalies: [], anomaly_count: 0 };
                try {
                    anomaliesResponse = await detectAnomalies(0.05);
                    // Cache anomalies
                    updateCache(CACHE_KEYS.ANOMALIES, anomaliesResponse.anomalies || []);
                } catch (anomalyErr) {
                    // Handle insufficient data gracefully
                    console.warn('Anomaly detection failed (likely insufficient data):', anomalyErr);
                }

                setAnomalies(anomaliesResponse.anomalies || []);

                // Try to get harmonization stats
                let statsResponse = { unique_fusion_groups: 0 };
                try {
                    statsResponse = await getHarmonizationStats();
                    // Cache stats
                    updateCache(CACHE_KEYS.HARMONIZE_STATS, statsResponse);
                } catch (statsErr) {
                    console.warn('Harmonization stats failed:', statsErr);
                }

                setStats({
                    totalStars: starsResponse.total_count || starsResponse.records?.length || 0,
                    fusionGroups: statsResponse.unique_fusion_groups || 0,
                    anomalyCount: anomaliesResponse.anomaly_count || 0,
                    sources: 2, // Gaia + TESS
                });

                setCacheStatus(cacheMetadata[CACHE_KEYS.STARS]);

            } catch (err) {
                console.error('Failed to fetch data:', err);
                setError('Failed to connect to the backend. Make sure the server is running.');
            } finally {
                setIsLoading(false);
                skipNextAutoApply.current = true; // Skip the auto-apply that triggers after this
                setInitialLoadComplete(true); // Mark initial load as complete
            }
        };

        fetchData();
    }, []);

    // Handle export
    const handleExport = async (format) => {
        try {
            await downloadExport(format);
        } catch (err) {
            console.error('Export failed:', err);
        }
    };

    // Handle logout
    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="dashboard">
            <Sidebar
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                filters={filters}
                setFilters={setFilters}
                onResetFilters={handleResetFilters}
                datasets={datasets}
                onDeleteDataset={handleDeleteDataset}
                isLoading={isLoading}
                onLogout={handleLogout}
                user={user}
            />

            <main className="dashboard-main">
                <Header
                    onExport={handleExport}
                    onRefresh={handleManualRefresh}
                    cacheStatus={cacheStatus}
                />

                {error ? (
                    <div className="error-banner">
                        <AlertTriangle size={18} />
                        <span>{error}</span>
                        <button onClick={() => window.location.reload()}>Retry</button>
                    </div>
                ) : activeTab === 'results' ? (
                    <div style={{ padding: '1.5rem' }}>
                        <ResultsTable
                            data={stars}
                            isLoading={isLoading}
                            title="Stellar Catalog"
                            highlightAnomalies={true}
                            anomalyIds={anomalies.map(a => a.id)}
                        />
                    </div>
                ) : activeTab === 'upload' ? (
                    <UploadView setActiveTab={setActiveTab} onUploadSuccess={handleUploadSuccess} />
                ) : activeTab === 'coordinate-resolver' ? (
                    <CoordinateResolver />
                ) : activeTab === 'anomaly' ? (
                    <AILab />
                ) : activeTab === 'harmonize' ? (
                    <Harmonizer />
                ) : (
                    <>
                        {/* Stats Row */}
                        <div className="stats-row">
                            <StatCard
                                icon={Star}
                                label="Total Stars"
                                value={stats.totalStars}
                                isLoading={isLoading}
                            />
                            <StatCard
                                icon={GitMerge}
                                label="Fusion Groups"
                                value={stats.fusionGroups}
                                isLoading={isLoading}
                            />
                            <StatCard
                                icon={AlertTriangle}
                                label="Anomalies"
                                value={stats.anomalyCount}
                                isLoading={isLoading}
                            />
                            <StatCard
                                icon={Database}
                                label="Data Sources"
                                value={stats.sources}
                                isLoading={isLoading}
                            />
                        </div>

                        {/* Sky Map */}
                        <SkyMap
                            stars={stars}
                            anomalies={anomalies}
                            isLoading={isLoading}
                        />

                        {/* Anomaly List */}
                        <AnomalyList
                            anomalies={anomalies}
                            isLoading={isLoading}
                        />
                    </>
                )}
            </main>
        </div>
    );
}

export default Dashboard;
