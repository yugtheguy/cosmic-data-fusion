import React, { useState, useEffect, useRef } from 'react';
import './TimelineController.css';

/**
 * Timeline Controller Component for Time Machine
 * 
 * Interactive timeline slider allowing users to:
 * - Scrub through time (-10,000 to +10,000 years)
 * - Play/pause animation
 * - Control animation speed
 * - Jump to preset epochs
 */
const TimelineController = ({
    currentEpoch,
    onEpochChange,
    isPlaying = false,
    onPlayPauseToggle,
    minEpoch = -10000,
    maxEpoch = 10000,
    referenceEpoch = 2016
}) => {
    const [localEpoch, setLocalEpoch] = useState(currentEpoch);
    const [playbackSpeed, setPlaybackSpeed] = useState(1); // 1x, 2x, 5x, 10x
    const animationRef = useRef(null);
    const lastUpdateRef = useRef(Date.now());
    const localEpochRef = useRef(currentEpoch);

    // Preset epoch bookmarks
    const bookmarks = [
        { epoch: -5000, label: '5000 BC', description: 'Bronze Age' },
        { epoch: -3000, label: '3000 BC', description: 'Pyramids Era' },
        { epoch: -1000, label: '1000 BC', description: 'Iron Age' },
        { epoch: 0, label: '0 AD', description: 'Common Era Start' },
        { epoch: 1000, label: '1000 AD', description: 'Medieval Period' },
        { epoch: 2016, label: '2016 AD', description: 'Gaia Reference' },
        { epoch: 3000, label: '3000 AD', description: 'Far Future' },
        { epoch: 5000, label: '5000 AD', description: 'Deep Future' }
    ];

    // Format epoch as human-readable year
    const formatEpoch = (epoch) => {
        if (epoch >= 1) {
            return `${Math.floor(epoch)} AD`;
        } else {
            return `${Math.abs(Math.floor(epoch))} BC`;
        }
    };

    // Get uncertainty classification based on delta from reference
    const getUncertaintyClass = (epoch) => {
        const delta = Math.abs(epoch - referenceEpoch);
        if (delta < 5000) return { class: 'high-confidence', label: 'High Confidence', color: '#10b981' };
        if (delta < 10000) return { class: 'acceptable', label: 'Acceptable', color: '#f59e0b' };
        if (delta < 20000) return { class: 'approximate', label: 'Approximate', color: '#ef4444' };
        return { class: 'unreliable', label: 'Unreliable', color: '#dc2626' };
    };

    // Keep local epoch in sync when external epoch changes (e.g., slider or parent updates)
    useEffect(() => {
        if (!isPlaying) {
            setLocalEpoch(currentEpoch);
            localEpochRef.current = currentEpoch;
        }
    }, [currentEpoch, isPlaying]);

    // Animation loop for playback
    useEffect(() => {
        if (!isPlaying) {
            return undefined;
        }

        let frameCount = 0;
        const EPOCH_UPDATE_INTERVAL = 10; // Only update epoch every 10 frames (~6 times per second)

        const animate = () => {
            const now = Date.now();
            const deltaTime = (now - lastUpdateRef.current) / 1000; // seconds
            lastUpdateRef.current = now;

            // Years per second (100 years/sec at 1x speed)
            const yearsPerSecond = 100 * playbackSpeed;
            let newEpoch = localEpochRef.current + (yearsPerSecond * deltaTime);

            // Wrap around or stop at boundaries
            if (newEpoch > maxEpoch) {
                newEpoch = minEpoch; // Loop back
            }

            localEpochRef.current = newEpoch;
            setLocalEpoch(newEpoch);

            // Throttle epoch change callbacks to reduce API calls
            frameCount++;
            if (frameCount >= EPOCH_UPDATE_INTERVAL) {
                onEpochChange(newEpoch);
                frameCount = 0;
            }

            animationRef.current = requestAnimationFrame(animate);
        };

        animationRef.current = requestAnimationFrame(animate);

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
            // Ensure final epoch is set when animation stops
            onEpochChange(localEpochRef.current);
        };
    }, [isPlaying, playbackSpeed, minEpoch, maxEpoch, onEpochChange]);

    // Handle slider change
    const handleSliderChange = (e) => {
        const newEpoch = parseFloat(e.target.value);
        setLocalEpoch(newEpoch);
        localEpochRef.current = newEpoch;
        onEpochChange(newEpoch);
    };

    // Jump to bookmark
    const jumpToEpoch = (epoch) => {
        setLocalEpoch(epoch);
        localEpochRef.current = epoch;
        onEpochChange(epoch);
    };

    // Step controls
    const stepBackward = () => {
        const newEpoch = Math.max(minEpoch, localEpoch - 100);
        setLocalEpoch(newEpoch);
        localEpochRef.current = newEpoch;
        onEpochChange(newEpoch);
    };

    const stepForward = () => {
        const newEpoch = Math.min(maxEpoch, localEpoch + 100);
        setLocalEpoch(newEpoch);
        localEpochRef.current = newEpoch;
        onEpochChange(newEpoch);
    };

    const uncertainty = getUncertaintyClass(localEpoch);

    // Calculate slider percentage position
    const sliderPercent = ((localEpoch - minEpoch) / (maxEpoch - minEpoch)) * 100;

    return (
        <div className="timeline-controller">
            {/* Main Display */}
            <div className="timeline-display">
                <div className="epoch-display">
                    <div className="epoch-year">{formatEpoch(localEpoch)}</div>
                    <div className="epoch-details">
                        <span className="delta-years">
                            {localEpoch - referenceEpoch > 0 ? '+' : ''}
                            {Math.floor(localEpoch - referenceEpoch)} years from Gaia epoch
                        </span>
                        <span
                            className={`uncertainty-badge ${uncertainty.class}`}
                            style={{ backgroundColor: uncertainty.color }}
                        >
                            {uncertainty.label}
                        </span>
                    </div>
                </div>

                {/* Playback Controls */}
                <div className="playback-controls">
                    <button
                        className="control-btn step-btn"
                        onClick={stepBackward}
                        title="Step backward 100 years"
                    >
                        ⏮
                    </button>

                    <button
                        className="control-btn play-pause-btn"
                        onClick={onPlayPauseToggle}
                    >
                        {isPlaying ? '⏸' : '▶'}
                    </button>

                    <button
                        className="control-btn step-btn"
                        onClick={stepForward}
                        title="Step forward 100 years"
                    >
                        ⏭
                    </button>

                    <div className="speed-selector">
                        <label>Speed:</label>
                        {[1, 2, 5, 10].map(speed => (
                            <button
                                key={speed}
                                className={`speed-btn ${playbackSpeed === speed ? 'active' : ''}`}
                                onClick={() => setPlaybackSpeed(speed)}
                            >
                                {speed}x
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Timeline Slider */}
            <div className="timeline-slider-container">
                <div className="timeline-track">
                    {/* Reference epoch marker */}
                    <div
                        className="reference-marker"
                        style={{ left: `${((referenceEpoch - minEpoch) / (maxEpoch - minEpoch)) * 100}%` }}
                        title={`Gaia Reference (${referenceEpoch} AD)`}
                    >
                        <div className="marker-line"></div>
                        <div className="marker-label">Now</div>
                    </div>

                    {/* Slider input */}
                    <input
                        type="range"
                        min={minEpoch}
                        max={maxEpoch}
                        step="1"
                        value={localEpoch}
                        onChange={handleSliderChange}
                        className="timeline-slider"
                        style={{
                            background: `linear-gradient(to right, 
                #8b5cf6 0%, 
                #8b5cf6 ${sliderPercent}%, 
                #374151 ${sliderPercent}%, 
                #374151 100%)`
                        }}
                    />

                    {/* Epoch bookmarks */}
                    <div className="bookmarks">
                        {bookmarks.map((bookmark) => {
                            const bookmarkPercent = ((bookmark.epoch - minEpoch) / (maxEpoch - minEpoch)) * 100;
                            return (
                                <div
                                    key={bookmark.epoch}
                                    className="bookmark"
                                    style={{ left: `${bookmarkPercent}%` }}
                                    onClick={() => jumpToEpoch(bookmark.epoch)}
                                    title={`${bookmark.label} - ${bookmark.description}`}
                                >
                                    <div className="bookmark-marker"></div>
                                    <div className="bookmark-label">{bookmark.label}</div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Timeline labels */}
                <div className="timeline-labels">
                    <span className="label-start">{formatEpoch(minEpoch)}</span>
                    <span className="label-end">{formatEpoch(maxEpoch)}</span>
                </div>
            </div>
        </div>
    );
};

export default TimelineController;
