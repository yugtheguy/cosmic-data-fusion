import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Plot from 'react-plotly.js';
import { 
    Target, 
    Search, 
    AlertCircle, 
    Loader2,
    ArrowLeft,
    Info,
    TrendingDown
} from 'lucide-react';
import axios from 'axios';
import './PlanetHunter.css';

function PlanetHunter() {
    const navigate = useNavigate();
    
    // Safe state initialization
    const [ticId, setTicId] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);
    const [plotData, setPlotData] = useState(null);

    // Handle form submission
    const handleSearch = async (e) => {
        e.preventDefault();
        
        // Validation
        if (!ticId || ticId.trim() === '') {
            setError('Please enter a TIC ID');
            return;
        }

        setIsLoading(true);
        setError(null);
        setResult(null);
        setPlotData(null);

        try {
            // Call the API endpoint
            const response = await axios.post(
                `http://localhost:8000/analysis/planet-hunt/${ticId.trim()}`,
                {},
                { timeout: 30000 } // 30 second timeout
            );

            const data = response.data;
            
            // Defensive: check if data exists
            if (!data) {
                throw new Error('No data returned from server');
            }

            setResult(data);

            // Defensive: Only create plot data if transit data exists
            if (data.transits && Array.isArray(data.transits) && data.transits.length > 0) {
                // Extract times and depths safely
                const times = data.transits.map(t => t.time || 0);
                const depths = data.transits.map(t => t.depth || 0);

                setPlotData({
                    x: times,
                    y: depths,
                    rawData: data.transits
                });
            }

        } catch (err) {
            console.error('Planet hunt error:', err);
            
            // User-friendly error messages
            if (err.code === 'ECONNABORTED') {
                setError('Request timed out. The server may be processing a large dataset.');
            } else if (err.response) {
                setError(err.response.data?.detail || `Server error: ${err.response.status}`);
            } else if (err.request) {
                setError('Cannot reach server. Please check if the backend is running.');
            } else {
                setError(err.message || 'An unexpected error occurred');
            }
        } finally {
            setIsLoading(false);
        }
    };

    // Reset form
    const handleReset = () => {
        setTicId('');
        setResult(null);
        setPlotData(null);
        setError(null);
    };

    return (
        <div className="planet-hunter-page">
            {/* Header */}
            <header className="page-header">
                <button 
                    className="back-button" 
                    onClick={() => navigate('/dashboard')}
                    title="Back to Dashboard"
                >
                    <ArrowLeft size={20} />
                </button>
                <div className="header-content">
                    <div className="header-icon">
                        <Target size={28} />
                    </div>
                    <div className="header-text">
                        <h1>Planet Hunter</h1>
                        <p>Search for exoplanet transit signals in TESS light curves</p>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="planet-hunter-content">
                {/* Search Form */}
                <div className="search-card">
                    <div className="card-header">
                        <Search size={20} />
                        <h2>Search by TIC ID</h2>
                    </div>
                    
                    <form onSubmit={handleSearch} className="search-form">
                        <div className="input-group">
                            <label htmlFor="ticId">TESS Input Catalog ID</label>
                            <input
                                id="ticId"
                                type="text"
                                placeholder="e.g., 307210830"
                                value={ticId}
                                onChange={(e) => setTicId(e.target.value)}
                                disabled={isLoading}
                                className="tic-input"
                            />
                        </div>

                        <div className="button-group">
                            <button 
                                type="submit" 
                                className="search-button"
                                disabled={isLoading || !ticId.trim()}
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 size={18} className="spinning" />
                                        Analyzing...
                                    </>
                                ) : (
                                    <>
                                        <Search size={18} />
                                        Hunt Planets
                                    </>
                                )}
                            </button>
                            
                            {(result || error) && (
                                <button 
                                    type="button" 
                                    className="reset-button"
                                    onClick={handleReset}
                                    disabled={isLoading}
                                >
                                    Clear
                                </button>
                            )}
                        </div>
                    </form>

                    {/* Info Box */}
                    <div className="info-box">
                        <Info size={16} />
                        <span>Enter a TIC ID to search for periodic transit signals that may indicate exoplanets</span>
                    </div>
                </div>

                {/* Error Display */}
                {error && (
                    <div className="error-card">
                        <AlertCircle size={24} />
                        <div className="error-content">
                            <h3>Analysis Failed</h3>
                            <p>{error}</p>
                        </div>
                    </div>
                )}

                {/* Results Display */}
                {result && !error && (
                    <div className="results-section">
                        {/* Summary Card */}
                        <div className="summary-card">
                            <div className="card-header">
                                <TrendingDown size={20} />
                                <h2>Transit Analysis Summary</h2>
                            </div>
                            
                            <div className="summary-grid">
                                <div className="summary-item">
                                    <span className="summary-label">TIC ID</span>
                                    <span className="summary-value">{result.tic_id || 'N/A'}</span>
                                </div>
                                <div className="summary-item">
                                    <span className="summary-label">Transits Detected</span>
                                    <span className="summary-value">
                                        {result.transits ? result.transits.length : 0}
                                    </span>
                                </div>
                                <div className="summary-item">
                                    <span className="summary-label">Period (days)</span>
                                    <span className="summary-value">
                                        {result.period ? result.period.toFixed(4) : 'N/A'}
                                    </span>
                                </div>
                                <div className="summary-item">
                                    <span className="summary-label">Transit Depth</span>
                                    <span className="summary-value">
                                        {result.depth ? `${(result.depth * 100).toFixed(3)}%` : 'N/A'}
                                    </span>
                                </div>
                            </div>

                            {result.message && (
                                <div className="result-message">
                                    <p>{result.message}</p>
                                </div>
                            )}
                        </div>

                        {/* Plot Card - DEFENSIVE RENDERING */}
                        {plotData && plotData.x && plotData.y && plotData.x.length > 0 ? (
                            <div className="plot-card">
                                <div className="card-header">
                                    <h2>Transit Light Curve</h2>
                                </div>
                                
                                <div className="plot-container">
                                    <Plot
                                        data={[
                                            {
                                                x: plotData.x,
                                                y: plotData.y,
                                                type: 'scatter',
                                                mode: 'lines+markers',
                                                marker: { 
                                                    color: '#e8a87c',
                                                    size: 6
                                                },
                                                line: {
                                                    color: '#e8a87c',
                                                    width: 2
                                                },
                                                name: 'Transit Signal'
                                            }
                                        ]}
                                        layout={{
                                            title: 'Phase-Folded Light Curve',
                                            xaxis: { 
                                                title: 'Time (BJD)',
                                                gridcolor: '#2a2a2a',
                                                color: '#e5e5e5'
                                            },
                                            yaxis: { 
                                                title: 'Relative Flux',
                                                gridcolor: '#2a2a2a',
                                                color: '#e5e5e5'
                                            },
                                            paper_bgcolor: 'rgba(26, 26, 26, 0.95)',
                                            plot_bgcolor: 'rgba(26, 26, 26, 0.95)',
                                            font: { color: '#e5e5e5' },
                                            hovermode: 'closest',
                                            margin: { t: 50, r: 30, b: 50, l: 60 }
                                        }}
                                        config={{
                                            responsive: true,
                                            displayModeBar: true,
                                            displaylogo: false
                                        }}
                                        style={{ width: '100%', height: '500px' }}
                                    />
                                </div>

                                {/* Transit Details Table */}
                                {plotData.rawData && plotData.rawData.length > 0 && (
                                    <div className="transit-table">
                                        <h3>Individual Transits</h3>
                                        <div className="table-wrapper">
                                            <table>
                                                <thead>
                                                    <tr>
                                                        <th>#</th>
                                                        <th>Time (BJD)</th>
                                                        <th>Depth</th>
                                                        <th>Duration (hrs)</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {plotData.rawData.map((transit, idx) => (
                                                        <tr key={idx}>
                                                            <td>{idx + 1}</td>
                                                            <td>{transit.time ? transit.time.toFixed(5) : 'N/A'}</td>
                                                            <td>{transit.depth ? (transit.depth * 100).toFixed(3) + '%' : 'N/A'}</td>
                                                            <td>{transit.duration ? (transit.duration * 24).toFixed(2) : 'N/A'}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : result.transits && result.transits.length === 0 ? (
                            <div className="no-data-card">
                                <Info size={24} />
                                <p>No transits detected in this light curve</p>
                            </div>
                        ) : (
                            <div className="no-data-card">
                                <AlertCircle size={24} />
                                <p>No plot data available</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default PlanetHunter;
