import React, { useMemo } from 'react';
import { EffectComposer, Bloom, ChromaticAberration } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';
import * as THREE from 'three';

/**
 * Advanced Visual Effects for 3D Celestial Sphere
 * - Volumetric bloom for bright stars
 * - Temporal trails during time travel
 * - Chromatic aberration for time warp effect
 */

export function CelestialEffects({ intensity = 1.0, isWarping = false }) {
    return (
        <EffectComposer>
            {/* Bloom effect for stars */}
            <Bloom
                intensity={intensity * 0.8}
                luminanceThreshold={0.2}
                luminanceSmoothing={0.9}
                mipmapBlur
                radius={0.8}
            />

            {/* Chromatic aberration during time warp */}
            {isWarping && (
                <ChromaticAberration
                    blendFunction={BlendFunction.NORMAL}
                    offset={new THREE.Vector2(0.002, 0.002)}
                />
            )}
        </EffectComposer>
    );
}

/**
 * Star Trail Component - Shows temporal motion paths
 */
export function StarTrails({ stars, currentEpoch, showTrails }) {
    const trailGeometry = useMemo(() => {
        if (!showTrails) return null;

        // Generate trail lines for stars with proper motion
        const starsWithPM = stars.filter(s => s.pmra && s.pmdec && s.total_pm > 20);
        const topMovers = starsWithPM.slice(0, 30);

        return topMovers.map((star, idx) => {
            // Calculate trail from past position to current
            const yearsBack = 1000; // 1000 year trail
            const pmraPerYear = star.pmra / 3600000; // mas/yr to deg/yr
            const pmdecPerYear = star.pmdec / 3600000;

            const points = [];
            for (let t = 0; t <= 1; t += 0.1) {
                const ra = star.ra_at_epoch - pmraPerYear * yearsBack * t;
                const dec = star.dec_at_epoch - pmdecPerYear * yearsBack * t;
                
                // Convert to 3D
                const raRad = (ra * Math.PI) / 180;
                const decRad = (dec * Math.PI) / 180;
                const radius = 100;
                
                const x = radius * Math.cos(decRad) * Math.cos(raRad);
                const y = radius * Math.sin(decRad);
                const z = -radius * Math.cos(decRad) * Math.sin(raRad);
                
                points.push(new THREE.Vector3(x, y, z));
            }

            return { points, color: `hsl(${25 + idx * 10}, 100%, 60%)` };
        });
    }, [stars, showTrails]);

    if (!showTrails || !trailGeometry) return null;

    return (
        <group>
            {trailGeometry.map((trail, idx) => (
                <line key={idx}>
                    <bufferGeometry>
                        <bufferAttribute
                            attach="attributes-position"
                            count={trail.points.length}
                            array={new Float32Array(trail.points.flatMap(p => [p.x, p.y, p.z]))}
                            itemSize={3}
                        />
                    </bufferGeometry>
                    <lineBasicMaterial
                        color={trail.color}
                        transparent
                        opacity={0.6}
                        linewidth={2}
                        blending={THREE.AdditiveBlending}
                    />
                </line>
            ))}
        </group>
    );
}

/**
 * Proper Motion Vectors - Show star movement direction
 */
export function ProperMotionVectors({ stars, showVectors }) {
    const vectors = useMemo(() => {
        if (!showVectors) return [];

        const starsWithPM = stars.filter(s => s.pmra && s.pmdec && s.total_pm > 30);
        const topMovers = starsWithPM.slice(0, 20);

        return topMovers.map(star => {
            const raRad = (star.ra_at_epoch * Math.PI) / 180;
            const decRad = (star.dec_at_epoch * Math.PI) / 180;
            const radius = 100;

            const x = radius * Math.cos(decRad) * Math.cos(raRad);
            const y = radius * Math.sin(decRad);
            const z = -radius * Math.cos(decRad) * Math.sin(raRad);

            // Calculate vector direction
            const pmraPerYear = star.pmra / 3600000;
            const pmdecPerYear = star.pmdec / 3600000;

            const futureRa = star.ra_at_epoch + pmraPerYear * 500;
            const futureDec = star.dec_at_epoch + pmdecPerYear * 500;

            const futureRaRad = (futureRa * Math.PI) / 180;
            const futureDecRad = (futureDec * Math.PI) / 180;

            const fx = radius * Math.cos(futureDecRad) * Math.cos(futureRaRad);
            const fy = radius * Math.sin(futureDecRad);
            const fz = -radius * Math.cos(futureDecRad) * Math.sin(futureRaRad);

            return {
                start: new THREE.Vector3(x, y, z),
                end: new THREE.Vector3(fx, fy, fz)
            };
        });
    }, [stars, showVectors]);

    if (!showVectors) return null;

    return (
        <group>
            {vectors.map((vec, idx) => (
                <arrowHelper
                    key={idx}
                    args={[
                        vec.end.clone().sub(vec.start).normalize(),
                        vec.start,
                        vec.start.distanceTo(vec.end),
                        '#00bfff',
                        2,
                        1
                    ]}
                />
            ))}
        </group>
    );
}

export default CelestialEffects;
