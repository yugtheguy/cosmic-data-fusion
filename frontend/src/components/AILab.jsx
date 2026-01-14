import React, { useState, useEffect } from 'react';
import {
    Brain,
    Sparkles,
    Target,
    TrendingUp,
    RefreshCw,
    AlertTriangle,
    CheckCircle,
    Loader2,
    Zap
} from 'lucide-react';
import Plot from 'react-plotly.js';
import { detectAnomalies, findClusters } from '../services/api';
import './AILab.css';

function AILab() {
    // State
    const [activeTab, setActiveTab] = useState('clusters'); // clusters, anomalies, insights
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Clustering state
    const [clusterParams, setClusterParams] = useState({ eps: 0.5, minSamples: 10 });
    const [clusterResult, setClusterResult] = useState(null);

    // Anomaly state
    const [contamination, setContamination] = useState(0.05);
    const [anomalyResult, setAnomalyResult] = useState(null);

    // Run clustering
    const runClustering = async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await findClusters(clusterParams.eps, clusterParams.minSamples);
            setClusterResult(result);
        } catch (err) {
            setError(err.response?.data?.detail || 'Clustering failed');
        } finally {
            setLoading(false);
        }
    };

    // Run anomaly detection
    const runAnomalyDetection = async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await detectAnomalies(contamination);
            setAnomalyResult(result);
        } catch (err) {
            setError(err.response?.data?.detail || 'Anomaly detection failed');
        } finally {
            setLoading(false);
        }
    };

    // Generate cluster plot data
    const getClusterPlotData = () => {
        if (!clusterResult?.clusters) return [];

        const colors = [
            '#D4683A', '#4A9F6E', '#6B8DD6', '#E6B84F', '#9B6B9E',
            '#5DADE2', '#F1948A', '#82E0AA', '#FAD7A0', '#D7BDE2'
        ];

        const traces = [];
        const clusterIds = Object.keys(clusterResult.clusters);

        clusterIds.forEach((clusterId, idx) => {
            const stats = clusterResult.cluster_stats?.[clusterId];
            if (stats) {
                traces.push({
                    type: 'scatter',
                    mode: 'markers',
                    name: clusterId === '-1' ? 'Noise' : `Cluster ${clusterId}`,
                    x: [stats.mean_ra],
                    y: [stats.mean_dec],
                    marker: {
                        size: Math.min(stats.count / 2, 30) + 10,
                        color: clusterId === '-1' ? '#666' : colors[idx % colors.length],
                        opacity: clusterId === '-1' ? 0.3 : 0.8,
                        line: { width: 1, color: '#fff' }
                    },
                    text: `${stats.count} stars`,
                    hovertemplate: `<b>${clusterId === '-1' ? 'Noise' : 'Cluster ' + clusterId}</b><br>` +
                        `Stars: ${stats.count}<br>` +
                        `RA: ${stats.mean_ra?.toFixed(2)}°<br>` +
                        `Dec: ${stats.mean_dec?.toFixed(2)}°<extra></extra>`
                });
            }
        });

        return traces;
    };

    // Generate anomaly plot data
    const getAnomalyPlotData = () => {
        if (!anomalyResult?.anomalies) return [];

        return [{
            type: 'scatter',
            mode: 'markers',
            x: anomalyResult.anomalies.map(a => a.ra_deg),
            y: anomalyResult.anomalies.map(a => a.dec_deg),
            marker: {
                size: anomalyResult.anomalies.map(a => Math.abs(a.anomaly_score) * 20 + 8),
                color: anomalyResult.anomalies.map(a => a.anomaly_score),
                colorscale: 'RdYlGn',
                reversescale: true,
                showscale: true,
                colorbar: { title: 'Anomaly Score', tickformat: '.2f' }
            },
            text: anomalyResult.anomalies.map(a => a.source_id),
            hovertemplate: '<b>%{text}</b><br>RA: %{x:.2f}°<br>Dec: %{y:.2f}°<br>Score: %{marker.color:.3f}<extra></extra>'
        }];
    };

    const plotLayout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(26,26,26,0.8)',
        font: { color: '#e0e0e0', family: 'Inter' },
        margin: { t: 40, r: 20, b: 50, l: 60 },
        xaxis: {
            title: 'Right Ascension (°)',
            gridcolor: 'rgba(255,255,255,0.1)',
            zerolinecolor: 'rgba(255,255,255,0.2)'
        },
        yaxis: {
            title: 'Declination (°)',
            gridcolor: 'rgba(255,255,255,0.1)',
            zerolinecolor: 'rgba(255,255,255,0.2)'
        },
        showlegend: true,
        legend: { orientation: 'h', y: -0.15 }
    };

    return (
        <div className="ai-lab">
            <div className="ai-lab-header">
                <div className="header-title">
                    <Brain size={28} className="brain-icon" />
                    <h2>AI Discovery Lab</h2>
                </div>
                <p>Unlock hidden patterns in your stellar data using machine learning</p>
            </div>

            {/* Tab Navigation */}
            <div className="ai-tabs">
                <button
                    className={`ai-tab ${activeTab === 'clusters' ? 'active' : ''}`}
                    onClick={() => setActiveTab('clusters')}
                >
                    <Target size={18} />
                    Cluster Analysis
                </button>
                <button
                    className={`ai-tab ${activeTab === 'anomalies' ? 'active' : ''}`}
                    onClick={() => setActiveTab('anomalies')}
                >
                    <Sparkles size={18} />
                    Anomaly Detection
                </button>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="error-banner">
                    <AlertTriangle size={18} />
                    <span>{error}</span>
                </div>
            )}

            {/* Cluster Analysis Tab */}
            {activeTab === 'clusters' && (
                <div className="ai-panel">
                    <div className="controls-row">
                        <div className="control-group">
                            <label>Epsilon (Distance)</label>
                            <input
                                type="range"
                                min="0.1"
                                max="2.0"
                                step="0.1"
                                value={clusterParams.eps}
                                onChange={(e) => setClusterParams(p => ({ ...p, eps: parseFloat(e.target.value) }))}
                            />
                            <span className="value-display">{clusterParams.eps.toFixed(1)}</span>
                        </div>
                        <div className="control-group">
                            <label>Min Samples</label>
                            <input
                                type="range"
                                min="3"
                                max="50"
                                step="1"
                                value={clusterParams.minSamples}
                                onChange={(e) => setClusterParams(p => ({ ...p, minSamples: parseInt(e.target.value) }))}
                            />
                            <span className="value-display">{clusterParams.minSamples}</span>
                        </div>
                        <button className="run-btn" onClick={runClustering} disabled={loading}>
                            {loading ? <Loader2 size={18} className="spin" /> : <Zap size={18} />}
                            {loading ? 'Running...' : 'Run DBSCAN'}
                        </button>
                    </div>

                    {clusterResult && (
                        <>
                            <div className="result-stats">
                                <div className="stat-card">
                                    <span className="stat-value">{clusterResult.n_clusters}</span>
                                    <span className="stat-label">Clusters Found</span>
                                </div>
                                <div className="stat-card">
                                    <span className="stat-value">{clusterResult.total_stars - clusterResult.n_noise}</span>
                                    <span className="stat-label">Grouped Stars</span>
                                </div>
                                <div className="stat-card">
                                    <span className="stat-value">{clusterResult.n_noise}</span>
                                    <span className="stat-label">Noise Points</span>
                                </div>
                            </div>

                            <div className="plot-container">
                                <Plot
                                    data={getClusterPlotData()}
                                    layout={{ ...plotLayout, title: 'Star Clusters (DBSCAN)' }}
                                    config={{ responsive: true, displayModeBar: false }}
                                    style={{ width: '100%', height: '400px' }}
                                />
                            </div>
                        </>
                    )}

                    {!clusterResult && !loading && (
                        <div className="empty-state">
                            <Target size={48} />
                            <h3>No Clusters Yet</h3>
                            <p>Adjust parameters and click "Run DBSCAN" to find star clusters</p>
                        </div>
                    )}
                </div>
            )}

            {/* Anomaly Detection Tab */}
            {activeTab === 'anomalies' && (
                <div className="ai-panel">
                    <div className="controls-row">
                        <div className="control-group wide">
                            <label>Contamination (Expected Anomaly %)</label>
                            <input
                                type="range"
                                min="0.01"
                                max="0.20"
                                step="0.01"
                                value={contamination}
                                onChange={(e) => setContamination(parseFloat(e.target.value))}
                            />
                            <span className="value-display">{(contamination * 100).toFixed(0)}%</span>
                        </div>
                        <button className="run-btn" onClick={runAnomalyDetection} disabled={loading}>
                            {loading ? <Loader2 size={18} className="spin" /> : <Sparkles size={18} />}
                            {loading ? 'Detecting...' : 'Detect Anomalies'}
                        </button>
                    </div>

                    {anomalyResult && (
                        <>
                            <div className="result-stats">
                                <div className="stat-card">
                                    <span className="stat-value">{anomalyResult.total_stars_analyzed}</span>
                                    <span className="stat-label">Stars Analyzed</span>
                                </div>
                                <div className="stat-card highlight">
                                    <span className="stat-value">{anomalyResult.anomaly_count}</span>
                                    <span className="stat-label">Anomalies Found</span>
                                </div>
                                <div className="stat-card">
                                    <span className="stat-value">{(anomalyResult.contamination_used * 100).toFixed(1)}%</span>
                                    <span className="stat-label">Contamination</span>
                                </div>
                            </div>

                            <div className="plot-container">
                                <Plot
                                    data={getAnomalyPlotData()}
                                    layout={{ ...plotLayout, title: 'Anomalous Stars (Isolation Forest)' }}
                                    config={{ responsive: true, displayModeBar: false }}
                                    style={{ width: '100%', height: '400px' }}
                                />
                            </div>

                            {/* Top Anomalies List */}
                            <div className="anomaly-list">
                                <h4>Top Anomalies</h4>
                                <div className="anomaly-items">
                                    {anomalyResult.anomalies.slice(0, 5).map((a, i) => (
                                        <div key={i} className="anomaly-item">
                                            <div className="anomaly-rank">#{i + 1}</div>
                                            <div className="anomaly-info">
                                                <span className="anomaly-id">{a.source_id}</span>
                                                <span className="anomaly-coords">RA: {a.ra_deg?.toFixed(2)}° | Dec: {a.dec_deg?.toFixed(2)}°</span>
                                            </div>
                                            <div className="anomaly-score">
                                                Score: {Math.abs(a.anomaly_score).toFixed(3)}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </>
                    )}

                    {!anomalyResult && !loading && (
                        <div className="empty-state">
                            <Sparkles size={48} />
                            <h3>No Anomalies Yet</h3>
                            <p>Adjust contamination and click "Detect Anomalies" to find unusual stars</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default AILab;
