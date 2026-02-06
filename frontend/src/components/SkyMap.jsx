import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { useNavigate } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';

// Sky Map Component - Enhanced Version
const SkyMap = ({ stars, anomalies, isLoading }) => {
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
        const passes = mag >= magRange[0] && mag <= magRange[1] && visibleCatalogs[catalog];
        return passes;
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
};

export default SkyMap;
