import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import Plot from 'react-plotly.js';
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
    AlertCircle
} from 'lucide-react';
import {
    searchStars,
    detectAnomalies,
    getHarmonizationStats,
    downloadExport,
    checkHealth,
    loadGaiaData,
    uploadData
} from '../services/api';
import SchemaMapper from '../components/SchemaMapper';
import AILab from '../components/AILab';
import Harmonizer from '../components/Harmonizer';
import './Dashboard.css';

// Sidebar Navigation Component
function Sidebar({ activeTab, setActiveTab, filters, setFilters, onResetFilters, isLoading }) {
    const navItems = [
        { id: 'overview', icon: LayoutDashboard, label: 'Overview' },
        { id: 'upload', icon: UploadCloud, label: 'Ingest Data' },
        { id: 'skymap', icon: Map, label: 'Sky Map' },
        { id: 'anomaly', icon: Brain, label: 'AI Anomaly' },
        { id: 'harmonize', icon: Link2, label: 'Harmonize' },
        { id: 'export', icon: Download, label: 'Export' },
    ];

    return (
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
                    <button
                        key={item.id}
                        className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                        onClick={() => setActiveTab(item.id)}
                    >
                        <item.icon size={18} strokeWidth={1.5} />
                        <span>{item.label}</span>
                    </button>
                ))}
            </nav>

            {/* Filters Section */}
            <div className="sidebar-filters">
                <div className="nav-section-label">
                    <Filter size={14} strokeWidth={1.5} />
                    Filters
                </div>
                <FilterControls
                    filters={filters}
                    setFilters={setFilters}
                    onResetFilters={onResetFilters}
                    isLoading={isLoading}
                />
            </div>

            {/* User Section */}
            <div className="sidebar-user">
                <div className="user-avatar">
                    <User size={16} strokeWidth={1.5} />
                </div>
                <div className="user-info">
                    <span className="user-name">Researcher</span>
                    <span className="user-role">Astronomer</span>
                </div>
                <button className="logout-btn" title="Logout">
                    <LogOut size={16} strokeWidth={1.5} />
                </button>
            </div>
        </aside>
    );
}

// Filter Controls Component
function FilterControls({ filters, setFilters, onResetFilters, isLoading }) {
    return (
        <div className="filter-controls">
            <div className="filter-group">
                <label>RA Min (°)</label>
                <div className="range-display">
                    <span>{filters.ra_min}</span>
                </div>
                <input
                    type="range"
                    min="0"
                    max="360"
                    value={filters.ra_min}
                    onChange={(e) => setFilters({ ...filters, ra_min: Number(e.target.value) })}
                    className="range-slider"
                />
            </div>
            <div className="filter-group">
                <label>RA Max (°)</label>
                <div className="range-display">
                    <span>{filters.ra_max}</span>
                </div>
                <input
                    type="range"
                    min="0"
                    max="360"
                    value={filters.ra_max}
                    onChange={(e) => setFilters({ ...filters, ra_max: Number(e.target.value) })}
                    className="range-slider"
                />
            </div>
            <div className="filter-group">
                <label>Dec Min (°)</label>
                <div className="range-display">
                    <span>{filters.dec_min}</span>
                </div>
                <input
                    type="range"
                    min="-90"
                    max="90"
                    value={filters.dec_min}
                    onChange={(e) => setFilters({ ...filters, dec_min: Number(e.target.value) })}
                    className="range-slider"
                />
            </div>
            <div className="filter-group">
                <label>Dec Max (°)</label>
                <div className="range-display">
                    <span>{filters.dec_max}</span>
                </div>
                <input
                    type="range"
                    min="-90"
                    max="90"
                    value={filters.dec_max}
                    onChange={(e) => setFilters({ ...filters, dec_max: Number(e.target.value) })}
                    className="range-slider"
                />
            </div>
            <div className="filter-group">
                <label>Mag Max</label>
                <div className="range-display">
                    <span>{filters.max_mag}</span>
                </div>
                <input
                    type="range"
                    min="0"
                    max="20"
                    step="0.5"
                    value={filters.max_mag}
                    onChange={(e) => setFilters({ ...filters, max_mag: parseFloat(e.target.value) })}
                    className="range-slider"
                />
            </div>
            <button
                className="apply-filters-btn reset-btn-style"
                onClick={onResetFilters}
                disabled={isLoading}
                style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    marginTop: '1rem'
                }}
            >
                <RefreshCw size={14} />
                Reset Filters
            </button>
        </div>
    );
}

