import React, { useState, useEffect, useRef } from 'react';
import {
    Link2,
    GitMerge,
    Zap,
    Target,
    Loader2,
    CheckCircle,
    AlertTriangle,
    Star,
    Activity,
    RefreshCw,
    Eye,
    Atom
} from 'lucide-react';
import { runCrossMatch, getHarmonizationStats } from '../services/api';
import './Harmonizer.css';

// Animated Network Visualization Component
function FusionNetwork({ groups, stats, onSelectGroup }) {
    const canvasRef = useRef(null);
    const [nodes, setNodes] = useState([]);
    const [selectedNode, setSelectedNode] = useState(null);
    const animationRef = useRef(null);

    // Generate nodes from stats
    useEffect(() => {
        if (!stats) return;

        const generatedNodes = [];
        const colors = {
            'Gaia DR3': '#6B8DD6',
            'SDSS': '#E6B84F',
            'Custom': '#D4683A',
            'Fused': '#4A9F6E'
        };

        // Create fusion group nodes
        const groupCount = stats.unique_fusion_groups || 0;
        const isolated = stats.isolated_stars || 0;
        const fused = stats.stars_in_fusion_groups || 0;

        // Create central hub nodes for fusion groups
        for (let i = 0; i < Math.min(groupCount, 20); i++) {
            const angle = (i / Math.min(groupCount, 20)) * Math.PI * 2;
            const radius = 120 + Math.random() * 40;
            generatedNodes.push({
                id: `fusion-${i}`,
                x: 250 + Math.cos(angle) * radius,
                y: 200 + Math.sin(angle) * radius,
                vx: 0,
                vy: 0,
                radius: 12 + Math.random() * 8,
                color: colors['Fused'],
                type: 'fusion',
                label: `Group ${i + 1}`,
                stars: Math.floor(Math.random() * 5) + 2
            });
        }

        // Add orbiting satellite nodes (source observations)
        generatedNodes.forEach((hub, idx) => {
            if (hub.type === 'fusion') {
                const satellites = hub.stars;
                for (let j = 0; j < satellites; j++) {
                    const sourceType = ['Gaia DR3', 'SDSS', 'Custom'][j % 3];
                    const satAngle = (j / satellites) * Math.PI * 2 + Math.random() * 0.5;
                    const satRadius = 25 + Math.random() * 15;
                    generatedNodes.push({
                        id: `sat-${idx}-${j}`,
                        x: hub.x + Math.cos(satAngle) * satRadius,
                        y: hub.y + Math.sin(satAngle) * satRadius,
                        vx: (Math.random() - 0.5) * 0.5,
                        vy: (Math.random() - 0.5) * 0.5,
                        radius: 4 + Math.random() * 3,
                        color: colors[sourceType] || colors['Custom'],
                        type: 'source',
                        parent: hub.id,
                        label: sourceType
                    });
                }
            }
        });

        // Add some isolated nodes
        for (let i = 0; i < Math.min(isolated, 15); i++) {
            generatedNodes.push({
                id: `isolated-${i}`,
                x: 50 + Math.random() * 400,
                y: 50 + Math.random() * 300,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                radius: 3,
                color: '#666',
                type: 'isolated',
                label: 'Isolated'
            });
        }

        setNodes(generatedNodes);
    }, [stats]);

    // Animation loop
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || nodes.length === 0) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        const animate = () => {
            ctx.clearRect(0, 0, width, height);

            // Draw connections (edges)
            ctx.strokeStyle = 'rgba(212, 104, 58, 0.2)';
            ctx.lineWidth = 1;
            nodes.forEach(node => {
                if (node.parent) {
                    const parent = nodes.find(n => n.id === node.parent);
                    if (parent) {
                        ctx.beginPath();
                        ctx.moveTo(node.x, node.y);
                        ctx.lineTo(parent.x, parent.y);
                        ctx.stroke();
                    }
                }
            });

            // Update and draw nodes
            nodes.forEach(node => {
                // Simple physics
                if (node.type !== 'fusion') {
                    node.x += node.vx;
                    node.y += node.vy;

                    // Bounce off walls
                    if (node.x < node.radius || node.x > width - node.radius) node.vx *= -0.8;
                    if (node.y < node.radius || node.y > height - node.radius) node.vy *= -0.8;

                    // Keep within bounds
                    node.x = Math.max(node.radius, Math.min(width - node.radius, node.x));
                    node.y = Math.max(node.radius, Math.min(height - node.radius, node.y));

                    // Attraction to parent
                    if (node.parent) {
                        const parent = nodes.find(n => n.id === node.parent);
                        if (parent) {
                            const dx = parent.x - node.x;
                            const dy = parent.y - node.y;
                            const dist = Math.sqrt(dx * dx + dy * dy);
                            if (dist > 40) {
                                node.vx += dx * 0.001;
                                node.vy += dy * 0.001;
                            }
                        }
                    }
                }

                // Glow effect
                if (node.type === 'fusion') {
                    const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, node.radius * 2);
                    gradient.addColorStop(0, node.color);
                    gradient.addColorStop(0.5, node.color + '40');
                    gradient.addColorStop(1, 'transparent');
                    ctx.fillStyle = gradient;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, node.radius * 2, 0, Math.PI * 2);
                    ctx.fill();
                }

                // Draw node
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
                ctx.fillStyle = node.color;
                ctx.fill();

                // Highlight selected
                if (selectedNode === node.id) {
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }
            });

            animationRef.current = requestAnimationFrame(animate);
        };

        animate();

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, [nodes, selectedNode]);

    // Handle click
    const handleClick = (e) => {
        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const clicked = nodes.find(node => {
            const dx = node.x - x;
            const dy = node.y - y;
            return Math.sqrt(dx * dx + dy * dy) < node.radius + 5;
        });

        if (clicked) {
            setSelectedNode(clicked.id);
            if (clicked.type === 'fusion' && onSelectGroup) {
                onSelectGroup(clicked);
            }
        }
    };

    return (
        <div className="fusion-network">
            <canvas
                ref={canvasRef}
                width={500}
                height={400}
                onClick={handleClick}
            />
            <div className="network-legend">
                <div className="legend-item">
                    <span className="dot fused"></span> Fusion Group
                </div>
                <div className="legend-item">
                    <span className="dot gaia"></span> Gaia DR3
                </div>
                <div className="legend-item">
                    <span className="dot sdss"></span> SDSS
                </div>
                <div className="legend-item">
                    <span className="dot custom"></span> Custom
                </div>
                <div className="legend-item">
                    <span className="dot isolated"></span> Isolated
                </div>
            </div>
        </div>
    );
}

