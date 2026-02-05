import React, { useState } from 'react';
import axios from 'axios';
import { Sparkles, TrendingUp, AlertCircle, Info, Lightbulb } from 'lucide-react';
import './AIResearchAssistant.css';

const AIResearchAssistant = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [aiEnabled, setAiEnabled] = useState(true);

  const exampleQueries = [
    "Which nearby stars stand out by brightness?",
    "Find stars with distinctive characteristics",
    "What objects show strongest feature deviations?",
    "Show me statistical outliers in the dataset",
    "Rank stars by proximity and brightness"
  ];

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await axios.post('http://localhost:8000/api/nl-query/query', {
        query: query,
        page: 1,
        page_size: 100,
        ai_enhanced: aiEnabled
      });

      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process query');
      console.error('Query error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getDeviationBadgeClass = (deviation_strength) => {
    if (!deviation_strength) return 'deviation-unknown';
    if (deviation_strength.includes('strong')) return 'deviation-strong';
    if (deviation_strength.includes('moderate')) return 'deviation-moderate';
    if (deviation_strength.includes('weak')) return 'deviation-weak';
    return 'deviation-unknown';
  };

  return (
    <div className="ai-research-assistant">
      <div className="assistant-header">
        <div className="header-title">
          <Sparkles className="sparkle-icon" />
          <h2>AI Research Assistant</h2>
        </div>
        <p className="header-subtitle">
          Ask questions naturally. AI ranks results by statistical deviation and explains outliers.
        </p>
      </div>

      {/* AI Toggle */}
      <div className="ai-toggle-container">
        <label className="ai-toggle">
          <input
            type="checkbox"
            checked={aiEnabled}
            onChange={(e) => setAiEnabled(e.target.checked)}
          />
          <span className="toggle-slider"></span>
          <span className="toggle-label">
            {aiEnabled ? '🧠 AI Analysis Enabled' : '📊 Standard Query Mode'}
          </span>
        </label>
        {aiEnabled && (
          <div className="ai-info">
            <Info size={16} />
            <span>AI ranks by composite deviation score (exploratory analysis only)</span>
          </div>
        )}
      </div>

      {/* Query Input */}
      <form onSubmit={handleQuery} className="query-form">
        <div className="query-input-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a research question... (e.g., 'Which stars show unusual motion?')"
            className="query-input"
            disabled={loading}
          />
          <button 
            type="submit" 
            className="query-button"
            disabled={loading || !query.trim()}
          >
            {loading ? 'Analyzing...' : 'Ask'}
          </button>
        </div>
      </form>

      {/* Example Queries */}
      <div className="example-queries">
        <span className="examples-label">Try asking:</span>
        <div className="examples-list">
          {exampleQueries.map((example, idx) => (
            <button
              key={idx}
              onClick={() => setQuery(example)}
              className="example-chip"
              disabled={loading}
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Analyzing query and processing results...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="error-banner">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {results && !loading && (
        <div className="results-container">
          {/* Query Interpretation */}
          <div className="interpretation-card">
            <h3>
              <Lightbulb size={20} />
              Query Interpretation
            </h3>
            <p className="interpretation-text">{results.explanation}</p>
            <div className="interpretation-meta">
              <span className="meta-item">Intent: <strong>{results.intent}</strong></span>
              <span className="meta-item">
                Parse Strength: <strong>{(results.confidence * 100).toFixed(0)}%</strong>
              </span>
            </div>
          </div>

          {/* AI Analysis (if enabled) */}
          {aiEnabled && results.ai_analysis && !results.ai_analysis.fallback_active && (
            <div className="ai-analysis-section">
              <div className="ai-header">
                <TrendingUp size={24} />
                <h3>AI Research Analysis</h3>
              </div>

              {/* Analysis Scope Disclaimer */}
              {results.ai_analysis.analysis_scope && (
                <div className="analysis-scope-notice">
                  <Info size={16} />
                  <span>{results.ai_analysis.analysis_scope}</span>
                </div>
              )}

              {/* Summary */}
              <div className="research-summary">
                <h4>Ranking Summary</h4>
                <p>{results.ai_analysis.research_summary}</p>
                <div className="analysis-stats">
                  <span>Analyzed: {results.ai_analysis.total_analyzed} objects</span>
                  <span>•</span>
                  <span>Showing: Top {results.ai_analysis.shown}</span>
                  <span>•</span>
                  <span>Sample Strength: {results.ai_analysis.analysis_strength}</span>
                </div>
                <p className="reasoning-text">
                  <Info size={14} />
                  {results.ai_analysis.reasoning}
                </p>
              </div>

              {/* Key Findings */}
              {results.ai_analysis.key_findings && results.ai_analysis.key_findings.length > 0 && (
                <div className="key-findings">
                  <h4>Key Research Findings</h4>
                  <div className="findings-list">
                    {results.ai_analysis.key_findings.map((finding, idx) => (
                      <div key={idx} className="finding-card">
                        <div className="finding-header">
                          <span className="finding-rank">#{idx + 1}</span>
                          <h5>{finding.object_name}</h5>
                          <span className={`deviation-badge ${getDeviationBadgeClass(finding.deviation_strength)}`}>
                            {finding.deviation_strength}
                          </span>
                        </div>
                        <p className="finding-significance">
                          <strong>Why it matters:</strong> {finding.why_it_matters}
                        </p>
                        <div className="finding-details">
                          <span>Magnitude: {finding.details.magnitude?.toFixed(2) || 'N/A'}</span>
                          <span>RA: {finding.details.ra?.toFixed(4)}°</span>
                          <span>Dec: {finding.details.dec?.toFixed(4)}°</span>
                          {finding.details.parallax && (
                            <span>Parallax: {finding.details.parallax.toFixed(2)} mas</span>
                          )}
                        </div>
                        <div className="significance-bar">
                          <div 
                            className="significance-fill"
                            style={{ width: `${finding.significance * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Fallback notification */}
          {aiEnabled && results.ai_analysis?.fallback_active && (
            <div className="fallback-notice">
              <AlertCircle size={20} />
              <div>
                <strong>AI Analysis Unavailable</strong>
                <p>{results.ai_analysis.suggestion}</p>
              </div>
            </div>
          )}

          {/* Standard Results Summary */}
          <div className="standard-results">
            <h4>All Results</h4>
            <p className="results-count">
              Found {results.total_count} objects matching your query
            </p>
            {results.results.length > 0 && (
              <div className="results-table-container">
                <table className="results-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Source ID</th>
                      <th>RA (deg)</th>
                      <th>Dec (deg)</th>
                      <th>Magnitude</th>
                      <th>Parallax (mas)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.results.slice(0, 20).map((result) => (
                      <tr key={result.id}>
                        <td>{result.id}</td>
                        <td>{result.source_id || 'N/A'}</td>
                        <td>{result.ra?.toFixed(4) || 'N/A'}</td>
                        <td>{result.dec?.toFixed(4) || 'N/A'}</td>
                        <td>{result.magnitude?.toFixed(2) || 'N/A'}</td>
                        <td>{result.parallax?.toFixed(2) || 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {results.results.length > 20 && (
                  <p className="more-results">
                    ... and {results.results.length - 20} more results
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Suggestions */}
          {results.suggestions && results.suggestions.length > 0 && (
            <div className="suggestions-section">
              <h4>Related Queries</h4>
              <div className="suggestions-list">
                {results.suggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => setQuery(suggestion)}
                    className="suggestion-button"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AIResearchAssistant;
