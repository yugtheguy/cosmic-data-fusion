import React from 'react';
import './UncertaintyCone.css';

/**
 * UncertaintyCone - Animated uncertainty visualization for star positions
 * 
 * Features:
 * - Pulsating cone animation
 * - Color-coded by uncertainty class
 * - Interactive hover tooltips
 * - Scales with uncertainty magnitude
 */

const UncertaintyCone = ({
    star,
    scale = 1,
    animate = true,
    onHover = null
}) => {
    if (!star || star.uncertainty_deg === undefined) return null;

    // Map uncertainty class to color
    const getColor = (uncertaintyClass) => {
        const colors = {
            'high_confidence': '#00ff88',    // Bright green
            'acceptable': '#ffeb3b',          // Yellow
            'approximate': '#ff9800',         // Orange
            'extreme_range': '#f44336',       // Red
            'unreliable': '#b71c1c'           // Dark red
        };
        return colors[uncertaintyClass] || '#999';
    };

    // Calculate cone size based on uncertainty
    // Scale uncertainty to visual size (degrees to pixels)
    const baseRadius = star.uncertainty_deg * scale * 50; // Tuned multiplier
    const radius = Math.max(2, Math.min(baseRadius, 100)); // Clamp between 2-100px

    const color = getColor(star.uncertainty_class);
    const opacity = 0.3 + (star.confidence_score * 0.4); // 0.3-0.7 based on confidence

    return (
        <g
            className={`uncertainty-cone ${animate ? 'pulse' : ''}`}
            onMouseEnter={() => onHover && onHover(star)}
            onMouseLeave={() => onHover && onHover(null)}
        >
            {/* Outer glow */}
            <circle
                cx="0"
                cy="0"
                r={radius * 1.5}
                fill={color}
                opacity={opacity * 0.2}
                className="uncertainty-glow"
            />

            {/* Main cone */}
            <circle
                cx="0"
                cy="0"
                r={radius}
                fill={color}
                opacity={opacity}
                stroke={color}
                strokeWidth="1"
                className="uncertainty-main"
            />

            {/* Inner core (higher confidence) */}
            <circle
                cx="0"
                cy="0"
                r={radius * 0.3}
                fill={color}
                opacity={opacity + 0.3}
                className="uncertainty-core"
            />

            {/* Confidence rings */}
            {star.confidence_score > 0.5 && (
                <circle
                    cx="0"
                    cy="0"
                    r={radius * 0.6}
                    fill="none"
                    stroke={color}
                    strokeWidth="0.5"
                    opacity={opacity * 0.6}
                    strokeDasharray="2,2"
                    className="confidence-ring"
                />
            )}
        </g>
    );
};

export default UncertaintyCone;
