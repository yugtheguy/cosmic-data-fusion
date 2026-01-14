import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Search,
    Filter,
    Database,
    MapPin,
    Globe,
    Save,
    Play,
    RefreshCw,
    ChevronDown,
    ChevronUp,
    List,
    Download,
    Trash2,
    Clock,
    Zap,
    ArrowLeft
} from 'lucide-react';
import ResultsTable from '../components/ResultsTable';
import { searchStars, boxSearch, coneSearch, getHarmonizationStats } from '../services/api';
import toast from 'react-hot-toast';
import './QueryBuilder.css';

function QueryBuilder() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('filters'); // filters, history, saved
    const [queryMode, setQueryMode] = useState('advanced'); // advanced, cone, box
    const [isLoading, setIsLoading] = useState(false);
    const [results, setResults] = useState([]);
    const [totalResults, setTotalResults] = useState(0);
    const [executionTime, setExecutionTime] = useState(0);
    const [databaseStats, setDatabaseStats] = useState({ total_records: 0 });

    // Filter States
    const [filters, setFilters] = useState({
        catalog: ['Gaia DR3'], // Default catalog
        raMin: '',
        raMax: '',
        decMin: '',
        decMax: '',
        raCenter: '',
        decCenter: '',
        radius: 0.5,
        magMin: -26,
        magMax: 20,
        parallaxMin: '',
        parallaxMax: '',
        distanceMin: '',
        distanceMax: '',
        limit: 100
    });

    // Mock Saved Queries
    const [savedQueries, setSavedQueries] = useState([
        { id: 1, name: 'Bright Giants', date: '2026-01-10', count: 124 },
        { id: 2, name: 'Nearby G-Type', date: '2026-01-12', count: 45 },
        { id: 3, name: 'Pleiades Cluster', date: '2026-01-13', count: 890 }
    ]);

    // Fetch database stats on mount
    useEffect(() => {
        const fetchStats = async () => {
            try {
                const stats = await getHarmonizationStats();
                setDatabaseStats(stats);
            } catch (err) {
                console.error('Failed to fetch database stats:', err);
            }
        };
        fetchStats();
    }, []);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFilters(prev => ({ ...prev, [name]: value }));
    };

    const handleCatalogToggle = (catalog) => {
        setFilters(prev => {
            const current = prev.catalog;
            if (current.includes(catalog)) {
                return { ...prev, catalog: current.filter(c => c !== catalog) };
            } else {
                return { ...prev, catalog: [...current, catalog] };
            }
        });
    };

    const executeQuery = async () => {
        setIsLoading(true);
        const startTime = performance.now();
        setResults([]);

        try {
            let data;
            if (queryMode === 'cone') {
                if (!filters.raCenter || !filters.decCenter) {
                    toast.error('Please provide Center RA and Dec for Cone Search');
                    setIsLoading(false);
                    return;
                }
                data = await coneSearch(
                    parseFloat(filters.raCenter),
                    parseFloat(filters.decCenter),
                    parseFloat(filters.radius),
                    parseInt(filters.limit)
                );
            } else if (queryMode === 'box') {
                if (!filters.raMin || !filters.raMax || !filters.decMin || !filters.decMax) {
                    toast.error('Please provide min/max RA and Dec for Box Search');
                    setIsLoading(false);
                    return;
                }
                data = await boxSearch(
                    parseFloat(filters.raMin),
                    parseFloat(filters.raMax),
                    parseFloat(filters.decMin),
                    parseFloat(filters.decMax),
                    parseInt(filters.limit)
                );
            } else {
                // Advanced Search
                const params = {
                    min_mag: filters.magMin === '' ? undefined : parseFloat(filters.magMin),
                    max_mag: filters.magMax === '' ? undefined : parseFloat(filters.magMax),
                    limit: parseInt(filters.limit)
                };

                // Add source filter if selected (currently backend supports single source)
                if (filters.catalog.length > 0) {
                    params.original_source = filters.catalog[0];
                }

                data = await searchStars(params);
            }

            // Transform data based on endpoint response structure
            // /query/search returns { records: [...], total_count: N }
            // /search/box and /search/cone return { stars: [...], count: N }
            if (data && data.records && data.records.length > 0) {
                setResults(data.records);
                setTotalResults(data.total_count || data.records.length);
            } else if (data && data.stars && data.stars.length > 0) {
                setResults(data.stars);
                setTotalResults(data.count || data.stars.length);
            } else if (Array.isArray(data) && data.length > 0) {
                setResults(data);
                setTotalResults(data.length);
            } else {
                setResults([]);
                setTotalResults(0);
            }

        } catch (err) {
            console.error('Query execution failed:', err);
            toast.error('Query execution failed. Check your parameters.');
        } finally {
            const endTime = performance.now();
            setExecutionTime(((endTime - startTime) / 1000).toFixed(2));
            setIsLoading(false);
            if (results.length > 0) {
                toast.success(`Found ${totalResults} objects`);
            }
        }
    };

    return (
        <div className="query-builder-page">
            <div className="query-header">
                <div className="header-content">
                    <button
                        className="back-to-dashboard-btn"
                        onClick={() => navigate('/dashboard')}
                        title="Back to Dashboard"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1>
                            <Database className="header-icon" />
                            Query Builder
                        </h1>
                        <p className="header-subtitle">Advanced multi-parameter cosmic search engine</p>
                    </div>
                </div>
                <div className="header-stats">
                    <div className="stat-item">
                        <span className="stat-label">Database Status</span>
                        <span className="stat-value active">ONLINE</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">Total Records</span>
                        <span className="stat-value">{databaseStats.total_stars?.toLocaleString() || '—'}</span>
                    </div>
                </div>
            </div>

            <div className="query-main-layout">
                {/* Left Panel: Query Controls */}
                <aside className="query-controls-panel">
                    <div className="panel-tabs">
                        <button
                            className={`panel-tab ${activeTab === 'filters' ? 'active' : ''}`}
                            onClick={() => setActiveTab('filters')}
                        >
                            <Filter size={16} /> Filters
                        </button>
                        <button
                            className={`panel-tab ${activeTab === 'saved' ? 'active' : ''}`}
                            onClick={() => setActiveTab('saved')}
                        >
                            <Save size={16} /> Saved
                        </button>
                        <button
                            className={`panel-tab ${activeTab === 'history' ? 'active' : ''}`}
                            onClick={() => setActiveTab('history')}
                        >
                            <Clock size={16} /> History
                        </button>
                    </div>

                    <div className="panel-content">
                        {activeTab === 'filters' && (
                            <div className="filters-container">
                                {/* Query Mode Selector */}
                                <div className="query-mode-selector">
                                    <button
                                        className={`mode-btn ${queryMode === 'advanced' ? 'active' : ''}`}
                                        onClick={() => setQueryMode('advanced')}
                                    >
                                        Advanced
                                    </button>
                                    <button
                                        className={`mode-btn ${queryMode === 'cone' ? 'active' : ''}`}
                                        onClick={() => setQueryMode('cone')}
                                    >
                                        Cone Search
                                    </button>
                                    <button
                                        className={`mode-btn ${queryMode === 'box' ? 'active' : ''}`}
                                        onClick={() => setQueryMode('box')}
                                    >
                                        Box Search
                                    </button>
                                </div>

                                {/* Catalogs Section */}
                                <div className="filter-group">
                                    <h3><Database size={14} /> Source Catalogs</h3>
                                    <div className="catalog-grid">
                                        {['Gaia DR3', 'Tycho-2', '2MASS', 'SDSS'].map(cat => (
                                            <label key={cat} className="checkbox-label">
                                                <input
                                                    type="checkbox"
                                                    checked={filters.catalog.includes(cat)}
                                                    onChange={() => handleCatalogToggle(cat)}
                                                />
                                                <span className="checkbox-custom"></span>
                                                <span style={{ marginLeft: '1rem' }}>{cat}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                {/* Coordinates Section */}
                                {queryMode === 'cone' && (
                                    <div className="filter-group">
                                        <h3><MapPin size={14} /> Cone Search Parameters</h3>
                                        <div className="input-row">
                                            <div className="input-wrapper">
                                                <label>RA Center (°)</label>
                                                <input
                                                    type="number"
                                                    name="raCenter"
                                                    value={filters.raCenter}
                                                    onChange={handleInputChange}
                                                    placeholder="0.00"
                                                />
                                            </div>
                                            <div className="input-wrapper">
                                                <label>Dec Center (°)</label>
                                                <input
                                                    type="number"
                                                    name="decCenter"
                                                    value={filters.decCenter}
                                                    onChange={handleInputChange}
                                                    placeholder="0.00"
                                                />
                                            </div>
                                        </div>
                                        <div className="input-wrapper mt-2">
                                            <label>Radius (deg)</label>
                                            <div className="range-slider-wrapper">
                                                <input
                                                    type="range"
                                                    min="0.1"
                                                    max="10"
                                                    step="0.1"
                                                    value={filters.radius}
                                                    onChange={(e) => setFilters(prev => ({ ...prev, radius: e.target.value }))}
                                                />
                                                <span className="range-value">{filters.radius}°</span>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {queryMode === 'box' && (
                                    <div className="filter-group">
                                        <h3><Globe size={14} /> Box Search Parameters</h3>
                                        <div className="input-grid-2x2">
                                            <div className="input-wrapper">
                                                <label>RA Min</label>
                                                <input type="number" name="raMin" value={filters.raMin} onChange={handleInputChange} />
                                            </div>
                                            <div className="input-wrapper">
                                                <label>RA Max</label>
                                                <input type="number" name="raMax" value={filters.raMax} onChange={handleInputChange} />
                                            </div>
                                            <div className="input-wrapper">
                                                <label>Dec Min</label>
                                                <input type="number" name="decMin" value={filters.decMin} onChange={handleInputChange} />
                                            </div>
                                            <div className="input-wrapper">
                                                <label>Dec Max</label>
                                                <input type="number" name="decMax" value={filters.decMax} onChange={handleInputChange} />
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Photometry Section */}
                                <div className="filter-group">
                                    <h3><Zap size={14} /> Photometry (Magnitude)</h3>
                                    <div className="dual-slider-container">
                                        <div className="input-row">
                                            <div className="input-wrapper">
                                                <label>Min Mag</label>
                                                <input
                                                    type="number"
                                                    name="magMin"
                                                    value={filters.magMin}
                                                    onChange={handleInputChange}
                                                />
                                            </div>
                                            <div className="input-wrapper">
                                                <label>Max Mag</label>
                                                <input
                                                    type="number"
                                                    name="magMax"
                                                    value={filters.magMax}
                                                    onChange={handleInputChange}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Limit Section */}
                                <div className="filter-group">
                                    <h3>Result Limit</h3>
                                    <select
                                        className="limit-select"
                                        value={filters.limit}
                                        onChange={(e) => setFilters(prev => ({ ...prev, limit: parseInt(e.target.value) }))}
                                    >
                                        <option value="100">100 Records</option>
                                        <option value="500">500 Records</option>
                                        <option value="1000">1,000 Records</option>
                                        <option value="5000">5,000 Records</option>
                                    </select>
                                </div>
                            </div>
                        )}

                        {activeTab === 'saved' && (
                            <div className="saved-queries-list">
                                {savedQueries.map(query => (
                                    <div key={query.id} className="saved-query-item">
                                        <div className="query-info">
                                            <h4>{query.name}</h4>
                                            <span>{query.count} stars • {query.date}</span>
                                        </div>
                                        <button className="icon-btn delete-btn">
                                            <Trash2 size={14} />
                                        </button>
                                        <button className="icon-btn load-btn">
                                            Load
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className="panel-footer">
                        <button
                            className="execute-btn"
                            onClick={executeQuery}
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <RefreshCw size={18} className="spin" />
                                    <span>Running...</span>
                                </>
                            ) : (
                                <>
                                    <Play size={18} fill="currentColor" />
                                    <span>Execute Query</span>
                                </>
                            )}
                        </button>
                    </div>
                </aside>

                {/* Right Panel: Results */}
                <main className="query-results-panel">
                    {results.length > 0 ? (
                        <>
                            <div className="results-toolbar">
                                <div className="results-count">
                                    <span className="count-number">{totalResults}</span>
                                    <span className="count-label">Objects Found</span>
                                    {executionTime > 0 && (
                                        <span className="execution-time">({executionTime}s)</span>
                                    )}
                                </div>
                                <div className="results-actions">
                                    <button className="toolbar-btn">
                                        <Save size={16} /> Save Query
                                    </button>
                                    <button className="toolbar-btn primary">
                                        <Download size={16} /> Export
                                    </button>
                                </div>
                            </div>
                            <div className="results-table-wrapper">
                                <ResultsTable data={results} itemsPerPage={filters.limit > 100 ? 50 : 10} />
                            </div>
                        </>
                    ) : (
                        <div className="empty-results-state">
                            <div className="empty-icon-wrapper">
                                <Search size={48} />
                            </div>
                            <h2>Ready to Search</h2>
                            <p>Configure filter parameters on the left and click "Execute Query" to explore the cosmos.</p>
                            <div className="quick-start-chips">
                                <button className="chip">Brightest Stars</button>
                                <button className="chip">Nearby Objects</button>
                                <button className="chip">High Proper Motion</button>
                            </div>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}

export default QueryBuilder;
