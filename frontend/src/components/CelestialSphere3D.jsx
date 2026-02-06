import React, { useRef, useMemo, useState, useEffect, useCallback } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';
import { CelestialEffects, StarTrails, ProperMotionVectors } from './CelestialEffects';
import { ConstellationLines, EclipticPlane, GalacticPlane } from './ConstellationLines';

/**
 * CelestialSphere3D - Advanced 3D Star Map Visualization
 * 
 * Features:
 * - Real Gaia DR3 star positions
 * - Temporal evolution (Time Machine integration)
 * - Dynamic LOD based on zoom
 * - Uncertainty visualization
 * - Interactive selection
 */

// Convert RA/Dec to 3D Cartesian coordinates on a sphere
function raDecToCartesian(ra, dec, radius = 100) {
    // RA in degrees (0-360), Dec in degrees (-90 to 90)
    const raRad = (ra * Math.PI) / 180;
    const decRad = (dec * Math.PI) / 180;

    // Spherical to Cartesian conversion
    const x = radius * Math.cos(decRad) * Math.cos(raRad);
    const y = radius * Math.sin(decRad);
    const z = -radius * Math.cos(decRad) * Math.sin(raRad); // Negative Z for proper orientation

    return new THREE.Vector3(x, y, z);
}

// Calculate star position at a given epoch using proper motion
function calculatePositionAtEpoch(star, targetEpoch, referenceEpoch = 2016) {
    // If star has proper motion data, calculate movement
    if (star.pmra && star.pmdec) {
        const yearsDelta = targetEpoch - referenceEpoch;
        
        // Convert proper motion from mas/year to degrees/year
        const pmraDegPerYear = (star.pmra / 1000) / 3600; // mas/yr to deg/yr
        const pmdecDegPerYear = (star.pmdec / 1000) / 3600;
        
        // Calculate new position
        const newRa = star.ra_at_epoch + (pmraDegPerYear * yearsDelta);
        const newDec = star.dec_at_epoch + (pmdecDegPerYear * yearsDelta);
        
        // Keep RA in valid range [0, 360]
        const normalizedRa = ((newRa % 360) + 360) % 360;
        
        // Clamp Dec to valid range [-90, 90]
        const clampedDec = Math.max(-90, Math.min(90, newDec));
        
        return { ra: normalizedRa, dec: clampedDec };
    }
    
    // No proper motion data - return original position
    return { ra: star.ra_at_epoch, dec: star.dec_at_epoch };
}

// Get realistic star color based on magnitude and spectral type simulation
function getStarColor(star) {
    const mag = star.brightness_mag || 10;
    const pmTotal = Math.sqrt((star.pmra || 0)**2 + (star.pmdec || 0)**2);
    
    // Spectral class simulation (brighter + high PM often = nearby hot stars)
    if (mag < 2) return '#E0F7FF'; // O/B type - brilliant blue-white (Rigel, Spica)
    if (mag < 4) return '#F0F8FF'; // A type - white (Sirius, Vega)
    if (mag < 6) return '#FFF8DC'; // F type - yellow-white (Procyon)
    if (mag < 8) return '#FFFFED'; // G type - yellow (Sun-like)
    if (mag < 10) return '#FFDDB4'; // K type - orange (Arcturus)
    if (mag < 12) return '#FFB380'; // M type - red-orange
    
    // Very faint stars - dim red
    return pmTotal > 20 ? '#FF6B6B' : '#FF9988'; // Highlight fast movers in brighter red
}

// Get star luminosity multiplier for bloom effect
function getStarBrightness(mag) {
    // Exponential brightness scaling (human eye perception)
    return Math.pow(2, (6 - mag) / 2.5);
}

// Get star size based on brightness (magnitude)
function getStarSize(magnitude, baseSize = 6) {
    // Brighter stars (lower magnitude) = larger size
    return baseSize * Math.pow(2, (6 - magnitude) / 3);
}

