import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
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
import { runCrossMatch, getHarmonizationStats, getFusionGroups, getFusionGroup } from '../services/api';
import './Harmonizer.css';

// Animated Network Visualization Component
function FusionNetwork({ groups, onSelectGroup }) {
    const canvasRef = useRef(null);
    const [nodes, setNodes] = useState([]);
    const [selectedNode, setSelectedNode] = useState(null);
    const animationRef = useRef(null);

    // Generate nodes from real groups
    useEffect(() => {
        if (!groups || groups.length === 0) return;

        const generatedNodes = [];
        const colors = {
            'Gaia DR3': '#6B8DD6',
            'SDSS': '#E6B84F',
            'Custom': '#D4683A',
            'Fused': '#4A9F6E'
        };

        // Create central hub nodes for fusion groups
        groups.forEach((group, i) => {
            // Position hubs in a circle or random
            const angle = (i / Math.min(groups.length, 50)) * Math.PI * 2;
            const radius = 120 + Math.random() * 60;

            generatedNodes.push({
                id: group.id, // Real UUID
                x: 250 + Math.cos(angle) * (radius * (0.8 + Math.random() * 0.4)),
                y: 200 + Math.sin(angle) * (radius * (0.8 + Math.random() * 0.4)),
                vx: 0,
                vy: 0,
                radius: 8 + Math.min(group.star_count * 2, 8),
                color: colors['Fused'],
                type: 'fusion',
                label: group.label,
                starCount: group.star_count,
                data: group
            });

            // Add satellites for member stars (visual only)
            const satellites = Math.min(group.star_count, 5); // Cap for viz
            for (let j = 0; j < satellites; j++) {
                const satAngle = (j / satellites) * Math.PI * 2 + Math.random() * 0.5;
                const satRadius = 15 + Math.random() * 10;
                generatedNodes.push({
                    id: `${group.id}-sat-${j}`,
                    x: 250 + Math.cos(angle) * radius + Math.cos(satAngle) * satRadius,
                    y: 200 + Math.sin(angle) * radius + Math.sin(satAngle) * satRadius,
                    vx: (Math.random() - 0.5) * 0.5,
                    vy: (Math.random() - 0.5) * 0.5,
                    radius: 3 + Math.random() * 2,
                    color: colors['Gaia DR3'], // Simplification
                    type: 'source',
                    parent: group.id
                });
            }
        });

        setNodes(generatedNodes);
    }, [groups]);

    // Animation loop (simplified for brevity, keeps existing physics)
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || nodes.length === 0) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        const animate = () => {
            ctx.clearRect(0, 0, width, height);

            // Draw connections
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
                if (node.type !== 'fusion') {
                    // Physics for non-hub nodes
                    node.x += node.vx;
                    node.y += node.vy;
                    if (node.x < 0 || node.x > width) node.vx *= -1;
                    if (node.y < 0 || node.y > height) node.vy *= -1;

                    if (node.parent) {
                        const parent = nodes.find(n => n.id === node.parent);
                        if (parent) {
                            const dx = parent.x - node.x;
                            const dy = parent.y - node.y;
                            node.vx += dx * 0.002;
                            node.vy += dy * 0.002;
                        }
                    }
                }

                // Draw
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
                ctx.fillStyle = node.color;
                ctx.fill();

                if (selectedNode === node.id) {
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }
            });

            animationRef.current = requestAnimationFrame(animate);
        };
        animate();
        return () => cancelAnimationFrame(animationRef.current);
    }, [nodes, selectedNode]);

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

        if (clicked && clicked.type === 'fusion') {
            setSelectedNode(clicked.id);
            if (onSelectGroup) onSelectGroup(clicked.data);
        }
    };

    return (
        <div className="fusion-network">
            <canvas ref={canvasRef} width={500} height={400} onClick={handleClick} />
            <div className="network-legend">
                <div className="legend-item"><span className="dot fused"></span> Fusion Group</div>
                <div className="legend-item"><span className="dot gaia"></span> Source Star</div>
            </div>
        </div>
    );
}

