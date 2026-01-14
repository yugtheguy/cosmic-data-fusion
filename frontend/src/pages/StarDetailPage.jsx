import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Plot from 'react-plotly.js';
import {
    ArrowLeft,
    Star,
    MapPin,
    Compass,
    Sun,
    Move,
    Database,
    Clock,
    ExternalLink,
    RefreshCw,
    AlertTriangle,
    Copy,
    Check,
    Eye,
    Zap,
    AlertCircle,
    TrendingUp,
    TrendingDown,
    Activity,
    Download,
    ChevronDown,
    FileJson,
    FileText,
    Clipboard
} from 'lucide-react';
import { getStarById, getNearbyStars, checkStarAnomaly, refreshStarFromGaia } from '../services/api';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import Star3D from '../components/Star3D';
import toast from 'react-hot-toast';
import './StarDetailPage.css';

// Stat Card Component
function StatCard({ icon: Icon, label, value, unit, highlight = false }) {
    return (
        <div className={`detail-stat-card ${highlight ? 'highlight' : ''}`}>
            <div className="stat-icon-wrapper">
                <Icon size={18} strokeWidth={1.5} />
            </div>
            <div className="stat-info">
                <span className="stat-label">{label}</span>
                <span className="stat-value">
                    {value !== null && value !== undefined ? value : '—'}
                    {unit && <span className="stat-unit">{unit}</span>}
                </span>
            </div>
        </div>
    );
}

// Coordinate Display with Copy
function CoordinateDisplay({ label, value, precision = 6, symbol }) {
    const [copied, setCopied] = useState(false);
    const formattedValue = value?.toFixed(precision) || '—';

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(formattedValue);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    return (
        <div className="coord-display">
            <div className="coord-header">
                <span className="coord-symbol">{symbol}</span>
                <span className="coord-label">{label}</span>
            </div>
            <div className="coord-value-wrapper">
                <span className="coord-value">{formattedValue}</span>
                <span className="coord-unit">°</span>
                <button className="copy-btn" onClick={handleCopy} title="Copy to clipboard">
                    {copied ? <Check size={16} /> : <Copy size={16} />}
                </button>
            </div>
        </div>
    );
}

// Nearby Stars Mini Map
function NearbyStarsMap({ star, nearbyStars, isLoading }) {
    if (isLoading) {
        return (
            <div className="nearby-map-loading">
                <RefreshCw size={24} className="spin" />
                <span>Loading nearby stars...</span>
            </div>
        );
    }

    const plotData = [
        // Target star (center)
        {
            type: 'scatter',
            mode: 'markers',
            name: 'This Star',
            x: [star?.ra_deg || 0],
            y: [star?.dec_deg || 0],
            marker: {
                size: 16,
                color: '#d4683a',
                symbol: 'star',
                line: { width: 2, color: '#e8a87c' }
            },
            hoverinfo: 'text',
            text: [`${star?.source_id}<br>RA: ${star?.ra_deg?.toFixed(4)}°<br>Dec: ${star?.dec_deg?.toFixed(4)}°`]
        },
        // Nearby stars
        {
            type: 'scatter',
            mode: 'markers',
            name: 'Nearby Stars',
            x: nearbyStars.map(s => s.ra_deg),
            y: nearbyStars.map(s => s.dec_deg),
            marker: {
                size: nearbyStars.map(s => Math.max(4, 12 - (s.brightness_mag || 10))),
                color: '#e8a87c',
                opacity: 0.7
            },
            hoverinfo: 'text',
            text: nearbyStars.map(s => `${s.source_id}<br>RA: ${s.ra_deg?.toFixed(4)}°<br>Dec: ${s.dec_deg?.toFixed(4)}°<br>Mag: ${s.brightness_mag?.toFixed(2)}`)
        }
    ];

    const layout = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#888888', family: 'Inter, sans-serif' },
        margin: { t: 30, r: 20, b: 40, l: 50 },
        xaxis: {
            title: { text: 'RA (°)', font: { size: 11 } },
            gridcolor: 'rgba(42, 42, 42, 0.5)',
            zerolinecolor: 'rgba(42, 42, 42, 0.5)',
            tickfont: { size: 9 },
        },
        yaxis: {
            title: { text: 'Dec (°)', font: { size: 11 } },
            gridcolor: 'rgba(42, 42, 42, 0.5)',
            zerolinecolor: 'rgba(42, 42, 42, 0.5)',
            tickfont: { size: 9 },
        },
        showlegend: true,
        legend: {
            x: 0,
            y: 1,
            xanchor: 'left',
            bgcolor: 'rgba(26, 26, 26, 0.8)',
            bordercolor: '#2a2a2a',
            borderwidth: 1,
            font: { size: 10 }
        },
        dragmode: 'pan'
    };

    const config = {
        displayModeBar: false,
        responsive: true
    };

    return (
        <div className="nearby-map">
            <Plot
                data={plotData}
                layout={layout}
                config={config}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
            />
        </div>
    );
}