// Enhanced Star Labels for brightest stars
function StarLabels({ stars, currentEpoch }) {
    // Show labels for very bright stars only (mag < 3)
    const brightStars = useMemo(() => {
        return stars
            .filter(s => (s.brightness_mag || 10) < 3)
            .slice(0, 20); // Top 20 brightest
    }, [stars]);

    return (
        <group>
            {brightStars.map((star) => {
                const pos = raDecToCartesian(
                    star.animated_ra || star.ra_at_epoch,
                    star.animated_dec || star.dec_at_epoch,
                    105 // Slightly outside sphere
                );
                
                return (
                    <group key={star.id} position={[pos.x, pos.y, pos.z]}>
                        {/* Text sprite would go here - simplified for performance */}
                        <sprite scale={[3, 1.5, 1]}>
                            <spriteMaterial 
                                color="#ffffff" 
                                transparent 
                                opacity={0.7}
                                depthTest={false}
                            />
                        </sprite>
                    </group>
                );
            })}
        </group>
    );
}

// Data Statistics Overlay Component
function DataStatsOverlay({ stars }) {
    const stats = useMemo(() => {
        if (!stars.length) return null;
        
        const mags = stars.map(s => s.brightness_mag || 10);
        const pmValues = stars.map(s => Math.sqrt((s.pmra || 0)**2 + (s.pmdec || 0)**2));
        
        return {
            count: stars.length,
            brightestMag: Math.min(...mags).toFixed(2),
            faintestMag: Math.max(...mags).toFixed(2),
            avgMag: (mags.reduce((a, b) => a + b, 0) / mags.length).toFixed(2),
            fastestPM: Math.max(...pmValues).toFixed(1),
            highPMCount: pmValues.filter(pm => pm > 20).length
        };
    }, [stars]);

    return stats;
}