// Main Harmonizer Component
function Harmonizer() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [stats, setStats] = useState(null);
    const [groups, setGroups] = useState([]); // Real groups list
    const [matchRadius, setMatchRadius] = useState(2.0);
    const [lastRun, setLastRun] = useState(null);

    // Selection state
    const [selectedGroup, setSelectedGroup] = useState(null);
    const [groupStars, setGroupStars] = useState([]);
    const [loadingGroup, setLoadingGroup] = useState(false);

    // Load initial stats & groups
    useEffect(() => {
        const saved = sessionStorage.getItem('harmonizer_state');
        let restored = false;

        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                if (parsed.stats) setStats(parsed.stats);
                if (parsed.groups) setGroups(parsed.groups);
                if (parsed.matchRadius) setMatchRadius(parsed.matchRadius);
                if (parsed.lastRun) setLastRun(parsed.lastRun);
                if (parsed.selectedGroup) setSelectedGroup(parsed.selectedGroup);
                if (parsed.groupStars) setGroupStars(parsed.groupStars);
                if (parsed.groups && parsed.groups.length > 0) {
                    restored = true;
                }
            } catch (e) {
                console.error('Failed to restore Harmonizer state', e);
            }
        }

        if (!restored) {
            loadData();
        }
    }, []);

    // Persistence
    useEffect(() => {
        const state = {
            stats,
            groups,
            matchRadius,
            lastRun,
            selectedGroup,
            groupStars
        };
        sessionStorage.setItem('harmonizer_state', JSON.stringify(state));
    }, [stats, groups, matchRadius, lastRun, selectedGroup, groupStars]);

    const loadData = async () => {
        try {
            const [statsData, groupsData] = await Promise.all([
                getHarmonizationStats(),
                getFusionGroups(50) // Load top 50 groups for viz
            ]);
            setStats(statsData);
            setGroups(groupsData);
        } catch (err) {
            console.error('Failed to load harmonization data:', err);
        }
    };

    const handleCrossMatch = async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await runCrossMatch(matchRadius, true);
            setLastRun(result);
            await loadData(); // Refresh everything
        } catch (err) {
            setError(err.response?.data?.detail || 'Cross-match failed');
        } finally {
            setLoading(false);
        }
    };

    const handleGroupSelect = async (group) => {
        setSelectedGroup(group);
        setLoadingGroup(true);
        try {
            const data = await getFusionGroup(group.id);
            setGroupStars(data.stars || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoadingGroup(false);
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
                                {lastRun.message}
                            </span>
                        </div>
                    )}
                </div>

                {/* Center: Network Visualization */}
                <div className="visualization-panel glass-panel">
                    <h3><Link2 size={18} /> Fusion Network</h3>
                    {groups.length > 0 ? (
                        <FusionNetwork
                            groups={groups}
                            onSelectGroup={handleGroupSelect}
                        />
                    ) : (
                        <div className="empty-viz">
                            <Atom size={48} />
                            <p>Run cross-match to generate fusion groups</p>
                        </div>
                    )}
                </div>

                {/* Right: Stats & Inspector */}
                <div className="stats-panel glass-panel">
                    {selectedGroup ? (
                        <div className="group-detail-view">
                            <div className="detail-header">
                                <h3><Eye size={18} /> {selectedGroup.label}</h3>
                                <button className="close-detail" onClick={() => setSelectedGroup(null)}>×</button>
                            </div>

                            <div className="group-meta">
                                <div className="meta-item">
                                    <span className="label">Position</span>
                                    <span className="value">RA {selectedGroup.ra?.toFixed(2)}°, Dec {selectedGroup.dec?.toFixed(2)}°</span>
                                </div>
                                <div className="meta-item">
                                    <span className="label">Stars</span>
                                    <span className="value">{selectedGroup.star_count}</span>
                                </div>
                            </div>

                            <div className="stars-list-wrapper">
                                <h4>Member Stars</h4>
                                {loadingGroup ? (
                                    <div className="loading-list"><Loader2 className="spin" /> Loading...</div>
                                ) : (
                                    <div className="stars-list">
                                        {groupStars.map(star => (
                                            <Link key={star.id} to={`/star/${star.id}`} className="star-list-item">
                                                <div className="star-icon"><Star size={14} /></div>
                                                <div className="star-info">
                                                    <span className="star-id">{star.source_id}</span>
                                                    <span className="star-mag">Mag: {star.brightness_mag?.toFixed(2)}</span>
                                                </div>
                                            </Link>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <>
                            <h3><Star size={18} /> Fusion Statistics</h3>
                            <div className="stat-grid">
                                <div className="stat-box">
                                    <div className="stat-value">{stats?.total_stars?.toLocaleString() || '—'}</div>
                                    <div className="stat-label">Total Stars</div>
                                </div>
                                <div className="stat-box highlight">
                                    <div className="stat-value">{stats?.unique_fusion_groups?.toLocaleString() || '—'}</div>
                                    <div className="stat-label">Fusion Groups</div>
                                </div>
                                <div className="stat-box">
                                    <div className="stat-value">{stats?.stars_in_fusion_groups?.toLocaleString() || '—'}</div>
                                    <div className="stat-label">Fused Stars</div>
                                </div>
                                <div className="stat-box">
                                    <div className="stat-value">{stats?.isolated_stars?.toLocaleString() || '—'}</div>
                                    <div className="stat-label">Isolated</div>
                                </div>
                            </div>
                            <div className="select-hint">
                                <p>Select a group node in the visualization to view its member stars.</p>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Harmonizer;