// Header Component
function Header({ onExport }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [showExportMenu, setShowExportMenu] = useState(false);

    return (
        <header className="dashboard-header">
            {/* Search Bar */}
            <div className="header-search">
                <Search size={16} strokeWidth={1.5} />
                <input
                    type="text"
                    placeholder="Search stars, coordinates, or anomalies..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            {/* Actions */}
            <div className="header-actions">
                {/* Export Dropdown */}
                <div className="export-dropdown">
                    <button
                        className="export-btn"
                        onClick={() => setShowExportMenu(!showExportMenu)}
                    >
                        <Download size={16} strokeWidth={1.5} />
                        <span>Export</span>
                        <ChevronDown size={14} strokeWidth={1.5} />
                    </button>
                    {showExportMenu && (
                        <div className="export-menu">
                            <button onClick={() => { onExport('csv'); setShowExportMenu(false); }}>
                                Export as CSV
                            </button>
                            <button onClick={() => { onExport('json'); setShowExportMenu(false); }}>
                                Export as JSON
                            </button>
                            <button onClick={() => { onExport('votable'); setShowExportMenu(false); }}>
                                Export as VOTable
                            </button>
                        </div>
                    )}
                </div>

                {/* User Profile */}
                <div className="user-profile">
                    <div className="profile-avatar">
                        <User size={16} strokeWidth={1.5} />
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
                <Icon size={20} strokeWidth={1.5} />
            </div>
            <div className="stat-content">
                <span className="stat-label">{label}</span>
                <span className="stat-value">
                    {isLoading ? '...' : value?.toLocaleString() || '0'}
                </span>
                {trend && <span className="stat-trend">{trend}</span>}
            </div>
        </div>
    );
}

// Sky Map Component
function SkyMap({ stars, anomalies, isLoading }) {
    const [showAnomalies, setShowAnomalies] = useState(true);
    const navigate = useNavigate();

    // Prepare plot data
    const anomalyIds = new Set(anomalies?.map(a => a.id) || []);

    const normalStars = stars?.filter(s => !anomalyIds.has(s.id)) || [];
    const anomalyStars = stars?.filter(s => anomalyIds.has(s.id)) || [];

    const plotData = [
        // Normal stars
        {
            type: 'scatter',
            mode: 'markers',
            name: 'Stars',
            x: normalStars.map(s => 360 - (s.ra_deg || 0)),
            y: normalStars.map(s => s.dec_deg || 0),
            customdata: normalStars.map(s => s.id),
            marker: {
                size: normalStars.map(s => Math.max(3, 12 - (s.brightness_mag || 10))),
                color: '#e8a87c',
                opacity: 0.8,
            },
            text: normalStars.map(s => `${s.source_id}<br>RA: ${s.ra_deg?.toFixed(2)}°<br>Dec: ${s.dec_deg?.toFixed(2)}°<br>Mag: ${s.brightness_mag?.toFixed(2)}<br><i>Click to view details</i>`),
            hoverinfo: 'text',
        },
        // Anomalies
        ...(showAnomalies ? [{
            type: 'scatter',
            mode: 'markers',
            name: 'Anomalies',
            x: anomalyStars.map(s => 360 - (s.ra_deg || 0)),
            y: anomalyStars.map(s => s.dec_deg || 0),
            customdata: anomalyStars.map(s => s.id),
            marker: {
                size: 12,
                color: '#d4683a',
                symbol: 'diamond',
                line: { width: 1, color: '#e8a87c' }
            },
            text: anomalyStars.map(s => `⚠️ ANOMALY<br>${s.source_id}<br>RA: ${s.ra_deg?.toFixed(2)}°<br>Dec: ${s.dec_deg?.toFixed(2)}°<br><i>Click to view details</i>`),
            hoverinfo: 'text',
        }] : []),
    ];

    const layout = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#888888', family: 'Inter, sans-serif' },
        margin: { t: 40, r: 20, b: 50, l: 60 },
        xaxis: {
            title: { text: 'Right Ascension (°)', font: { size: 12 } },
            range: [360, 0],
            gridcolor: 'rgba(42, 42, 42, 0.5)',
            zerolinecolor: 'rgba(42, 42, 42, 0.5)',
            tickfont: { size: 10 },
        },
        yaxis: {
            title: { text: 'Declination (°)', font: { size: 12 } },
            range: [-90, 90],
            gridcolor: 'rgba(42, 42, 42, 0.5)',
            zerolinecolor: 'rgba(42, 42, 42, 0.5)',
            tickfont: { size: 10 },
        },
        showlegend: true,
        legend: {
            x: 1,
            y: 1,
            xanchor: 'right',
            bgcolor: 'rgba(26, 26, 26, 0.8)',
            bordercolor: '#2a2a2a',
            borderwidth: 1,
            font: { size: 11 }
        },
        dragmode: 'zoom',
        hovermode: 'closest',
    };

    const config = {
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        responsive: true,
    };

    // Handle click on star
    const handlePlotClick = (event) => {
        if (event.points && event.points.length > 0) {
            const point = event.points[0];
            const starId = point.customdata;
            if (starId) {
                navigate(`/star/${starId}`);
            }
        }
    };

    return (
        <div className="skymap-container">
            <div className="skymap-header">
                <h2>Interactive Sky Map</h2>
                <div className="skymap-controls">
                    <span className="click-hint">Click on any star to view details</span>
                    <label className="toggle-label">
                        <input
                            type="checkbox"
                            checked={showAnomalies}
                            onChange={(e) => setShowAnomalies(e.target.checked)}
                        />
                        <span>Show Anomalies</span>
                    </label>
                </div>
            </div>
            <div className="skymap-plot">
                {isLoading ? (
                    <div className="skymap-loading">
                        <RefreshCw size={24} className="spin" />
                        <span>Loading star data...</span>
                    </div>
                ) : (
                    <Plot
                        data={plotData}
                        layout={layout}
                        config={config}
                        style={{ width: '100%', height: '100%' }}
                        useResizeHandler={true}
                        onClick={handlePlotClick}
                    />
                )}
            </div>
        </div>
    );
}