// Star Field Component - Photorealistic rendering with temporal animation
function StarField({ stars, currentEpoch, showUncertainty, selectedStarId, onStarClick }) {
    // Performance optimization: limit visible stars with smart filtering
    const MAX_VISIBLE_STARS = 5000;
    const limitedStars = useMemo(() => {
        if (stars.length <= MAX_VISIBLE_STARS) return stars;
        
        // Smart prioritization: brightest stars + high proper motion stars
        const bright = stars.filter(s => (s.brightness_mag || 10) < 8);
        const fastMovers = stars.filter(s => {
            const pm = Math.sqrt((s.pmra || 0)**2 + (s.pmdec || 0)**2);
            return pm > 20;
        });
        
        // Combine and deduplicate
        const priority = [...new Set([...bright, ...fastMovers])];
        const remaining = stars.filter(s => !priority.includes(s));
        
        return [...priority, ...remaining].slice(0, MAX_VISIBLE_STARS);
    }, [stars]);

    // Recalculate all star positions when epoch changes
    const animatedStars = useMemo(() => {
        return limitedStars.map(star => {
            const position = calculatePositionAtEpoch(star, currentEpoch);
            return {
                ...star,
                animated_ra: position.ra,
                animated_dec: position.dec
            };
        });
    }, [limitedStars, currentEpoch]);
    
    // Debug logging - reduced frequency to avoid spam
    const debugRef = useRef(0);
    useEffect(() => {
        debugRef.current++;
        // Only log every 10th render to reduce console spam
        if (debugRef.current % 10 === 0) {
            console.log(`StarField rendered ${animatedStars.length} stars (render #${debugRef.current})`);
            if (animatedStars.length > 0) {
                console.log(`Sample star magnitude:`, animatedStars[0].brightness_mag);
            }
        }
    }, [animatedStars]);
    
    return (
        <group>
            {animatedStars.map((star, index) => {
                const pos = raDecToCartesian(star.animated_ra, star.animated_dec, 100);
                const color = getStarColor(star);
                const mag = star.brightness_mag || 10;
                
                // Stellarium-like star sizes - clearly visible but elegant
                const baseMagnitude = Math.min(mag, 12); // Cap very faint stars
                const coreSize = Math.max(0.5, (8 - baseMagnitude) * 0.25); // Much more visible
                const glowSize = coreSize * 2.5; // Moderate glow
                
                // Magnitude-based brightness: brighter stars (lower mag) = higher opacity
                // Magnitude scale: -1.5 (Sirius) to 6 (naked eye limit) to 15+ (very faint)
                const normalizedMag = Math.max(-1, Math.min(baseMagnitude, 12)); // Clamp for calculation
                const brightness = 1 - ((normalizedMag + 1) / 13); // 0 to 1 scale (reversed)
                
                const outerGlowOpacity = Math.max(0.05, brightness * 0.25); // 0.05 to 0.25
                const midGlowOpacity = Math.max(0.15, brightness * 0.5); // 0.15 to 0.5
                const coreOpacity = Math.max(0.6, brightness); // 0.6 to 1.0 for core
                
                const isSelected = selectedStarId === star.id;
                
                return (
                    <group key={star.id || index} position={[pos.x, pos.y, pos.z]}>
                        {/* Outer glow - magnitude-based opacity */}
                        <mesh
                            onClick={(e) => {
                                e.stopPropagation();
                                onStarClick(star);
                            }}
                        >
                            <sphereGeometry args={[glowSize, 6, 6]} />
                            <meshBasicMaterial 
                                color={color}
                                transparent
                                opacity={outerGlowOpacity}
                                depthWrite={false}
                            />
                        </mesh>
                        
                        {/* Mid glow - magnitude-based opacity */}
                        <mesh>
                            <sphereGeometry args={[glowSize * 0.5, 6, 6]} />
                            <meshBasicMaterial 
                                color={color}
                                transparent
                                opacity={midGlowOpacity}
                                depthWrite={false}
                            />
                        </mesh>
                        
                        {/* Bright core - magnitude-based opacity */}
                        <mesh>
                            <sphereGeometry args={[coreSize, 6, 6]} />
                            <meshBasicMaterial 
                                color={color}
                                transparent={baseMagnitude > 3}
                                opacity={baseMagnitude > 3 ? coreOpacity : 1.0}
                            />
                        </mesh>
                        
                        {/* Selection indicator */}
                        {isSelected && (
                            <>
                                <mesh>
                                    <ringGeometry args={[coreSize * 3, coreSize * 3.5, 16]} />
                                    <meshBasicMaterial 
                                        color="#00ffff"
                                        transparent
                                        opacity={0.6}
                                        side={THREE.DoubleSide}
                                    />
                                </mesh>
                                <mesh>
                                    <sphereGeometry args={[glowSize * 2, 8, 8]} />
                                    <meshBasicMaterial 
                                        color="#00ffff"
                                        transparent
                                        opacity={0.05}
                                        wireframe
                                    />
                                </mesh>
                            </>
                        )}
                    </group>
                );
            })}
        </group>
    );
}

