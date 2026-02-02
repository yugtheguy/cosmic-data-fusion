import React, { useEffect, useRef } from 'react';
import './ConfidenceHeatmap.css';

/**
 * ConfidenceHeatmap - Background gradient showing prediction confidence zones
 * 
 * Features:
 * - Radial gradient from current epoch
 * - Color zones based on time delta
 * - Smooth transitions
 * - Canvas-based for performance
 */

const ConfidenceHeatmap = ({
    currentEpoch = 2016,
    width = 800,
    height = 600,
    opacity = 0.3
}) => {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const centerX = width / 2;
        const centerY = height / 2;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Calculate time delta from reference epoch (2016)
        const deltaYears = Math.abs(currentEpoch - 2016);

        // Determine color zone based on delta
        let colors;
        if (deltaYears < 5000) {
            // Safe zone (green)
            colors = ['rgba(0, 255, 136, 0.4)', 'rgba(0, 212, 255, 0.2)', 'rgba(0, 212, 255, 0)'];
        } else if (deltaYears < 10000) {
            // Caution zone (yellow)
            colors = ['rgba(255, 235, 59, 0.4)', 'rgba(255, 152, 0, 0.2)', 'rgba(255, 152, 0, 0)'];
        } else if (deltaYears < 20000) {
            // Warning zone (orange)
            colors = ['rgba(255, 152, 0, 0.4)', 'rgba(244, 67, 54, 0.2)', 'rgba(244, 67, 54, 0)'];
        } else if (deltaYears < 50000) {
            // Extreme zone (red)
            colors = ['rgba(244, 67, 54, 0.5)', 'rgba(183, 28, 28, 0.3)', 'rgba(183, 28, 28, 0)'];
        } else {
            // Danger zone (dark red)
            colors = ['rgba(183, 28, 28, 0.6)', 'rgba(100, 0, 0, 0.4)', 'rgba(100, 0, 0, 0)'];
        }

        // Create radial gradient
        const maxRadius = Math.max(width, height);
        const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, maxRadius);

        gradient.addColorStop(0, colors[0]);
        gradient.addColorStop(0.5, colors[1]);
        gradient.addColorStop(1, colors[2]);

        // Apply gradient
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);

        // Add subtle noise texture for visual interest
        if (deltaYears > 20000) {
            ctx.globalAlpha = 0.05;
            for (let i = 0; i < 1000; i++) {
                const x = Math.random() * width;
                const y = Math.random() * height;
                const size = Math.random() * 2;
                ctx.fillStyle = 'white';
                ctx.fillRect(x, y, size, size);
            }
        }

    }, [currentEpoch, width, height]);

    return (
        <canvas
            ref={canvasRef}
            width={width}
            height={height}
            className="confidence-heatmap"
            style={{ opacity }}
        />
    );
};

export default ConfidenceHeatmap;