// Anomaly List Component
function AnomalyList({ anomalies, isLoading }) {
    const navigate = useNavigate();

    return (
        <div className="anomaly-list">
            <div className="list-header">
                <h3>Recent Anomalies</h3>
                <span className="anomaly-count">{anomalies?.length || 0} detected</span>
            </div>
            <div className="list-content">
                {isLoading ? (
                    <div className="list-loading">Loading...</div>
                ) : anomalies?.slice(0, 8).map((anomaly, index) => (
                    <div
                        key={anomaly.id}
                        className="anomaly-item clickable"
                        style={{ animationDelay: `${index * 0.05}s` }}
                        onClick={() => navigate(`/star/${anomaly.id}`)}
                        title="Click to view star details"
                    >
                        <div className="anomaly-indicator">
                            <span className="pulse-dot"></span>
                        </div>
                        <div className="anomaly-info">
                            <span className="anomaly-id">{anomaly.source_id}</span>
                            <span className="anomaly-coords">
                                RA: {anomaly.ra_deg?.toFixed(2)}° | Dec: {anomaly.dec_deg?.toFixed(2)}°
                            </span>
                        </div>
                        <div className="anomaly-score">
                            Score: {Math.abs(anomaly.anomaly_score || 0).toFixed(3)}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// Upload View Component
function UploadView({ setActiveTab }) {
    const [dragActive, setDragActive] = useState(false);
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFiles(e.dataTransfer.files);
        }
    };

    const handleChange = (e) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            handleFiles(e.target.files);
        }
    };

    const handleFiles = (fileList) => {
        setFiles(Array.from(fileList));
        setResult(null);
        setError(null);
    };

    const handleUpload = async () => {
        if (!files.length) return;

        setUploading(true);
        setProgress(0);
        setError(null);
        setResult(null);

        try {
            // Upload first file only for now (backend supports single file auto-detect)
            const result = await uploadData(files[0], (event) => {
                const percent = Math.round((event.loaded * 100) / event.total);
                setProgress(percent);
            });

            setResult(result);
        } catch (err) {
            console.error("Upload failed:", err);
            setError(err.response?.data?.detail?.message || "Failed to upload file. Please try again.");
        } finally {
            setUploading(false);
        }
    };

    const resetUpload = () => {
        setFiles([]);
        setResult(null);
        setError(null);
        setProgress(0);
    };

    return (
        <div className="upload-view">
            <div className="upload-header">
                <h2>Data Ingestion & Unification</h2>
                <p>Upload raw astronomical data (FITS, CSV, JSON). The system will automatically detect the format, parse coordinates, and unify it into the COSMIC catalog.</p>
            </div>

            {!result ? (
                <div className="upload-container">
                    <div
                        className={`drop-zone ${dragActive ? 'active' : ''} ${files.length ? 'has-file' : ''}`}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                        onClick={() => document.getElementById('file-upload').click()}
                    >
                        <input
                            type="file"
                            id="file-upload"
                            multiple={false}
                            onChange={handleChange}
                            style={{ display: 'none' }}
                        />

                        {files.length > 0 ? (
                            <div className="file-preview">
                                <FileText size={48} className="file-icon" />
                                <div className="file-info">
                                    <span className="file-name">{files[0].name}</span>
                                    <span className="file-size">{(files[0].size / 1024).toFixed(1)} KB</span>
                                </div>
                                <button className="remove-file" onClick={(e) => { e.stopPropagation(); resetUpload(); }}>
                                    <XCircle size={20} />
                                </button>
                            </div>
                        ) : (
                            <div className="drop-prompt">
                                <UploadCloud size={64} className="upload-icon" />
                                <h3>Drag & Drop files here</h3>
                                <span>or click to browse</span>
                                <p className="supported-formats">Supported: FITS, CSV, JSON</p>
                            </div>
                        )}
                    </div>

                    {files.length > 0 && (
                        <div className="upload-actions">
                            <button
                                className="upload-btn"
                                onClick={handleUpload}
                                disabled={uploading}
                            >
                                {uploading ? `Uploading... ${progress}%` : 'Ingest Data'}
                            </button>
                            {uploading && (
                                <div className="progress-bar">
                                    <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                                </div>
                            )}
                        </div>
                    )}

                    {error && (
                        <div className="upload-error">
                            <AlertCircle size={20} />
                            <span>{error}</span>
                        </div>
                    )}
                </div>
            ) : (
                <div className="upload-result">
                    <div className="result-card">
                        <CheckCircle size={64} className="success-icon" />
                        <h3>Ingestion Successful!</h3>
                        <p>{result.message}</p>

                        <div className="result-stats">
                            <div className="result-stat">
                                <span className="label">Total Records</span>
                                <span className="value">{result.counts?.total || 0}</span>
                            </div>
                            <div className="result-stat">
                                <span className="label">Successfully Ingested</span>
                                <span className="value highlight">{result.counts?.success || 0}</span>
                            </div>
                            <div className="result-stat">
                                <span className="label">Failed/Skipped</span>
                                <span className="value warning">{result.counts?.failed || 0}</span>
                            </div>
                        </div>

                        <div className="result-details">
                            <h4>Dataset Details</h4>
                            <div className="detail-grid">
                                <div className="detail-item">
                                    <span>Dataset ID:</span>
                                    <code>{result.dataset_id}</code>
                                </div>
                                <div className="detail-item">
                                    <span>Source:</span>
                                    <code>{files[0]?.name}</code>
                                </div>
                            </div>
                        </div>

                        <div className="action-buttons" style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                            <button
                                className="visualize-btn"
                                onClick={() => setActiveTab('skymap')}
                                style={{
                                    background: 'linear-gradient(135deg, #e8a87c 0%, #d4683a 100%)',
                                    color: 'white',
                                    border: 'none',
                                    padding: '0.75rem 1.5rem',
                                    borderRadius: '8px',
                                    fontWeight: '600',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    flex: 1,
                                    justifyContent: 'center'
                                }}
                            >
                                <Map size={18} />
                                Visualize in Sky Map
                            </button>
                            <button
                                className="reset-btn"
                                onClick={resetUpload}
                                style={{ flex: 1 }}
                            >
                                Upload Another File
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Main Dashboard Component
function Dashboard() {
    const [searchParams, setSearchParams] = useSearchParams();
    const navigate = useNavigate();

    // Initialize state from URL or defaults
    const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'overview');

    // Filter state initialized from URL
    const [filters, setFilters] = useState({
        ra_min: Number(searchParams.get('ra_min')) || 0,
        ra_max: Number(searchParams.get('ra_max')) || 360,
        dec_min: Number(searchParams.get('dec_min')) || -90,
        dec_max: Number(searchParams.get('dec_max')) || 90,
        max_mag: Number(searchParams.get('max_mag')) || 20
    });

    const [stars, setStars] = useState([]);
    const [anomalies, setAnomalies] = useState([]);
    const [stats, setStats] = useState({});
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

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
        setIsLoading(true);
        try {
            // Number() ensures we handle 0 correctly and don't get NaN
            const starsResponse = await searchStars({
                limit: 1000,
                ra_min: Number(filters.ra_min),
                ra_max: Number(filters.ra_max),
                dec_min: Number(filters.dec_min),
                dec_max: Number(filters.dec_max),
                max_mag: Number(filters.max_mag)
            });
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
            max_mag: 20
        };
        setFilters(defaults);
        // The useEffect will pick up the change and auto-fetch
    };

    // Auto-apply filters with debounce
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchStarsData();
        }, 800);

        return () => clearTimeout(timer);
    }, [fetchStarsData]);

    // Initial data load handled by separate effect below, but we can merge if needed.
    // Ideally, we want initial load to populate filters, or filters to drive initial load.
    // The existing 'Fetch data on mount' effect does health check + initial load.
    // To avoid double-fetch, we should rely on this filter effect for updates.
    // However, the initial load includes anomaly detection checks which this doesn't.
    // So we keep them separate but be aware of potential race condition on mount.

    // Fetch data on mount
    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            setError(null);

            try {
                // Check health first
                await checkHealth();

                // Try to fetch stars first
                let starsResponse;
                try {
                    starsResponse = await searchStars({ limit: 1000 });
                } catch (starErr) {
                    console.error('Failed to fetch stars:', starErr);
                    starsResponse = { records: [], total_count: 0 };
                }

                // If no stars, try to load Gaia data automatically
                if (!starsResponse.records?.length || starsResponse.total_count === 0) {
                    console.log('No star data found, loading Gaia sample data...');
                    try {
                        await loadGaiaData();
                        // Re-fetch stars after loading
                        starsResponse = await searchStars({ limit: 1000 });
                    } catch (loadErr) {
                        console.error('Failed to load Gaia data:', loadErr);
                    }
                }

                setStars(starsResponse.records || []);

                // Try to detect anomalies (may fail if not enough data)
                let anomaliesResponse = { anomalies: [], anomaly_count: 0 };
                try {
                    anomaliesResponse = await detectAnomalies(0.05);
                } catch (anomalyErr) {
                    // Handle insufficient data gracefully
                    console.warn('Anomaly detection failed (likely insufficient data):', anomalyErr);
                }

                setAnomalies(anomaliesResponse.anomalies || []);

                // Try to get harmonization stats
                let statsResponse = { unique_fusion_groups: 0 };
                try {
                    statsResponse = await getHarmonizationStats();
                } catch (statsErr) {
                    console.warn('Harmonization stats failed:', statsErr);
                }

                setStats({
                    totalStars: starsResponse.total_count || starsResponse.records?.length || 0,
                    fusionGroups: statsResponse.unique_fusion_groups || 0,
                    anomalyCount: anomaliesResponse.anomaly_count || 0,
                    sources: 2, // Gaia + TESS
                });

            } catch (err) {
                console.error('Failed to fetch data:', err);
                setError('Failed to connect to the backend. Make sure the server is running.');
            } finally {
                setIsLoading(false);
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

    return (
        <div className="dashboard">
            <Sidebar
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                filters={filters}
                setFilters={setFilters}
                onResetFilters={handleResetFilters}
                isLoading={isLoading}
            />

            <main className="dashboard-main">
                <Header onExport={handleExport} />

                {error ? (
                    <div className="error-banner">
                        <AlertTriangle size={18} />
                        <span>{error}</span>
                        <button onClick={() => window.location.reload()}>Retry</button>
                    </div>
                ) : activeTab === 'upload' ? (
                    <UploadView setActiveTab={setActiveTab} />
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