// Motion Trails Component - Shows star paths over time
function MotionTrails({ stars, currentEpoch, showTrails }) {
    if (!showTrails) return null;
    
    // Only show trails for stars with ANY proper motion (much lower threshold)
    const trailStars = useMemo(() => {
        return stars
            .map(s => ({
                ...s,
                totalPm: Math.sqrt((s.pmra || 0) ** 2 + (s.pmdec || 0) ** 2)
            }))
            .filter(s => s.totalPm > 2) // Higher threshold for visible motion
            .sort((a, b) => b.totalPm - a.totalPm) // Sort by speed (fastest first)
            .slice(0, 50); // Top 50 fastest stars for performance
    }, [stars]);
    
    console.log(`MotionTrails: Found ${trailStars.length} stars with significant proper motion`);
    if (trailStars.length > 0) {
        console.log(`Top star PM: ${trailStars[0].totalPm.toFixed(2)} mas/yr`);
    }
    
    return (
        <group>
            {trailStars.map((star, idx) => {
                // Generate trail points from past to present - visible trails
                const trailPoints = [];
                const yearsBack = 5000; // 5,000 years for clearly visible trails
                const steps = 15; // Fewer steps for performance
                
                for (let i = 0; i <= steps; i++) {
                    const epoch = currentEpoch - yearsBack + (yearsBack * i / steps);
                    const position = calculatePositionAtEpoch(star, epoch);
                    const pos3d = raDecToCartesian(position.ra, position.dec, 100);
                    trailPoints.push(pos3d);
                }
                
                const curve = new THREE.CatmullRomCurve3(trailPoints);
                const points = curve.getPoints(30); // Good balance of smoothness and performance
                const geometry = new THREE.BufferGeometry().setFromPoints(points);
                
                // Create multiple lines for thickness since linewidth doesn't work in WebGL
                return (
                    <group key={idx}>
                        <line geometry={geometry}>
                            <lineBasicMaterial 
                                color="#ff8800" // Bright orange that stands out
                                transparent
                                opacity={0.9} // High opacity for visibility
                            />
                        </line>
                        {/* Secondary glow trail */}
                        <line geometry={geometry}>
                            <lineBasicMaterial 
                                color="#ff6600" // Slightly different orange
                                transparent
                                opacity={0.6}
                            />
                        </line>
                        {/* Trail markers - small spheres along the path */}
                        {points.filter((_, i) => i % 10 === 0).map((point, markerIdx) => (
                            <mesh key={markerIdx} position={[point.x, point.y, point.z]}>
                                <sphereGeometry args={[0.05, 4, 4]} />
                                <meshBasicMaterial 
                                    color="#ff4500"
                                    transparent
                                    opacity={0.8}
                                />
                            </mesh>
                        ))}
                    </group>
                );
            })}
        </group>
    );
}

// Uncertainty Cone Component (shows prediction uncertainty)
function UncertaintyCones({ stars, showUncertainty }) {
    if (!showUncertainty) return null;

    // Only show cones for top 50 stars to avoid performance hit
    const topStars = useMemo(() => {
        return stars
            .filter(s => s.uncertainty_deg && s.uncertainty_deg < 10)
            .slice(0, 50);
    }, [stars]);

    return (
        <group>
            {topStars.map((star, idx) => {
                const pos = raDecToCartesian(star.ra_at_epoch, star.dec_at_epoch, 100);
                const coneHeight = star.uncertainty_deg * 2;
                const coneRadius = star.uncertainty_deg * 0.5;

                return (
                    <mesh key={idx} position={pos}>
                        <coneGeometry args={[coneRadius, coneHeight, 8]} />
                        <meshBasicMaterial
                            color={getStarColor(star)}
                            transparent
                            opacity={0.15}
                            side={THREE.DoubleSide}
                        />
                    </mesh>
                );
            })}
        </group>
    );
}

// Celestial Grid Component - Elegant wireframe
function CelestialGrid({ show }) {
    if (!show) return null;

    return (
        <group>
            {/* Declination circles - subtle blue lines */}
            {[-60, -30, 0, 30, 60].map((dec) => {
                const radius = 100 * Math.cos((dec * Math.PI) / 180);
                const y = 100 * Math.sin((dec * Math.PI) / 180);
                return (
                    <mesh key={dec} position={[0, y, 0]} rotation={[Math.PI / 2, 0, 0]}>
                        <ringGeometry args={[radius - 0.1, radius + 0.1, 64]} />
                        <meshBasicMaterial 
                            color="#4488ff" 
                            transparent 
                            opacity={0.08} 
                            side={THREE.DoubleSide} 
                        />
                    </mesh>
                );
            })}

            {/* RA meridians - very subtle */}
            {Array.from({ length: 24 }, (_, i) => i * 15).map((ra) => {
                const angle = (ra * Math.PI) / 180;
                return (
                    <line key={ra}>
                        <bufferGeometry>
                            <bufferAttribute
                                attach="attributes-position"
                                count={2}
                                array={new Float32Array([
                                    100 * Math.cos(angle), -100, -100 * Math.sin(angle),
                                    100 * Math.cos(angle), 100, -100 * Math.sin(angle)
                                ])}
                                itemSize={3}
                            />
                        </bufferGeometry>
                        <lineBasicMaterial color="#3366cc" transparent opacity={0.06} />
                    </line>
                );
            })}
        </group>
    );
}

