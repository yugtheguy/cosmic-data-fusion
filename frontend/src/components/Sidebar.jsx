
import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    Target,
    Clock,
    Search,
    Database,
    UploadCloud,
    Map,
    Brain,
    Link2,
    Download,
    Sparkles,
    BookOpen,
    Filter,
    LogOut,
    RefreshCw,
    User
} from 'lucide-react';
import './Sidebar.css';

// Sidebar Navigation Component
export default function Sidebar({ activeTab, setActiveTab, filters, setFilters, onResetFilters, isLoading, datasets, onDeleteDataset, onLogout }) {
    const navigate = useNavigate();
    const navItems = [
        { id: 'overview', icon: LayoutDashboard, label: 'Overview', link: '/dashboard' },
        { id: 'coordinate-resolver', icon: Target, label: 'Coordinate Finder', link: '/coordinate-resolver' },
        { id: 'timemachine', icon: Clock, label: 'Time Machine', link: '/timemachine' },
        { id: 'query', icon: Search, label: 'Query Builder', link: '/query' },
        { id: 'results', icon: Database, label: 'Data Table', link: '/results' }, // Assuming this route exists or is part of dashboard? Dashboard has it as tab.
        { id: 'upload', icon: UploadCloud, label: 'Ingest Data', link: '/upload' }, // Dashboard tab
        { id: 'skymap', icon: Map, label: 'Sky Map', link: '/skymap' }, // Dashboard tab
        { id: 'anomaly', icon: Brain, label: 'AI Lab', link: '/ai-lab' }, // Dashboard tab but also own component? existing AILab is component.
        { id: 'harmonize', icon: Link2, label: 'Harmonizer', link: '/harmonizer' },
        { id: 'export', icon: Download, label: 'Export', link: '/export' },
        { id: 'planet-hunter', icon: Target, label: 'Planet Hunter', external: true, link: '/planet-hunter' },
        { id: 'ai-assistant', icon: Sparkles, label: 'AI Assistant', link: '/ai-assistant' },
        { id: 'research-methodology', icon: BookOpen, label: 'Research Methods', link: '/research-methodology' },
    ];

    // Note: detailed logic for "activeTab" vs "link" navigation might need adjustment based on how the app routing works. 
    // For now, I'll assume if 'link' is present we navigate, otherwise we use setActiveTab if passed.
    // However, for the pages we are fixing (independent pages), we likely just want navigation.

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
                            } else {
                                setActiveTab && setActiveTab(item.id);
                            }
                        }}
                    >
                        <item.icon size={18} strokeWidth={1.5} />
                        <span>{item.label}</span>
                    </button>
                ))}
            </nav>

            {/* Filters Section - Only show if props are provided */}
            {filters && setFilters && (
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
            )}

            {/* User Section */}
            <div className="sidebar-user">
                <div className="user-avatar">
                    <User size={16} strokeWidth={1.5} />
                </div>
                <div className="user-info">
                    <span className="user-name">Researcher</span>
                    <span className="user-role">Astronomer</span>
                </div>
                <button className="logout-btn" title="Logout" onClick={onLogout}>
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
                    value={filters.ra_min || 0}
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
                    value={filters.ra_max || 360}
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
                    value={filters.dec_min || -90}
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
                    value={filters.dec_max || 90}
                    onChange={(e) => setFilters({ ...filters, dec_max: Number(e.target.value) })}
                    className="range-slider"
                />
            </div>
            <div className="filter-group">
                <label>Mag Max (Brightness)</label>
                <div className="range-display">
                    <span>{filters.max_mag}</span>
                </div>
                <input
                    type="range"
                    min="-30"
                    max="25"
                    step="0.5"
                    value={filters.max_mag || 15}
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