// Main Harmonizer Component
function Harmonizer() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [stats, setStats] = useState(null);
    const [matchRadius, setMatchRadius] = useState(2.0);
    const [lastRun, setLastRun] = useState(null);
    const [selectedGroup, setSelectedGroup] = useState(null);

    // Load initial stats
    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            const data = await getHarmonizationStats();
            setStats(data);
        } catch (err) {
            console.error('Failed to load stats:', err);
        }
    };

    const handleCrossMatch = async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await runCrossMatch(matchRadius);
            setLastRun(result);
            await loadStats(); // Refresh stats
        } catch (err) {
            setError(err.response?.data?.detail || 'Cross-match failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="harmonizer">
            {/* Header */}
            <div className="harmonizer-header">
                <div className="header-icon">
                    <Atom size={32} className="orbit-icon" />
                </div>
                <h2>Data Fusion Engine</h2>
                <p>Unify observations from multiple catalogs into coherent stellar groups</p>
            </div>

            {/* Error */}
            {error && (
                <div className="error-banner">
                    <AlertTriangle size={18} />
                    <span>{error}</span>
                </div>
            )}

            {/* Main Grid */}
            <div className="harmonizer-grid">
                {/* Left: Controls */}
                <div className="control-panel glass-panel">
                    <h3><Target size={18} /> Cross-Match Configuration</h3>

                    <div className="control-item">
                        <label>Match Radius (arcseconds)</label>
                        <div className="slider-row">
                            <input
                                type="range"
                                min="0.5"
                                max="5.0"
                                step="0.1"
                                value={matchRadius}
                                onChange={(e) => setMatchRadius(parseFloat(e.target.value))}
                            />
                            <span className="value">{matchRadius.toFixed(1)}"</span>
                        </div>
                        <p className="hint">Smaller = stricter matches, Larger = more fusions</p>
                    </div>

                    <button
                        className="fusion-btn"
                        onClick={handleCrossMatch}
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <Loader2 size={20} className="spin" />
                                Fusing Data...
                            </>
                        ) : (
                            <>
                                <GitMerge size={20} />
                                Run Cross-Match
                            </>
                        )}
                    </button>

                    {lastRun && (
                        <div className="last-run-result">
                            <CheckCircle size={16} />
                            <span>
                                Created {lastRun.groups_created} groups from {lastRun.total_stars} stars
                            </span>
                        </div>
                    )}
                </div>

                {/* Center: Network Visualization */}
                <div className="visualization-panel glass-panel">
                    <h3><Link2 size={18} /> Fusion Network</h3>
                    {stats ? (
                        <FusionNetwork
                            stats={stats}
                            onSelectGroup={setSelectedGroup}
                        />
                    ) : (
                        <div className="empty-viz">
                            <Atom size={48} />
                            <p>Run cross-match to visualize fusion groups</p>
                        </div>
                    )}
                </div>

                {/* Right: Stats */}
                <div className="stats-panel glass-panel">
                    <h3><Star size={18} /> Fusion Statistics</h3>

                    <div className="stat-grid">
                        <div className="stat-box">
                            <div className="stat-value">
                                {stats?.total_stars?.toLocaleString() || '—'}
                            </div>
                            <div className="stat-label">Total Stars</div>
                        </div>
                        <div className="stat-box highlight">
                            <div className="stat-value">
                                {stats?.unique_fusion_groups?.toLocaleString() || '—'}
                            </div>
                            <div className="stat-label">Fusion Groups</div>
                        </div>
                        <div className="stat-box">
                            <div className="stat-value">
                                {stats?.stars_in_fusion_groups?.toLocaleString() || '—'}
                            </div>
                            <div className="stat-label">Fused Stars</div>
                        </div>
                        <div className="stat-box">
                            <div className="stat-value">
                                {stats?.isolated_stars?.toLocaleString() || '—'}
                            </div>
                            <div className="stat-label">Isolated</div>
                        </div>
                    </div>

                    {/* Selected Group Inspector */}
                    {selectedGroup && (
                        <div className="group-inspector">
                            <h4><Eye size={16} /> {selectedGroup.label}</h4>
                            <div className="inspector-content">
                                <div className="inspector-row">
                                    <span>Stars in group:</span>
                                    <span className="value">{selectedGroup.stars}</span>
                                </div>
                                <div className="inspector-row">
                                    <span>Position:</span>
                                    <span className="value">
                                        ({selectedGroup.x?.toFixed(0)}, {selectedGroup.y?.toFixed(0)})
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Harmonizer;
