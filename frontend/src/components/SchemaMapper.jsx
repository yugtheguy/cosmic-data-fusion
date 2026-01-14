import React, { useState, useEffect } from 'react';
import {
    UploadCloud,
    FileText,
    ArrowRight,
    CheckCircle,
    AlertTriangle,
    Database,
    Table,
    XCircle
} from 'lucide-react';
import { suggestMapping, ingestCSV } from '../services/api';
import './SchemaMapper.css';

const TARGET_FIELDS = [
    { value: 'ra', label: 'Right Ascension (deg)', required: true },
    { value: 'dec', label: 'Declination (deg)', required: true },
    { value: 'parallax', label: 'Parallax (mas)' },
    { value: 'pmra', label: 'Proper Motion RA (mas/yr)' },
    { value: 'pmdec', label: 'Proper Motion Dec (mas/yr)' },
    { value: 'mag', label: 'Magnitude (Brightness)' },
    { value: 'name', label: 'Object Name/ID' },
    { value: 'epoch', label: 'Epoch (year)' },
    { value: 'radial_velocity', label: 'Radial Velocity (km/s)' }
];

function SchemaMapper() {
    const [step, setStep] = useState('upload'); // upload, map, ingest, result
    const [file, setFile] = useState(null);
    const [headers, setHeaders] = useState([]);
    const [mapping, setMapping] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);
    const [progress, setProgress] = useState(0);

    // Step 1: Handle File Selection
    const handleFileSelect = (e) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0];
            setFile(selectedFile);
            parseHeaders(selectedFile);
        }
    };

    const parseHeaders = (file) => {
        setLoading(true);
        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const text = e.target.result;
                const firstLine = text.split('\n')[0];
                // Simple CSV parser for headers
                const fileHeaders = firstLine.split(',').map(h => h.trim().replace(/^"|"$/g, ''));
                setHeaders(fileHeaders);

                // Get suggestions from backend
                const suggestions = await suggestMapping(fileHeaders);

                // mappings is already {sourceCol: targetCol} object
                setMapping(suggestions.mappings || {});
                setStep('map');
            } catch (err) {
                console.error("Analysis failed:", err);
                setError(`Failed to analyze file: ${err.response?.data?.detail || err.message}`);
            } finally {
                setLoading(false);
            }
        };
        reader.readAsText(file.slice(0, 5000)); // Read first 5KB
    };

    // Step 2: Handle Mapping Changes
    const handleMappingChange = (sourceCol, targetCol) => {
        setMapping(prev => {
            const newMap = { ...prev };
            if (targetCol === '') {
                delete newMap[sourceCol];
            } else {
                newMap[sourceCol] = targetCol;
            }
            return newMap;
        });
    };

    const validateMapping = () => {
        const values = Object.values(mapping);
        const hasRa = values.includes('ra');
        const hasDec = values.includes('dec');
        return hasRa && hasDec;
    };

    // Step 3: Ingest
    const handleIngest = async () => {
        setStep('ingest');
        setLoading(true);
        setProgress(0);

        try {
            const response = await ingestCSV(file, mapping, (event) => {
                const percent = Math.round((event.loaded * 100) / event.total);
                setProgress(percent);
            });
            setResult(response);
            setStep('result');
        } catch (err) {
            setError(err.response?.data?.detail?.message || "Ingestion failed.");
            setStep('map'); // Go back to map on error
        } finally {
            setLoading(false);
        }
    };

    const reset = () => {
        setStep('upload');
        setFile(null);
        setHeaders([]);
        setMapping({});
        setResult(null);
        setError(null);
    };

    // Render Steps
    return (
        <div className="schema-mapper">
            <div className="mapper-header">
                <h2>Schema Unification</h2>
                <p>Map your file's columns to the COSMIC Standard Model.</p>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="error-banner" style={{ marginBottom: '1rem' }}>
                    <AlertTriangle size={18} />
                    <span>{error}</span>
                    <button onClick={() => setError(null)}><XCircle size={16} /></button>
                </div>
            )}

            {/* Step 1: Upload */}
            {step === 'upload' && (
                <div className="mapper-card">
                    <div className="drop-zone" onClick={() => document.getElementById('mapper-upload').click()}>
                        <input type="file" id="mapper-upload" accept=".csv,.txt" hidden onChange={handleFileSelect} />
                        <UploadCloud size={48} className="upload-icon" />
                        <h3>Select CSV File to Map</h3>
                        <p>We'll analyze the headers to suggest a mapping.</p>
                    </div>
                </div>
            )}

            {/* Step 2: Map Columns */}
            {step === 'map' && (
                <div className="mapper-card">
                    <div className="file-summary">
                        <FileText size={20} />
                        <span>{file?.name}</span>
                        <span className="badge">{(file?.size / 1024).toFixed(1)} KB</span>
                    </div>

                    <div className="mapping-grid">
                        <div className="grid-header">
                            <span>Source Column</span>
                            <ArrowRight size={16} />
                            <span>Target Field</span>
                        </div>

                        {headers.map(header => (
                            <div key={header} className={`mapping-row ${mapping[header] ? 'mapped' : ''}`}>
                                <div className="source-col" title={header}>{header}</div>
                                <ArrowRight size={16} className="arrow-icon" />
                                <select
                                    value={mapping[header] || ''}
                                    onChange={(e) => handleMappingChange(header, e.target.value)}
                                    className="target-select"
                                >
                                    <option value="">-- Ignore --</option>
                                    {TARGET_FIELDS.map(field => (
                                        <option key={field.value} value={field.value}>
                                            {field.label} {field.required ? '*' : ''}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        ))}
                    </div>

                    <div className="mapping-actions">
                        <div className="validation-status">
                            {validateMapping() ? (
                                <span className="text-success"><CheckCircle size={16} /> Ready to Ingest</span>
                            ) : (
                                <span className="text-warning"><AlertTriangle size={16} /> RA and Dec are required</span>
                            )}
                        </div>
                        <button
                            className="primary-btn"
                            disabled={!validateMapping() || loading}
                            onClick={handleIngest}
                        >
                            {loading ? 'Processing...' : 'Ingest Data'}
                        </button>
                    </div>
                </div>
            )}

            {/* Step 3: Ingesting */}
            {step === 'ingest' && (
                <div className="mapper-card centered">
                    <Database size={48} className="pulse-icon" />
                    <h3>Ingesting Mapping Data...</h3>
                    <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                    </div>
                    <p>{progress}% Complete</p>
                </div>
            )}

            {/* Step 4: Result */}
            {step === 'result' && (
                <div className="mapper-card centered">
                    <CheckCircle size={64} className="success-icon" />
                    <h3>Ingestion Successful!</h3>
                    <div className="result-stats">
                        <div className="stat-box">
                            <span className="label">Total</span>
                            <span className="value">{result?.counts?.total ?? result?.total ?? result?.records_processed ?? '–'}</span>
                        </div>
                        <div className="stat-box">
                            <span className="label">Success</span>
                            <span className="value highlight">{result?.counts?.success ?? result?.success ?? result?.records_ingested ?? '–'}</span>
                        </div>
                        <div className="stat-box">
                            <span className="label">Dataset ID</span>
                            <span className="value small">{(result?.dataset_id || 'N/A').substring(0, 12)}...</span>
                        </div>
                    </div>
                    <button className="secondary-btn" onClick={reset}>Map Another File</button>
                </div>
            )}
        </div>
    );
}

export default SchemaMapper;