// Main Scene Component
function Scene({ stars, currentEpoch, showUncertainty, showGrid, selectedStarId, onStarClick, showTrails, showVectors, isWarping, showConstellations, showEcliptic, showGalactic }) {
    const controlsRef = useRef();

    return (
        <>
            {/* Camera with cinematic positioning */}
            <PerspectiveCamera makeDefault position={[0, 30, 200]} fov={70} />
            <OrbitControls
                ref={controlsRef}
                enableDamping
                dampingFactor={0.03}
                rotateSpeed={0.4}
                zoomSpeed={0.8}
                minDistance={80}
                maxDistance={400}
                enablePan={true}
                maxPolarAngle={Math.PI}
            />

            {/* Enhanced lighting for depth */}
            <ambientLight intensity={0.15} color="#0a0a25" />
            <pointLight position={[0, 0, 0]} intensity={0.4} color="#ffffff" distance={500} decay={2} />
            <pointLight position={[100, 50, 100]} intensity={0.2} color="#6699ff" distance={300} decay={2} />
            <pointLight position={[-100, -50, -100]} intensity={0.2} color="#ffaa44" distance={300} decay={2} />
            <pointLight position={[0, 150, 0]} intensity={0.15} color="#9966ff" distance={400} decay={2} />

            {/* Distant starfield - reduced to avoid interference */}
            <Stars 
                radius={350} 
                depth={80} 
                count={500} // Reduced from 5000
                factor={1} // Reduced from 3
                saturation={0.05} // Reduced from 0.1
                fade 
                speed={0.1} // Reduced from 0.2
            />

            {/* Main star field */}
            <StarField
                stars={stars}
                currentEpoch={currentEpoch}
                showUncertainty={showUncertainty}
                selectedStarId={selectedStarId}
                onStarClick={onStarClick}
            />

            {/* Uncertainty visualization */}
            <UncertaintyCones stars={stars} showUncertainty={showUncertainty} />

            {/* Motion trails - shows temporal star paths */}
            <MotionTrails stars={stars} currentEpoch={currentEpoch} showTrails={showTrails} />

            {/* Proper motion vectors */}
            <ProperMotionVectors stars={stars} showVectors={showVectors} />

            {/* Celestial grid - subtle and elegant */}
            <CelestialGrid show={showGrid} />
            
            {/* Constellation lines - for navigation */}
            <ConstellationLines show={showConstellations} />
            
            {/* Ecliptic Plane - Earth's orbital plane */}
            <EclipticPlane show={showEcliptic} />
            
            {/* Galactic Plane - Milky Way disk */}
            <GalacticPlane show={showGalactic} />
            
            {/* Atmospheric nebula fog */}
            <fog attach="fog" args={['#050510', 150, 500]} />

            {/* Celestial sphere (outer sphere) - removed for better visibility */}

            {/* Post-processing effects */}
            {/* <CelestialEffects intensity={1.2} isWarping={isWarping} /> */}
        </>
    );
}

