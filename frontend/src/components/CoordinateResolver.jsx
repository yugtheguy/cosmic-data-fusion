import { useState } from 'react';
import { Search, HelpCircle, Check, X, Loader, Lightbulb } from 'lucide-react';
import axios from 'axios';
import Sidebar from './Sidebar';
import './CoordinateResolver.css';

/**
 * Coordinate Resolver Component
 * 
 * Flexible coordinate search supporting multiple astronomical notation formats.
 * Original implementation for COSMIC Data Fusion platform.
 */
function CoordinateResolver() {
    const [coordinateInput, setCoordinateInput] = useState('');
    const [radius, setRadius] = useState(2.0);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);
    const [showHelp, setShowHelp] = useState(false);

    const exampleFormats = [
        { label: 'Decimal Degrees', example: '350.123456 -17.33333' },
        { label: 'Sexagesimal', example: '20 54 05.689 +37 01 17.38' },
        { label: 'HMS/DMS', example: '10:12:45.3 -45:17:50' },
        { label: 'Mixed Notation', example: '15h17m-11d10m' },
        { label: 'Compact Format', example: '15h17+89d15' },
        { label: 'Degree Suffix', example: '275d11m15.6954s +17d59m59.876s' },
        { label: 'Hybrid', example: '12.34567h -17.87654d' },
    ];

    const handleSearch = async () => {
        if (!coordinateInput.trim()) {
            setError('Please enter coordinates');
            return;
        }

        setLoading(true);
        setError(null);
        setResults(null);

        try {
            const response = await axios.post('/search/coordinate', null, {
                params: {
                    coordinates: coordinateInput.trim(),
                    radius: radius,
                    limit: 1000
                }
            });

            setResults(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Search failed. Please check your coordinate format.');
        } finally {
            setLoading(false);
        }
    };

    const handleExampleClick = (example) => {
        setCoordinateInput(example);
        setError(null);
        setResults(null);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !loading) {
            handleSearch();
        }
    };

    return (
        <div className="coordinate-resolver-page-container">
            <Sidebar activeTab="coordinate-resolver" />
            <div className="coordinate-resolver-content-wrapper">
                <div className="coordinate-resolver">
                    <div className="resolver-header">
                        <h2><Search size={28} /> Coordinate Resolver</h2>
                        <p className="resolver-subtitle">
                            Search the stellar catalog using flexible coordinate formats
                        </p>
                    </div>

                    {/* Main Search Interface */}
                    <div className="search-panel">
                        <div className="search-row">
                            <div className="coordinate-input-group">
                                <label htmlFor="coord-input">
                                    Enter Coordinates:
                                    <button
                                        className="help-button"
                                        onClick={() => setShowHelp(!showHelp)}
                                        title="Show supported formats"
                                    >
                                        <HelpCircle size={16} />
                                    </button>
                                </label>
                                <input
                                    id="coord-input"
                                    type="text"
                                    className="coordinate-input"
                                    placeholder="e.g., 20 54 05.689 +37 01 17.38"
                                    value={coordinateInput}
                                    onChange={(e) => setCoordinateInput(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    disabled={loading}
                                />
                            </div>

                            <div className="radius-input-group">
                                <label htmlFor="radius-input">
                                    Radius (arcmin):
                                </label>
                                <input
                                    id="radius-input"
                                    type="number"
                                    className="radius-input"
                                    min="0.1"
                                    max="180"
                                    step="0.5"
                                    value={radius}
                                    onChange={(e) => setRadius(parseFloat(e.target.value))}
                                    disabled={loading}
                                />
                            </div>

                            <button
                                className="search-button"
                                onClick={handleSearch}
                                disabled={loading || !coordinateInput.trim()}
                            >
                                {loading ? (
                                    <>
                                        <Loader size={18} className="spinner" />
                                        Searching...
                                    </>
                                ) : (
                                    <>
                                        <Search size={18} />
                                        Search
                                    </>
                                )}
                            </button>
                        </div>

                        {/* Format Help Panel */}
                        {showHelp && (
                            <div className="format-help">
                                <h4>Supported Coordinate Formats:</h4>
                                <div className="format-examples">
                                    {exampleFormats.map((format, idx) => (
                                        <div key={idx} className="format-item">
                                            <span className="format-label">{format.label}:</span>
                                            <code
                                                className="format-example"
                                                onClick={() => handleExampleClick(format.example)}
                                                title="Click to use this example"
                                            >
                                                {format.example}
                                            </code>
                                        </div>
                                    ))}
                                </div>
                                <p className="format-note">
                                    <Lightbulb size={16} /> <strong>Tip:</strong> Click any example to try it instantly!
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Error Display */}
                    {error && (
                        <div className="error-banner">
                            <X size={18} />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Results Display */}
                    {results && (
                        <div className="results-panel">
                            <div className="results-header">
                                <div className="results-summary">
                                    <Check size={20} className="success-icon" />
                                    <h3>Found {results.total_count} {results.total_count === 1 ? 'star' : 'stars'}</h3>
                                </div>
                                <div className="parsed-coords">
                                    <span className="coord-label">Parsed Coordinates:</span>
                                    <span className="coord-value">
                                        RA = {results.parsed_coordinates?.ra_deg?.toFixed(6)}°
                                    </span>
                                    <span className="coord-value">
                                        Dec = {results.parsed_coordinates?.dec_deg?.toFixed(6)}°
                                    </span>
                                    <span className="coord-note">
                                        (Search radius: {results.search_params?.radius_arcmin} arcmin)
                                    </span>
                                </div>
                            </div>

                            {results.total_count > 0 ? (
                                <div className="results-table-container">
                                    <table className="results-table">
                                        <thead>
                                            <tr>
                                                <th>Source ID</th>
                                                <th>RA (°)</th>
                                                <th>Dec (°)</th>
                                                <th>Magnitude</th>
                                                <th>Parallax (mas)</th>
                                                <th>Distance (pc)</th>
                                                <th>Source</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {results.records.map((star, idx) => (
                                                <tr key={idx}>
                                                    <td className="monospace">{star.source_id || 'N/A'}</td>
                                                    <td>{star.ra_deg?.toFixed(6)}</td>
                                                    <td>{star.dec_deg?.toFixed(6)}</td>
                                                    <td>{star.brightness_mag?.toFixed(2) || 'N/A'}</td>
                                                    <td>{star.parallax_mas?.toFixed(3) || 'N/A'}</td>
                                                    <td>{star.distance_pc?.toFixed(1) || 'N/A'}</td>
                                                    <td className="source-badge">{star.original_source || 'Unknown'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="no-results">
                                    <p>No stars found within the search radius.</p>
                                    <p className="suggestion">Try increasing the search radius or using different coordinates.</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default CoordinateResolver;
