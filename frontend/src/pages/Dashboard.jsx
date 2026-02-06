import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import Plot from 'react-plotly.js';
import { useDataCache } from '../hooks/useDataCache';
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
import './Dashboard.css';

// Sidebar Navigation Component
function Sidebar({ activeTab, setActiveTab, filters, setFilters, onResetFilters, isLoading, datasets, onDeleteDataset }) {
    const navigate = useNavigate();
    const navItems = [
        { id: 'overview', icon: LayoutDashboard, label: 'Overview' },
        { id: 'coordinate-resolver', icon: Target, label: 'Coordinate Finder' },
        { id: 'timemachine', icon: Clock, label: 'Time Machine', link: '/timemachine' },
        { id: 'query', icon: Search, label: 'Query Builder' },
        { id: 'results', icon: Database, label: 'Data Table' },
        { id: 'upload', icon: UploadCloud, label: 'Ingest Data' },
        { id: 'skymap', icon: Map, label: 'Sky Map' },
        { id: 'anomaly', icon: Brain, label: 'AI Lab' },
        { id: 'harmonize', icon: Link2, label: 'Harmonizer' },
        { id: 'export', icon: Download, label: 'Export' },
        { id: 'planet-hunter', icon: Target, label: 'Planet Hunter', external: true },
        { id: 'ai-assistant', icon: Sparkles, label: 'AI Assistant', link: '/ai-assistant' },
        { id: 'research-methodology', icon: BookOpen, label: 'Research Methods', link: '/research-methodology' },
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
                        onClick={() => {
                            if (item.link) {
                                navigate(item.link);
                            } else if (item.id === 'query') {
                                navigate('/query');
                            } else if (item.id === 'planet-hunter') {
                                navigate('/planet-hunter');
                            } else {
                                setActiveTab(item.id);
                            }
                        }}
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
                    datasets={datasets}
                    onDeleteDataset={onDeleteDataset}
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
function FilterControls({ filters, setFilters, onResetFilters, isLoading, datasets, onDeleteDataset }) {

    const toggleDataset = (id) => {
        const currentIds = filters.dataset_ids || [];
        if (currentIds.includes(id)) {
            setFilters({
                ...filters,
                dataset_ids: currentIds.filter(d => d !== id)
            });
        } else {
            setFilters({
                ...filters,
                dataset_ids: [...currentIds, id]
            });
        }
    };

    return (
        <div className="filter-controls">
            {datasets && datasets.length > 0 && (
                <div className="filter-group">
                    <label>My Uploads</label>
                    <div className="dataset-list" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
                        {datasets?.map(d => (
                            <div key={d.id} className="dataset-item" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', flex: 1 }}>
                                    <input
                                        type="checkbox"
                                        checked={filters.dataset_ids?.includes(d.id)}
                                        onChange={() => toggleDataset(d.id)}
                                    />
                                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={d.name}>
                                        {d.name?.length > 15 ? d.name.substring(0, 15) + '...' : d.name}
                                    </span>
                                </label>
                                <button
                                    onClick={() => onDeleteDataset(d.id)}
                                    style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '0.2rem' }}
                                    title="Delete Dataset"
                                >
                                    <LogOut size={12} />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

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
function Header({ onExport, onRefresh, cacheStatus }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [showExportMenu, setShowExportMenu] = useState(false);

    return (
        <header className="dashboard-header">
            {/* Cache Status */}
            {cacheStatus && (
                <div className="cache-status" style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '10px',
                    marginRight: '20px',
                    fontSize: '0.85rem',
                    color: '#888'
                }}>
                    <span>
                        Cache: {cacheStatus.fresh ? '✓ Fresh' : '⚠ Stale'}
                        {cacheStatus.age && ` (${Math.floor(cacheStatus.age / 1000)}s old)`}
                    </span>
                    <button 
                        onClick={onRefresh}
                        style={{
                            padding: '4px 8px',
                            fontSize: '0.8rem',
                            cursor: 'pointer',
                            background: '#2a2a4a',
                            color: '#fff',
                            border: '1px solid #444',
                            borderRadius: '4px'
                        }}
                    >
                        ↻ Refresh
                    </button>
                </div>
            )}
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

// Sky Map Component - Enhanced Version
function SkyMap({ stars, anomalies, isLoading }) {
    const [showAnomalies, setShowAnomalies] = useState(true);
    const [magRange, setMagRange] = useState([-30, 25]); // Min/max magnitude filter
    const [visibleCatalogs, setVisibleCatalogs] = useState({
        'Gaia DR3': true,
        'SDSS': true,
        '2MASS': true,
        'Tycho-2': true,
        'TESS': true,
        'Other': true
    });
    const [mouseCoords, setMouseCoords] = useState({ ra: null, dec: null });
    const [selectionMode, setSelectionMode] = useState(false);
    const [selectedRegion, setSelectedRegion] = useState(null);
    const [viewBounds, setViewBounds] = useState(null); // { x: [min, max], y: [min, max] }
    const navigate = useNavigate();

    // Catalog color mapping (Orange shades)
    const catalogColors = {
        'Gaia DR3': '#d4683a', // Primary orange
        'SDSS': '#e8a87c',     // Light orange
        '2MASS': '#ef4444',    // Red (kept for contrast)
        'Tycho-2': '#f59e0b',  // Amber
        'TESS': '#8b5cf6',     // Purple (High-tech/Exoplanets)
        'Other': '#c2410c'     // Deep burnt orange
    };

    // Auto-zoom when stars change
    useEffect(() => {
        if (stars && stars.length > 0) {
            // Find bounds
            let minRa = 360, maxRa = 0, minDec = 90, maxDec = -90;
            stars.forEach(s => {
                if (s.ra_deg < minRa) minRa = s.ra_deg;
                if (s.ra_deg > maxRa) maxRa = s.ra_deg;
                if (s.dec_deg < minDec) minDec = s.dec_deg;
                if (s.dec_deg > maxDec) maxDec = s.dec_deg;
            });

            // Add padding (approx 10%)
            const raSpan = maxRa - minRa;
            const decSpan = maxDec - minDec;
            const padding = Math.max(raSpan, decSpan, 0.5) * 0.1;

            // X axis is reversed for RA (East to West)
            setViewBounds({
                x: [360 - (minRa - padding), 360 - (maxRa + padding)],
                y: [minDec - padding, maxDec + padding]
            });
        }
    }, [stars]);

    const handleResetZoom = () => {
        setViewBounds(null); // Reset to full sky
    };

    const getCatalogKey = (source) => {
        if (!source) return 'Other';
        const s = source.toLowerCase();
        if (s.includes('gaia')) return 'Gaia DR3';
        if (s.includes('sdss')) return 'SDSS';
        if (s.includes('2mass')) return '2MASS';
        if (s.includes('tycho')) return 'Tycho-2';
        if (s.includes('tess')) return 'TESS';
        return 'Other';
    };

    // Prepare plot data
    const anomalyIds = new Set(anomalies?.map(a => a.id) || []);

    // Filter stars by magnitude and catalog
    const filteredStars = (stars || []).filter(s => {
        const mag = s.brightness_mag || 10;
        const catalog = getCatalogKey(s.original_source);
        return mag >= magRange[0] && mag <= magRange[1] && visibleCatalogs[catalog];
    });

    const normalStars = filteredStars.filter(s => !anomalyIds.has(s.id));
    const anomalyStars = filteredStars.filter(s => anomalyIds.has(s.id));

    // Group stars by catalog for separate traces
    const catalogGroups = {};
    normalStars.forEach(s => {
        const catalog = getCatalogKey(s.original_source);
        if (!catalogGroups[catalog]) catalogGroups[catalog] = [];
        catalogGroups[catalog].push(s);
    });

    // Create plot traces for each catalog
    const plotData = Object.entries(catalogGroups).map(([catalog, catStars]) => ({
        type: 'scatter',
        mode: 'markers',
        name: catalog,
        x: catStars.map(s => 360 - (s.ra_deg || 0)),
        y: catStars.map(s => s.dec_deg || 0),
        customdata: catStars.map(s => s.id),
        marker: {
            size: catStars.map(s => Math.max(6, 16 - (s.brightness_mag || 10) * 0.8)), // Slightly larger for visibility
            color: catalogColors[catalog],
            opacity: 0.85,
            line: { width: 0.5, color: 'rgba(255,255,255,0.3)' }
        },
        text: catStars.map(s => `<b>${s.source_id}</b><br>Catalog: ${catalog}<br>RA: ${s.ra_deg?.toFixed(4)}°<br>Dec: ${s.dec_deg?.toFixed(4)}°<br>Mag: ${s.brightness_mag?.toFixed(2)}<br><i>Click to view details</i>`),
        hoverinfo: 'text',
    }));

    // Add anomalies trace
    if (showAnomalies && anomalyStars.length > 0) {
        plotData.push({
            type: 'scatter',
            mode: 'markers',
            name: '⚠️ Anomalies',
            x: anomalyStars.map(s => 360 - (s.ra_deg || 0)),
            y: anomalyStars.map(s => s.dec_deg || 0),
            customdata: anomalyStars.map(s => s.id),
            marker: {
                size: 14,
                color: '#ff6b6b',
                symbol: 'diamond',
                line: { width: 2, color: '#fff' }
            },
            text: anomalyStars.map(s => `<b>⚠️ ANOMALY</b><br>${s.source_id}<br>RA: ${s.ra_deg?.toFixed(4)}°<br>Dec: ${s.dec_deg?.toFixed(4)}°<br><i>Click to investigate</i>`),
            hoverinfo: 'text',
        });
    }

    const layout = {
        paper_bgcolor: 'rgba(8, 8, 20, 0.95)',
        plot_bgcolor: 'rgba(12, 12, 30, 0.9)',
        font: { color: '#a0a0a0', family: 'Inter, sans-serif' },
        margin: { t: 30, r: 30, b: 60, l: 70 },
        xaxis: {
            title: { text: 'Right Ascension (°)', font: { size: 12, color: '#888' } },
            range: viewBounds ? viewBounds.x : [360, 0],
            gridcolor: 'rgba(60, 60, 80, 0.4)',
            zerolinecolor: 'rgba(100, 100, 120, 0.5)',
            tickfont: { size: 10 },
            dtick: viewBounds ? undefined : 30, // Auto ticks when zoomed
        },
        yaxis: {
            title: { text: 'Declination (°)', font: { size: 12, color: '#888' } },
            range: viewBounds ? viewBounds.y : [-90, 90],
            gridcolor: 'rgba(60, 60, 80, 0.4)',
            zerolinecolor: 'rgba(100, 100, 120, 0.5)',
            tickfont: { size: 10 },
            dtick: viewBounds ? undefined : 30, // Auto ticks when zoomed
        },
        showlegend: true,
        legend: {
            x: 0.01,
            y: 0.99,
            xanchor: 'left',
            yanchor: 'top',
            bgcolor: 'rgba(20, 20, 35, 0.9)',
            bordercolor: 'rgba(100, 100, 120, 0.5)',
            borderwidth: 1,
            font: { size: 11 }
        },
        dragmode: selectionMode ? 'select' : 'zoom',
        hovermode: 'closest',
        // Add subtle background shapes for celestial equator
        shapes: [
            { type: 'line', x0: 0, x1: 360, y0: 0, y1: 0, line: { color: 'rgba(100,100,150,0.3)', width: 1, dash: 'dot' } }
        ],
    };

    const config = {
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d'],
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

    // Handle hover for coordinate readout
    const handleHover = (event) => {
        if (event.points && event.points.length > 0) {
            const point = event.points[0];
            setMouseCoords({
                ra: (360 - point.x).toFixed(4),
                dec: point.y.toFixed(4)
            });
        }
    };

    // Handle selection
    const handleSelection = (event) => {
        if (event.range) {
            const raMax = 360 - event.range.x[0];
            const raMin = 360 - event.range.x[1];
            const decMin = event.range.y[0];
            const decMax = event.range.y[1];
            setSelectedRegion({ raMin, raMax, decMin, decMax });
        }
    };

    const toggleCatalog = (catalog) => {
        setVisibleCatalogs(prev => ({ ...prev, [catalog]: !prev[catalog] }));
    };

    const querySelectedRegion = () => {
        if (selectedRegion) {
            navigate(`/query?mode=box&raMin=${selectedRegion.raMin.toFixed(2)}&raMax=${selectedRegion.raMax.toFixed(2)}&decMin=${selectedRegion.decMin.toFixed(2)}&decMax=${selectedRegion.decMax.toFixed(2)}`);
        }
    };

    return (
        <div className="skymap-container enhanced">
            {/* Header */}
            <div className="skymap-header">
                <div className="skymap-title-section">
                    <h2>🌌 Interactive Sky Map</h2>
                    <div className="skymap-stats">
                        <span className="stat-badge">{filteredStars.length.toLocaleString()} stars visible</span>
                        {anomalyStars.length > 0 && <span className="stat-badge anomaly">{anomalyStars.length} anomalies</span>}
                    </div>
                </div>

                {/* Coordinate Readout */}
                <div className="coord-readout">
                    <span className="coord-label">RA:</span>
                    <span className="coord-value">{mouseCoords.ra || '—'}°</span>
                    <span className="coord-label">Dec:</span>
                    <span className="coord-value">{mouseCoords.dec || '—'}°</span>

                    {/* View Controls */}
                    <div className="view-controls" style={{ marginLeft: '1rem', display: 'flex', gap: '8px' }}>
                        <button
                            className="view-btn"
                            onClick={() => setViewBounds(null)}
                            title="Reset to full sky view"
                            style={{
                                background: 'transparent',
                                border: '1px solid rgba(255,255,255,0.2)',
                                color: '#aaa',
                                padding: '2px 8px',
                                borderRadius: '4px',
                                fontSize: '11px',
                                cursor: 'pointer'
                            }}
                        >
                            Full Sky
                        </button>
                        <button
                            className="view-btn"
                            title="Zoom to fit data"
                            style={{
                                background: 'rgba(59, 130, 246, 0.2)',
                                border: '1px solid rgba(59, 130, 246, 0.4)',
                                color: '#60a5fa',
                                padding: '2px 8px',
                                borderRadius: '4px',
                                fontSize: '11px',
                                cursor: 'pointer'
                            }}
                            onClick={() => {
                                // Re-calculate bounds
                                if (stars && stars.length > 0) {
                                    let minRa = 360, maxRa = 0, minDec = 90, maxDec = -90;
                                    stars.forEach(s => {
                                        if (s.ra_deg < minRa) minRa = s.ra_deg;
                                        if (s.ra_deg > maxRa) maxRa = s.ra_deg;
                                        if (s.dec_deg < minDec) minDec = s.dec_deg;
                                        if (s.dec_deg > maxDec) maxDec = s.dec_deg;
                                    });
                                    const padding = Math.max((maxRa - minRa), (maxDec - minDec), 0.5) * 0.1;
                                    setViewBounds({
                                        x: [360 - (minRa - padding), 360 - (maxRa + padding)],
                                        y: [minDec - padding, maxDec + padding]
                                    });
                                }
                            }}
                        >
                            Fit Data
                        </button>
                    </div>
                </div>
            </div>

            {/* Controls Panel */}
            <div className="skymap-controls-panel">
                {/* Catalog Toggles */}
                <div className="control-group">
                    <label className="control-label">Catalogs</label>
                    <div className="catalog-toggles">
                        {Object.keys(catalogColors).map(cat => (
                            <button
                                key={cat}
                                className={`catalog-btn ${visibleCatalogs[cat] ? 'active' : ''}`}
                                style={{ '--cat-color': catalogColors[cat] }}
                                onClick={() => toggleCatalog(cat)}
                            >
                                <span className="cat-dot"></span>
                                {cat}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Magnitude Filter */}
                <div className="control-group">
                    <label className="control-label">Magnitude: {magRange[0]} to {magRange[1]}</label>
                    <div className="mag-slider-container">
                        <input
                            type="range"
                            min="-5"
                            max="20"
                            value={magRange[1]}
                            onChange={(e) => setMagRange([magRange[0], parseInt(e.target.value)])}
                            className="mag-slider"
                        />
                    </div>
                </div>

                {/* Mode Toggles */}
                <div className="control-group inline">
                    <label className="toggle-label">
                        <input
                            type="checkbox"
                            checked={showAnomalies}
                            onChange={(e) => setShowAnomalies(e.target.checked)}
                        />
                        <span>Anomalies</span>
                    </label>
                    <button
                        className={`selection-btn ${selectionMode ? 'active' : ''}`}
                        onClick={() => setSelectionMode(!selectionMode)}
                    >
                        {selectionMode ? '✓ Selection Mode' : '☐ Select Region'}
                    </button>
                </div>
            </div>

            {/* Selection Popup */}
            {selectedRegion && (
                <div className="selection-popup">
                    <div className="selection-info">
                        <strong>Selected Region:</strong><br />
                        RA: {selectedRegion.raMin.toFixed(2)}° – {selectedRegion.raMax.toFixed(2)}°<br />
                        Dec: {selectedRegion.decMin.toFixed(2)}° – {selectedRegion.decMax.toFixed(2)}°
                    </div>
                    <div className="selection-actions">
                        <button className="query-btn" onClick={querySelectedRegion}>
                            Query This Region
                        </button>
                        <button className="clear-btn" onClick={() => setSelectedRegion(null)}>
                            Clear
                        </button>
                    </div>
                </div>
            )}

            {/* Plot */}
            <div className="skymap-plot">
                {isLoading ? (
                    <div className="skymap-loading">
                        <RefreshCw size={32} className="spin" />
                        <span>Loading celestial data...</span>
                    </div>
                ) : (
                    <Plot
                        data={plotData}
                        layout={layout}
                        config={config}
                        style={{ width: '100%', height: '100%' }}
                        useResizeHandler={true}
                        onClick={handlePlotClick}
                        onHover={handleHover}
                        onSelected={handleSelection}
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
function UploadView({ setActiveTab, onUploadSuccess }) {
    const [dragActive, setDragActive] = useState(false);
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [processingPreview, setProcessingPreview] = useState(false);
    const [progress, setProgress] = useState(0);
    const [result, setResult] = useState(null);
    const [previewResult, setPreviewResult] = useState(null);
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
        setPreviewResult(null);
        setError(null);
    };

    const handlePreview = async () => {
        if (!files.length) return;
        setProcessingPreview(true);
        setError(null);
        try {
            const data = await previewData(files[0]);
            setPreviewResult(data);
        } catch (err) {
            console.error("Preview failed:", err);
            setError("Failed to generate preview. The file format might be invalid.");
        } finally {
            setProcessingPreview(false);
        }
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
            if (onUploadSuccess) {
                onUploadSuccess();
            }
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
        setPreviewResult(null);
        setError(null);
        setProgress(0);
    };

    return (
        <div className="upload-view">
            <div className="upload-header">
                <h2>Data Ingestion & Unification</h2>
                <p>Upload raw astronomical data (FITS, CSV, JSON). The system will preview and validate your data before ingestion.</p>
            </div>

            {!result ? (
                <div className="upload-container">
                    {!previewResult ? (
                        <>
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
                                        className="preview-btn"
                                        onClick={handlePreview}
                                        disabled={processingPreview}
                                        style={{
                                            background: '#3b82f6',
                                            color: 'white',
                                            padding: '0.8rem 2rem',
                                            borderRadius: '8px',
                                            border: 'none',
                                            fontWeight: '600',
                                            fontSize: '1rem',
                                            cursor: 'pointer',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.5rem',
                                            transition: 'all 0.2s ease',
                                        }}
                                    >
                                        {processingPreview ? (
                                            <>
                                                <RefreshCw size={18} className="spin" />
                                                Analyzing Data...
                                            </>
                                        ) : (
                                            <>
                                                <Eye size={18} />
                                                Preview Data
                                            </>
                                        )}
                                    </button>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="preview-results glass-panel" style={{ padding: '1.5rem', marginTop: '1rem' }}>
                            <div className="preview-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                                <h3>Data Preview</h3>
                                <div className="preview-stats" style={{ display: 'flex', gap: '1rem' }}>
                                    <span style={{ color: '#4ade80' }}>✓ {previewResult.valid_count} Valid</span>
                                    <span style={{ color: '#f87171' }}>⚠ {previewResult.invalid_count} Invalid</span>
                                </div>
                            </div>

                            <div className="table-wrapper" style={{ maxHeight: '300px', overflow: 'auto', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                                    <thead>
                                        <tr style={{ background: 'rgba(255,255,255,0.05)', textAlign: 'left' }}>
                                            {['Source ID', 'RA (°)', 'Dec (°)', 'Mag', 'Distance (pc)'].map(h => (
                                                <th key={h} style={{ padding: '0.75rem' }}>{h}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {previewResult.samples.map((row, i) => (
                                            <tr key={i} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                                                <td style={{ padding: '0.5rem 0.75rem' }}>{row.source_id}</td>
                                                <td style={{ padding: '0.5rem 0.75rem' }}>{row.ra_deg?.toFixed(5)}</td>
                                                <td style={{ padding: '0.5rem 0.75rem' }}>{row.dec_deg?.toFixed(5)}</td>
                                                <td style={{ padding: '0.5rem 0.75rem' }}>{row.brightness_mag?.toFixed(2)}</td>
                                                <td style={{ padding: '0.5rem 0.75rem' }}>{row.distance_pc?.toFixed(1) || '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {previewResult.sample_errors && previewResult.sample_errors.length > 0 && (
                                <div className="preview-errors" style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                                    <h4 style={{ color: '#f87171', margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>Validation Issues Detected</h4>
                                    <ul style={{ margin: 0, paddingLeft: '1.5rem', fontSize: '0.85rem', color: '#fca5a5' }}>
                                        {previewResult.sample_errors.slice(0, 3).map((err, i) => (
                                            <li key={i}>{err}</li>
                                        ))}
                                        {previewResult.sample_errors.length > 3 && <li>...and {previewResult.sample_errors.length - 3} more</li>}
                                    </ul>
                                </div>
                            )}

                            <div className="preview-actions" style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', justifyContent: 'flex-end' }}>
                                <button
                                    onClick={resetUpload}
                                    style={{
                                        background: 'transparent',
                                        border: '1px solid rgba(255,255,255,0.2)',
                                        color: '#aaa',
                                        padding: '0.75rem 1.5rem',
                                        borderRadius: '8px',
                                        cursor: 'pointer'
                                    }}
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleUpload}
                                    disabled={uploading}
                                    style={{
                                        background: 'linear-gradient(135deg, #e8a87c 0%, #d4683a 100%)',
                                        color: 'white',
                                        border: 'none',
                                        padding: '0.75rem 2rem',
                                        borderRadius: '8px',
                                        fontWeight: '600',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.5rem'
                                    }}
                                >
                                    {uploading ? 'Ingesting...' : 'Confirm & Ingest'}
                                    {!uploading && <CheckCircle size={18} />}
                                </button>
                            </div>
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
                                <span className="value">{result.counts?.total || result.ingested_count + result.failed_count || 0}</span>
                            </div>
                            <div className="result-stat">
                                <span className="label">Successfully Ingested</span>
                                <span className="value highlight">{result.ingested_count || result.counts?.success || 0}</span>
                            </div>
                            <div className="result-stat">
                                <span className="label">Failed/Skipped</span>
                                <span className="value warning">{result.failed_count || result.counts?.failed || 0}</span>
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
        max_mag: Number(searchParams.get('max_mag')) || 20,
        dataset_ids: []
    });

    const [datasets, setDatasets] = useState([]);

    const [stars, setStars] = useState([]);
    const [anomalies, setAnomalies] = useState([]);
    const [stats, setStats] = useState({});
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [cacheStatus, setCacheStatus] = useState(null);

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
                limit: 5000,
                ra_min: Number(filters.ra_min),
                ra_max: Number(filters.ra_max),
                dec_min: Number(filters.dec_min),
                dec_max: Number(filters.dec_max),
                max_mag: Number(filters.max_mag),
                dataset_ids: filters.dataset_ids && filters.dataset_ids.length > 0 ? filters.dataset_ids : undefined
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
            max_mag: 20,
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
                // Check cache first
                const cachedStars = getCached(CACHE_KEYS.STARS);
                const cachedAnomalies = getCached(CACHE_KEYS.ANOMALIES);
                const cachedDatasets = getCached(CACHE_KEYS.DATASETS);
                const cachedStats = getCached(CACHE_KEYS.HARMONIZE_STATS);

                // If we have fresh cached data, use it
                if (cachedStars && cachedStars.fresh) {
                    console.log('✅ Using cached stars data');
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
                    starsResponse = await searchStars({ limit: 5000 });
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
                datasets={datasets}
                onDeleteDataset={handleDeleteDataset}
                isLoading={isLoading}
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