// Nearby Stars List
function NearbyStarsList({ nearbyStars, isLoading }) {
    const navigate = useNavigate();

    if (isLoading) {
        return <div className="nearby-list-loading">Loading...</div>;
    }

    if (!nearbyStars.length) {
        return (
            <div className="nearby-list-empty">
                <Eye size={24} />
                <span>No nearby stars found within search radius</span>
            </div>
        );
    }

    return (
        <div className="nearby-list">
            {nearbyStars.slice(0, 10).map((star, index) => (
                <div
                    key={star.id}
                    className="nearby-star-item"
                    onClick={() => navigate(`/star/${star.id}`)}
                    style={{ animationDelay: `${index * 0.05}s` }}
                >
                    <div className="nearby-star-indicator">
                        <Star size={12} fill="currentColor" />
                    </div>
                    <div className="nearby-star-info">
                        <span className="nearby-star-id">{star.source_id}</span>
                        <span className="nearby-star-coords">
                            RA: {star.ra_deg?.toFixed(2)}° | Dec: {star.dec_deg?.toFixed(2)}°
                        </span>
                    </div>
                    <div className="nearby-star-mag">
                        Mag: {star.brightness_mag?.toFixed(2)}
                    </div>
                </div>
            ))}
        </div>
    );
}

// Anomaly Section Component
function AnomalySection({ anomalyInfo, isLoading }) {
    if (isLoading) {
        return (
            <section className="anomaly-section">
                <h2 className="section-title">
                    <Activity size={18} />
                    AI Analysis
                </h2>
                <div className="anomaly-loading">
                    <RefreshCw size={20} className="spin" />
                    <span>Analyzing star properties...</span>
                </div>
            </section>
        );
    }

    if (!anomalyInfo) {
        return null;
    }

    const getDeviationIcon = (level) => {
        switch (level) {
            case 'extreme': return <AlertTriangle size={14} className="deviation-extreme" />;
            case 'high': return <TrendingUp size={14} className="deviation-high" />;
            case 'moderate': return <TrendingDown size={14} className="deviation-moderate" />;
            default: return <Activity size={14} className="deviation-normal" />;
        }
    };

    const featureLabels = {
        ra_deg: 'Right Ascension',
        dec_deg: 'Declination',
        brightness_mag: 'Brightness',
        parallax_mas: 'Parallax'
    };

    return (
        <section className="anomaly-section">
            <h2 className="section-title">
                <Activity size={18} />
                AI Anomaly Analysis
                {anomalyInfo.is_anomaly && (
                    <span className="anomaly-badge">⚠️ ANOMALY DETECTED</span>
                )}
            </h2>

            <div className="anomaly-container">
                {/* Status Card */}
                <div className={`anomaly-status-card ${anomalyInfo.is_anomaly ? 'is-anomaly' : 'is-normal'}`}>
                    <div className="status-header">
                        {anomalyInfo.is_anomaly ? (
                            <AlertCircle size={24} className="status-icon anomaly" />
                        ) : (
                            <Check size={24} className="status-icon normal" />
                        )}
                        <h3>{anomalyInfo.is_anomaly ? 'Anomalous Star' : 'Normal Star'}</h3>
                    </div>

                    {anomalyInfo.is_anomaly && (
                        <div className="anomaly-score-display">
                            <div className="score-item">
                                <span className="score-label">Anomaly Score</span>
                                <span className="score-value">{anomalyInfo.anomaly_score?.toFixed(4)}</span>
                            </div>
                            <div className="score-item">
                                <span className="score-label">Rank</span>
                                <span className="score-value">#{anomalyInfo.anomaly_rank} of {anomalyInfo.total_anomalies}</span>
                            </div>
                        </div>
                    )}

                    <p className="anomaly-explanation">{anomalyInfo.explanation}</p>
                </div>

                {/* Feature Deviations */}
                <div className="feature-deviations-card">
                    <h3>Feature Analysis</h3>
                    <div className="deviations-grid">
                        {Object.entries(anomalyInfo.feature_deviations || {}).map(([key, data]) => (
                            <div key={key} className={`deviation-item ${data.deviation_level}`}>
                                <div className="deviation-header">
                                    {getDeviationIcon(data.deviation_level)}
                                    <span className="deviation-name">{featureLabels[key] || key}</span>
                                    <span className={`deviation-badge ${data.deviation_level}`}>
                                        {data.deviation_level}
                                    </span>
                                </div>
                                <div className="deviation-details">
                                    <div className="deviation-stat">
                                        <span>Value:</span>
                                        <strong>{data.value}</strong>
                                    </div>
                                    <div className="deviation-stat">
                                        <span>Catalog Mean:</span>
                                        <strong>{data.catalog_mean}</strong>
                                    </div>
                                    <div className="deviation-stat">
                                        <span>Z-Score:</span>
                                        <strong className={Math.abs(data.z_score) > 2 ? 'highlight' : ''}>
                                            {data.z_score > 0 ? '+' : ''}{data.z_score}σ
                                        </strong>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Recommendations */}
                <div className="recommendations-card">
                    <h3>Recommendations</h3>
                    <ul className="recommendations-list">
                        {anomalyInfo.recommendations?.map((rec, index) => (
                            <li key={index}>{rec}</li>
                        ))}
                    </ul>
                </div>
            </div>
        </section>
    );
}

// Main Star Detail Page Component
function StarDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [star, setStar] = useState(null);
    const [nearbyStars, setNearbyStars] = useState([]);
    const [anomalyInfo, setAnomalyInfo] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isLoadingNearby, setIsLoadingNearby] = useState(true);
    const [isLoadingAnomaly, setIsLoadingAnomaly] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [showExportMenu, setShowExportMenu] = useState(false);
    const [error, setError] = useState(null);

    // Export star data
    const handleExport = async (format) => {
        setShowExportMenu(false);

        if (!star) return;

        const starData = {
            source_id: star.source_id,
            ra_deg: star.ra_deg,
            dec_deg: star.dec_deg,
            brightness_mag: star.brightness_mag,
            parallax_mas: star.parallax_mas,
            distance_pc: star.distance_pc,
            original_source: star.original_source,
            exported_at: new Date().toISOString()
        };

        if (format === 'json') {
            const blob = new Blob([JSON.stringify(starData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `star_${star.source_id || star.id}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        } else if (format === 'csv') {
            const headers = Object.keys(starData).join(',');
            const values = Object.values(starData).join(',');
            const csv = `${headers}\n${values}`;
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `star_${star.source_id || star.id}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        } else if (format === 'clipboard') {
            try {
                await navigator.clipboard.writeText(JSON.stringify(starData, null, 2));
                toast.success('Star data copied to clipboard!');
            } catch (err) {
                toast.error('Failed to copy to clipboard');
                console.error('Failed to copy:', err);
            }
        }
    };

    // Open in SIMBAD
    const handleOpenSimbad = () => {
        setShowExportMenu(false);
        if (star?.ra_deg && star?.dec_deg) {
            const simbadUrl = `https://simbad.u-strasbg.fr/simbad/sim-coo?Coord=${star.ra_deg}+${star.dec_deg}&CooFrame=ICRS&CooEpoch=2000&CooEqui=2000&Radius=2&Radius.unit=arcsec&submit=submit+query`;
            window.open(simbadUrl, '_blank');
        }
    };

    const handleGaiaRefresh = async () => {
        setIsRefreshing(true);
        try {
            const updatedStar = await refreshStarFromGaia(id);
            setStar(updatedStar);
            toast.success('Star data refreshed from Gaia Archive');
            // Optionally refresh anomaly check with new data
            checkStarAnomaly(id).then(setAnomalyInfo).catch(console.warn);
        } catch (err) {
            toast.error('Failed to fetch data from ESA Gaia Archive');
            console.error(err);
        } finally {
            setIsRefreshing(false);
        }
    };

    useEffect(() => {
        const fetchStarData = async () => {
            setIsLoading(true);
            setError(null);

            try {
                // Fetch star details
                const starData = await getStarById(id);
                setStar(starData);

                // Fetch nearby stars
                setIsLoadingNearby(true);
                try {
                    const nearbyData = await getNearbyStars(id, 0.5, 20);
                    setNearbyStars(nearbyData.stars || []);
                } catch (nearbyErr) {
                    console.warn('Failed to fetch nearby stars:', nearbyErr);
                    setNearbyStars([]);
                }
                setIsLoadingNearby(false);

                // Fetch anomaly information
                setIsLoadingAnomaly(true);
                try {
                    const anomalyData = await checkStarAnomaly(id);
                    setAnomalyInfo(anomalyData);
                } catch (anomalyErr) {
                    console.warn('Failed to fetch anomaly info:', anomalyErr);
                    setAnomalyInfo(null);
                }
                setIsLoadingAnomaly(false);

            } catch (err) {
                console.error('Failed to fetch star:', err);
                setError(err.response?.status === 404
                    ? 'Star not found. It may have been removed from the catalog.'
                    : 'Failed to load star data. Please try again.'
                );
            } finally {
                setIsLoading(false);
            }
        };

        if (id) {
            fetchStarData();
        }
    }, [id]);

    if (isLoading) {
        return (
            <div className="star-detail-page">
                <div className="star-detail-loading">
                    <div className="loading-spinner">
                        <Zap size={48} className="sparkle-spin" />
                    </div>
                    <span>Loading star data...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="star-detail-page">
                <div className="star-detail-error">
                    <AlertTriangle size={48} />
                    <h2>Oops!</h2>
                    <p>{error}</p>
                    <button onClick={() => navigate(-1)}>
                        <ArrowLeft size={16} />
                        Back to Previous Page
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="star-detail-page">
            {/* Background Effects */}
            <div className="star-bg-particles"></div>
            <div className="star-bg-gradient"></div>

            {/* Header */}
            <header className="star-detail-header">
                <button className="back-button" onClick={() => navigate(-1)}>
                    <ArrowLeft size={18} />
                    <span>Back</span>
                </button>

                <div className="header-center">
                    <div className="header-icon-wrapper">
                        <Star size={28} fill="currentColor" />
                        <div className="icon-ring"></div>
                    </div>
                    <div className="header-title-block">
                        <div className="title-row">
                            <h1>{star?.source_id}</h1>
                        </div>
                        <div className="subtitle-row">
                            <span className="source-badge">{star?.original_source}</span>
                            <span className="divider">•</span>
                            <span className="catalog-info">Stellar Object</span>
                        </div>
                    </div>
                </div>

                <div className="header-actions">
                    <button
                        className="action-btn refresh-btn"
                        onClick={handleGaiaRefresh}
                        disabled={isRefreshing}
                        title="Refresh from Gaia Archive"
                    >
                        <RefreshCw size={16} className={isRefreshing ? 'spin' : ''} />
                    </button>

                    {/* Export Dropdown */}
                    <div className="export-dropdown-container">
                        <button
                            className="action-btn export-trigger"
                            onClick={() => setShowExportMenu(!showExportMenu)}
                            title="Export star data"
                        >
                            <Download size={16} />
                            <ChevronDown size={12} />
                        </button>

                        {showExportMenu && (
                            <div className="export-dropdown-menu">
                                <div className="export-menu-header">Export Star Data</div>
                                <button onClick={() => handleExport('json')}>
                                    <FileJson size={14} />
                                    <span>Download JSON</span>
                                </button>
                                <button onClick={() => handleExport('csv')}>
                                    <FileText size={14} />
                                    <span>Download CSV</span>
                                </button>
                                <button onClick={() => handleExport('clipboard')}>
                                    <Clipboard size={14} />
                                    <span>Copy to Clipboard</span>
                                </button>
                                <div className="export-menu-divider"></div>
                                <button onClick={() => handleOpenSimbad()}>
                                    <ExternalLink size={14} />
                                    <span>View on SIMBAD</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="star-detail-content">
                {/* Hero Section with Coordinates */}
                <section className="hero-section">
                    <div className="hero-card coordinates-card">
                        <div className="card-header">
                            <Compass size={20} />
                            <h2>Celestial Coordinates</h2>
                            <span className="frame-badge">ICRS J2000</span>
                        </div>
                        <div className="coordinates-grid">
                            <CoordinateDisplay
                                label="Right Ascension"
                                value={star?.ra_deg}
                                precision={6}
                                symbol="α"
                            />
                            <div className="coord-divider"></div>
                            <CoordinateDisplay
                                label="Declination"
                                value={star?.dec_deg}
                                precision={6}
                                symbol="δ"
                            />
                        </div>
                    </div>

                    <div className="hero-card visual-card">
                        <div className="star-visual-container">
                            <Canvas camera={{ position: [0, 0, 8], fov: 45 }}>
                                <ambientLight intensity={0.5} />
                                <Star3D
                                    color={star?.brightness_mag < 0 ? '#add8e6' : // Very bright (Blue-ish)
                                        star?.brightness_mag < 5 ? '#fffacd' : // Bright (LemonChiffon/White)
                                            star?.brightness_mag < 10 ? '#ffae00' : // Medium (Bright Orange/Gold)
                                                '#ff6600'} // Dimmer (Vivid Orange instead of Red)
                                />
                                <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.5} />
                            </Canvas>
                        </div>
                        <div className="magnitude-display">
                            <span className="mag-label">Apparent Magnitude</span>
                            <span className="mag-value">{star?.brightness_mag?.toFixed(2) || '—'}</span>
                        </div>
                    </div>
                </section>

                {/* Properties Grid */}
                <section className="properties-section">
                    <h2 className="section-title">
                        <Database size={18} />
                        Star Properties
                    </h2>
                    <div className="properties-grid">
                        <StatCard
                            icon={Sun}
                            label="Brightness"
                            value={star?.brightness_mag?.toFixed(2)}
                            unit="mag"
                            highlight={true}
                        />
                        <StatCard
                            icon={Move}
                            label="Parallax"
                            value={star?.parallax_mas?.toFixed(4)}
                            unit="mas"
                        />
                        <StatCard
                            icon={MapPin}
                            label="Distance"
                            value={star?.distance_pc?.toFixed(2)}
                            unit="pc"
                        />
                        <StatCard
                            icon={Database}
                            label="Source"
                            value={star?.original_source}
                        />
                        <StatCard
                            icon={Clock}
                            label="Database ID"
                            value={star?.id}
                        />
                        <StatCard
                            icon={Eye}
                            label="Frame"
                            value={star?.raw_frame || 'ICRS'}
                        />
                    </div>
                </section>

                {/* AI Anomaly Analysis Section */}
                <AnomalySection
                    anomalyInfo={anomalyInfo}
                    isLoading={isLoadingAnomaly}
                />

                {/* Nearby Stars Section */}
                <section className="nearby-section">
                    <h2 className="section-title">
                        <Zap size={18} />
                        Nearby Stars
                        <span className="nearby-count">{nearbyStars.length} found within 0.5°</span>
                    </h2>
                    <div className="nearby-container">
                        <div className="nearby-map-wrapper">
                            <NearbyStarsMap
                                star={star}
                                nearbyStars={nearbyStars}
                                isLoading={isLoadingNearby}
                            />
                        </div>
                        <div className="nearby-list-wrapper">
                            <h3>Neighboring Objects</h3>
                            <NearbyStarsList
                                nearbyStars={nearbyStars}
                                isLoading={isLoadingNearby}
                            />
                        </div>
                    </div>
                </section>

                {/* Metadata Section */}
                {star?.raw_metadata && Object.keys(star.raw_metadata).length > 0 && (
                    <section className="metadata-section">
                        <h2 className="section-title">
                            <Database size={18} />
                            Raw Metadata
                        </h2>
                        <div className="metadata-grid">
                            {Object.entries(star.raw_metadata)
                                .filter(([key]) => !['data_source', 'confidence'].includes(key.toLowerCase()))
                                .map(([key, value]) => (
                                    <div key={key} className="metadata-item">
                                        <span className="metadata-key">{key}</span>
                                        <span className="metadata-value">
                                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                        </span>
                                    </div>
                                ))}
                        </div>
                    </section>
                )}
            </main>
        </div>
    );
}

export default StarDetailPage;
