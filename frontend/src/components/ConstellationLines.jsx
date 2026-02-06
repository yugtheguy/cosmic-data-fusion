import React, { useMemo } from 'react';
import * as THREE from 'three';

// Simplified constellation data (major constellations)
const CONSTELLATIONS = {
    'Ursa Major': [
        { ra: 165.93, dec: 61.75 }, // Dubhe
        { ra: 166.46, dec: 56.38 }, // Merak
        { ra: 178.46, dec: 53.69 }, // Phecda
        { ra: 183.86, dec: 57.03 }, // Megrez
        { ra: 193.51, dec: 49.31 }, // Alioth
        { ra: 201.30, dec: 54.93 }, // Mizar
        { ra: 206.89, dec: 49.31 }, // Alkaid
    ],
    'Orion': [
        { ra: 88.79, dec: 7.41 },   // Betelgeuse
        { ra: 84.05, dec: 6.35 },   // Bellatrix  
        { ra: 83.00, dec: -0.30 },  // Mintaka
        { ra: 83.82, dec: -1.20 },  // Alnilam
        { ra: 84.05, dec: -1.94 },  // Alnitak
        { ra: 78.63, dec: -8.20 },  // Rigel
        { ra: 85.19, dec: -1.20 },  // Saiph
    ],
    'Cassiopeia': [
        { ra: 14.18, dec: 60.72 },
        { ra: 10.13, dec: 59.15 },
        { ra: 3.31, dec: 60.24 },
        { ra: 358.56, dec: 56.54 },
        { ra: 354.84, dec: 62.93 },
    ]
};

// Convert RA/Dec to 3D Cartesian
function raDecToCartesian(ra, dec, radius = 102) {
    const raRad = (ra * Math.PI) / 180;
    const decRad = (dec * Math.PI) / 180;
    const x = radius * Math.cos(decRad) * Math.cos(raRad);
    const y = radius * Math.sin(decRad);
    const z = -radius * Math.cos(decRad) * Math.sin(raRad);
    return new THREE.Vector3(x, y, z);
}

export function ConstellationLines({ show = false }) {
    if (!show) return null;

    const lines = useMemo(() => {
        const allLines = [];
        
        Object.entries(CONSTELLATIONS).forEach(([name, stars]) => {
            for (let i = 0; i < stars.length - 1; i++) {
                const start = raDecToCartesian(stars[i].ra, stars[i].dec);
                const end = raDecToCartesian(stars[i + 1].ra, stars[i + 1].dec);
                
                allLines.push({
                    name,
                    start,
                    end,
                    color: '#4488FF'
                });
            }
        });
        
        return allLines;
    }, []);

    return (
        <group>
            {lines.map((line, idx) => {
                const points = [line.start, line.end];
                const geometry = new THREE.BufferGeometry().setFromPoints(points);
                
                return (
                    <line key={idx} geometry={geometry}>
                        <lineBasicMaterial 
                            color={line.color} 
                            transparent 
                            opacity={0.25}
                            linewidth={2}
                        />
                    </line>
                );
            })}
        </group>
    );
}

// Ecliptic Plane (Earth's orbital plane)
export function EclipticPlane({ show = false }) {
    if (!show) return null;

    const points = useMemo(() => {
        const pts = [];
        for (let i = 0; i <= 360; i += 5) {
            const angle = (i * Math.PI) / 180;
            // Ecliptic is tilted 23.44° from celestial equator
            const x = 98 * Math.cos(angle);
            const y = 98 * Math.sin(angle) * Math.sin(23.44 * Math.PI / 180);
            const z = 98 * Math.sin(angle) * Math.cos(23.44 * Math.PI / 180);
            pts.push(new THREE.Vector3(x, y, z));
        }
        return pts;
    }, []);

    const geometry = useMemo(() => {
        return new THREE.BufferGeometry().setFromPoints(points);
    }, [points]);

    return (
        <group>
            {/* Ecliptic line */}
            <line geometry={geometry}>
                <lineBasicMaterial 
                    color="#FFD700" 
                    transparent 
                    opacity={0.3}
                    linewidth={2}
                />
            </line>
            {/* Ecliptic plane (semi-transparent) */}
            <mesh rotation={[0, 0, 23.44 * Math.PI / 180]}>
                <ringGeometry args={[0, 98, 64]} />
                <meshBasicMaterial 
                    color="#FFD700" 
                    transparent 
                    opacity={0.03}
                    side={THREE.DoubleSide}
                />
            </mesh>
        </group>
    );
}

// Galactic Plane  
export function GalacticPlane({ show = false }) {
    if (!show) return null;

    return (
        <group rotation={[62.87 * Math.PI / 180, 0, 0]}>
            <mesh>
                <ringGeometry args={[0, 100, 64]} />
                <meshBasicMaterial 
                    color="#9966FF" 
                    transparent 
                    opacity={0.04}
                    side={THREE.DoubleSide}
                />
            </mesh>
            {/* Galactic center marker */}
            <mesh position={[0, 0, 95]}>
                <sphereGeometry args={[1, 16, 16]} />
                <meshBasicMaterial 
                    color="#FF6600" 
                    transparent 
                    opacity={0.8}
                />
            </mesh>
        </group>
    );
}