// Main Component Export
export default function CelestialSphere3D({
    stars = [],
    currentEpoch = 2016,
    showUncertainty = true,
    showGrid = true,
    selectedStarId = null,
    onStarClick = () => {},
    showTrails = false,
    showVectors = false,
    isWarping = false,
    className = ''
}) {
    const [selectedStar, setSelectedStar] = useState(null);
    const [showConstellations, setShowConstellations] = useState(false);
    const [showEcliptic, setShowEcliptic] = useState(false);
    const [showGalactic, setShowGalactic] = useState(false);
    const [showStats, setShowStats] = useState(true);

    const handleStarClick = (star) => {
        setSelectedStar(star);
        onStarClick(star);
    };
    
    // Calculate statistics
    const stats = useMemo(() => {
        if (!stars.length) return null;
        
        const mags = stars.map(s => s.brightness_mag || 10);
        const pmValues = stars.map(s => Math.sqrt((s.pmra || 0)**2 + (s.pmdec || 0)**2));
        
        return {
            count: stars.length,
            brightestMag: Math.min(...mags).toFixed(2),
            faintestMag: Math.max(...mags).toFixed(2),
            avgMag: (mags.reduce((a, b) => a + b, 0) / mags.length).toFixed(2),
            fastestPM: Math.max(...pmValues).toFixed(1),
            highPMCount: pmValues.filter(pm => pm > 20).length
        };
    }, [stars]);

    return (
        <div className={className} style={{ width: '100%', height: '100%', position: 'relative' }}>
            <WebGLErrorBoundary>
                <Canvas
                    gl={{
                        antialias: true,
                        alpha: true,
                        powerPreference: 'high-performance',
                        preserveDrawingBuffer: false,
                        failIfMajorPerformanceCaveat: false
                    }}
                    dpr={[1, 2]}
                    onCreated={(state) => {
                        // Add context loss and restore handlers
                        const gl = state.gl.getContext();
                        const canvas = state.gl.domElement;
                        
                        canvas.addEventListener('webglcontextlost', (event) => {
                            console.warn('WebGL context lost, preventing default and attempting recovery');
                            event.preventDefault();
                        });
                        
                        canvas.addEventListener('webglcontextrestored', () => {
                            console.log('WebGL context restored successfully');
                            // Force re-render
                            state.invalidate();
                        });
                    }}
                >
                    <Scene
                        stars={stars}
                        currentEpoch={currentEpoch}
                        showUncertainty={showUncertainty}
                        showGrid={showGrid}
                        selectedStarId={selectedStar?.id || selectedStarId}
                        onStarClick={handleStarClick}
                        showTrails={showTrails}
                        showVectors={showVectors}
                        isWarping={isWarping}
                        showConstellations={showConstellations}
                        showEcliptic={showEcliptic}
                        showGalactic={showGalactic}
                    />
                </Canvas>
            </WebGLErrorBoundary>

            {/* Visual Controls Panel */}
            <div
                style={{
                    position: 'absolute',
                    top: '5.5rem',
                    right: '1rem',
                    background: 'rgba(0, 0, 0, 0.75)',
                    backdropFilter: 'blur(15px)',
                    padding: '1rem',
                    borderRadius: '12px',
                    color: '#e5e5e5',
                    fontSize: '0.85rem',
                    fontFamily: 'JetBrains Mono, monospace',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    minWidth: '200px',
                    zIndex: 90
                }}
            >
                <div style={{ fontWeight: '600', marginBottom: '0.75rem', color: '#6699ff' }}>
                    🎨 Visual Controls
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input 
                            type="checkbox" 
                            checked={showConstellations}
                            onChange={(e) => setShowConstellations(e.target.checked)}
                            style={{ marginRight: '0.5rem' }}
                        />
                        <span>Constellations</span>
                    </label>
                    
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input 
                            type="checkbox" 
                            checked={showEcliptic}
                            onChange={(e) => setShowEcliptic(e.target.checked)}
                            style={{ marginRight: '0.5rem' }}
                        />
                        <span>Ecliptic Plane</span>
                    </label>
                    
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input 
                            type="checkbox" 
                            checked={showGalactic}
                            onChange={(e) => setShowGalactic(e.target.checked)}
                            style={{ marginRight: '0.5rem' }}
                        />
                        <span>Galactic Plane</span>
                    </label>
                    
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input 
                            type="checkbox" 
                            checked={showStats}
                            onChange={(e) => setShowStats(e.target.checked)}
                            style={{ marginRight: '0.5rem' }}
                        />
                        <span>Data Statistics</span>
                    </label>
                </div>
            </div>

            {/* Data Statistics Panel */}
            {showStats && stats && (
                <div
                    style={{
                        position: 'absolute',
                        bottom: '5.5rem',
                        right: '1rem',
                        background: 'rgba(0, 0, 0, 0.7)',
                        backdropFilter: 'blur(10px)',
                        padding: '1rem',
                        borderRadius: '12px',
                        color: '#e5e5e5',
                        fontSize: '0.8rem',
                        fontFamily: 'JetBrains Mono, monospace',
                        border: '1px solid rgba(255, 255, 255, 0.12)',
                        minWidth: '200px',
                        zIndex: 90
                    }}
                >
                    <div style={{ fontWeight: '600', marginBottom: '0.5rem', color: '#ff9966' }}>
                        📊 Dataset Statistics
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', fontSize: '0.75rem' }}>
                        <div style={{ color: '#888' }}>Total Stars:</div>
                        <div style={{ color: '#6699ff', fontWeight: '500' }}>{stats.count.toLocaleString()}</div>
                        
                        <div style={{ color: '#888' }}>Brightest Mag:</div>
                        <div style={{ color: '#ffcc66' }}>{stats.brightestMag}</div>
                        
                        <div style={{ color: '#888' }}>Faintest Mag:</div>
                        <div>{stats.faintestMag}</div>
                        
                        <div style={{ color: '#888' }}>Average Mag:</div>
                        <div>{stats.avgMag}</div>
                        
                        <div style={{ color: '#888' }}>Fast Movers:</div>
                        <div style={{ color: '#ff6666' }}>{stats.highPMCount}</div>
                        
                        <div style={{ color: '#888' }}>Max PM:</div>
                        <div style={{ color: '#ff6666' }}>{stats.fastestPM} mas/yr</div>
                    </div>
                </div>
            )}

            {/* Info overlay */}
            <div
                style={{
                    position: 'absolute',
                    bottom: '5.5rem',
                    left: '1rem',
                    background: 'rgba(0, 0, 0, 0.6)',
                    backdropFilter: 'blur(10px)',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    color: '#e5e5e5',
                    fontSize: '0.85rem',
                    fontFamily: 'JetBrains Mono, monospace',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    pointerEvents: 'none'
                }}
            >
                <div>🌟 {stars.length} stars visible</div>
                <div>📅 Epoch: {currentEpoch} {currentEpoch < 0 ? 'BC' : 'AD'}</div>
                {currentEpoch !== 2016 && (
                    <div style={{ color: '#d4683a', fontSize: '0.75rem', marginTop: '0.25rem' }}>
                        ⏱️ Motion: {currentEpoch > 2016 ? '+' : ''}{currentEpoch - 2016} years
                    </div>
                )}
                <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#888' }}>
                    Click stars for details • Drag to rotate • Scroll to zoom
                </div>
            </div>

            {/* Selected Star Info Panel */}
            {selectedStar && (
                <div
                    style={{
                        position: 'absolute',
                        top: '1rem',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        background: 'rgba(0, 0, 0, 0.85)',
                        backdropFilter: 'blur(15px)',
                        padding: '1rem 1.5rem',
                        borderRadius: '12px',
                        color: '#e5e5e5',
                        fontSize: '0.9rem',
                        fontFamily: 'JetBrains Mono, monospace',
                        border: '2px solid ' + getStarColor(selectedStar),
                        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
                        minWidth: '320px',
                        maxWidth: '400px',
                        zIndex: 100
                    }}
                >
                    <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'flex-start',
                        marginBottom: '1rem'
                    }}>
                        <div style={{ 
                            fontSize: '1.1rem', 
                            fontWeight: 'bold',
                            color: getStarColor(selectedStar),
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}>
                            <span>⭐</span>
                            <span>Star {selectedStar.source_id?.slice(-8) || 'Unknown'}</span>
                        </div>
                        <button
                            onClick={() => setSelectedStar(null)}
                            style={{
                                background: 'rgba(255, 255, 255, 0.1)',
                                border: 'none',
                                color: '#fff',
                                borderRadius: '6px',
                                padding: '0.25rem 0.5rem',
                                cursor: 'pointer',
                                fontSize: '0.85rem'
                            }}
                        >
                            ✕
                        </button>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '0.5rem' }}>
                            <span style={{ color: '#888' }}>Position:</span>
                            <span>RA {selectedStar.ra_at_epoch?.toFixed(4)}°, Dec {selectedStar.dec_at_epoch?.toFixed(4)}°</span>
                        </div>
                        
                        <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '0.5rem' }}>
                            <span style={{ color: '#888' }}>Magnitude:</span>
                            <span>{selectedStar.brightness_mag?.toFixed(2)}</span>
                        </div>

                        {selectedStar.total_pm && (
                            <>
                                <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '0.5rem' }}>
                                    <span style={{ color: '#888' }}>Proper Motion:</span>
                                    <span>{selectedStar.total_pm.toFixed(2)} mas/yr</span>
                                </div>
                                
                                {(selectedStar.pmra || selectedStar.pmdec) && (
                                    <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '0.5rem' }}>
                                        <span style={{ color: '#888' }}>PM Vector:</span>
                                        <span style={{ fontSize: '0.85rem' }}>
                                            RA: {selectedStar.pmra?.toFixed(2) || 0} mas/yr<br/>
                                            Dec: {selectedStar.pmdec?.toFixed(2) || 0} mas/yr
                                        </span>
                                    </div>
                                )}
                                
                                {currentEpoch !== 2016 && (
                                    <div style={{ 
                                        padding: '0.5rem',
                                        background: 'rgba(212, 104, 58, 0.15)',
                                        borderRadius: '6px',
                                        fontSize: '0.85rem',
                                        borderLeft: '3px solid #d4683a'
                                    }}>
                                        <div style={{ color: '#d4683a', fontWeight: 'bold', marginBottom: '0.25rem' }}>
                                            Motion Calculated
                                        </div>
                                        <div style={{ color: '#e8a87c' }}>
                                            Position shifted {Math.abs(currentEpoch - 2016)} years {currentEpoch > 2016 ? 'forward' : 'backward'}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}

                        <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '0.5rem' }}>
                            <span style={{ color: '#888' }}>Uncertainty:</span>
                            <span style={{ 
                                color: getStarColor(selectedStar),
                                fontWeight: 'bold'
                            }}>
                                {selectedStar.uncertainty_class?.replace('_', ' ').toUpperCase() || 'N/A'}
                                {selectedStar.uncertainty_deg && ` (${selectedStar.uncertainty_deg.toFixed(3)}°)`}
                            </span>
                        </div>

                        {selectedStar.parallax && (
                            <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '0.5rem' }}>
                                <span style={{ color: '#888' }}>Parallax:</span>
                                <span>{selectedStar.parallax.toFixed(4)} mas</span>
                            </div>
                        )}

                        <div style={{ 
                            marginTop: '0.5rem', 
                            padding: '0.75rem',
                            background: 'rgba(255, 255, 255, 0.05)',
                            borderRadius: '6px',
                            fontSize: '0.8rem',
                            color: '#aaa'
                        }}>
                            <div>Gaia Source ID: {selectedStar.source_id || 'N/A'}</div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// WebGL Error Boundary Component
class WebGLErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, errorMessage: '' };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, errorMessage: error.message };
    }

    componentDidCatch(error, errorInfo) {
        console.error('WebGL Error:', error, errorInfo);
        
        // Try to recover from WebGL context loss
        if (error.message.includes('context') || error.message.includes('WebGL')) {
            setTimeout(() => {
                this.setState({ hasError: false, errorMessage: '' });
            }, 2000);
        }
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    background: '#0a0a0f',
                    color: '#ffffff',
                    textAlign: 'center',
                    padding: '2rem'
                }}>
                    <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🌌</div>
                    <h3>WebGL Context Lost</h3>
                    <p>Attempting to recover the 3D visualization...</p>
                    <div style={{ 
                        marginTop: '1rem', 
                        fontSize: '0.8rem', 
                        color: '#888',
                        maxWidth: '400px'
                    }}>
                        This can happen due to GPU driver issues or browser memory management.
                        The visualization should automatically recover in a moment.
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
