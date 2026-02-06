import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, CheckCircle, XCircle, AlertCircle, Map } from 'lucide-react';
import { uploadData, previewData } from '../services/api';



// Upload View Component
const UploadView = ({ onUploadSuccess }) => {
    const navigate = useNavigate();
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [previewResult, setPreviewResult] = useState(null);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const onDrop = useCallback(acceptedFiles => {
        setFiles(acceptedFiles);
        setError(null);
        setResult(null);
        setPreviewResult(null);

        // Auto-preview logic
        if (acceptedFiles.length > 0) {
            handlePreview(acceptedFiles[0]);
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'text/csv': ['.csv'],
            'application/json': ['.json'],
            'application/x-fits': ['.fits']
        },
        maxFiles: 1
    });

    const handlePreview = async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        try {
            setUploading(true);
            // Assuming previewData exists in API service
            const response = await previewData(formData);
            setPreviewResult(response);
            setUploading(false);
        } catch (err) {
            console.error('Preview failed:', err);
            setError(err.response?.data?.detail || 'Failed to generate preview. Please check file format.');
            setUploading(false);
        }
    };

    const handleUpload = async () => {
        if (files.length === 0) return;

        setUploading(true);
        setError(null);
        setResult(null);

        const formData = new FormData();
        formData.append('file', files[0]);

        try {
            const response = await uploadData(formData);
            setResult(response);
            if (onUploadSuccess) {
                onUploadSuccess();
            }
        } catch (err) {
            console.error('Upload failed:', err);
            setError(err.response?.data?.detail || 'Upload failed. Please try again.');
        } finally {
            setUploading(false);
        }
    };

    const resetUpload = () => {
        setFiles([]);
        setResult(null);
        setPreviewResult(null);
        setError(null);
    };

    return (
        <div className="upload-view">
            {!result ? (
                <div className="upload-container">
                    <div className="upload-header-text">
                        <h3>Ingest New Dataset</h3>
                        <p>Upload CSV, JSON, or FITS files to integrate with the catalog.</p>
                    </div>

                    {!previewResult ? (
                        <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
                            <input {...getInputProps()} />
                            <div className="dropzone-content">
                                <UploadCloud size={48} className="upload-icon" />
                                {isDragActive ? (
                                    <p>Drop the file here...</p>
                                ) : (
                                    <>
                                        <p className="drop-text">Drag & drop files here, or click to select</p>
                                        <p className="file-types">Supports CSV, JSON, FITS (VOTable)</p>
                                    </>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="preview-file-card">
                            <div className="file-info">
                                <FileText size={24} />
                                <div>
                                    <span className="file-name">{files[0].name}</span>
                                    <span className="file-size">{(files[0].size / 1024).toFixed(1)} KB</span>
                                </div>
                            </div>
                            <button className="change-file-btn" onClick={resetUpload}>
                                <XCircle size={18} />
                            </button>
                        </div>
                    )}

                    {previewResult && (
                        <div className="preview-results glass-panel" style={{ padding: '1.5rem', marginTop: '1rem' }}>
                            <div className="preview-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                                <h3>Data Preview</h3>
                                <div className="preview-stats" style={{ display: 'flex', gap: '1rem' }}>
                                    <span style={{ color: '#4ade80' }}>✓ {previewResult.valid_count} Valid</span>
                                    <span style={{ color: '#f87171' }}>⚠ {previewResult.invalid_count} Invalid</span>
                                </div>
                            </div>

                            <div className="table-wrapper" style={{ maxHeight: '300px', overflow: 'auto', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                                    <thead>
                                        <tr style={{ background: 'rgba(255,255,255,0.05)', textAlign: 'left' }}>
                                            {['Source ID', 'RA (°)', 'Dec (°)', 'Mag', 'Distance (pc)'].map(h => (
                                                <th key={h} style={{ padding: '0.75rem' }}>{h}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {previewResult.samples.map((row, i) => (
                                            <tr key={i} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                                                <td style={{ padding: '0.5rem 0.75rem' }}>{row.source_id}</td>
                                                <td style={{ padding: '0.5rem 0.75rem' }}>{row.ra_deg?.toFixed(5)}</td>
                                                <td style={{ padding: '0.5rem 0.75rem' }}>{row.dec_deg?.toFixed(5)}</td>
                                                <td style={{ padding: '0.5rem 0.75rem' }}>{row.brightness_mag?.toFixed(2)}</td>
                                                <td style={{ padding: '0.5rem 0.75rem' }}>{row.distance_pc?.toFixed(1) || '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {previewResult.sample_errors && previewResult.sample_errors.length > 0 && (
                                <div className="preview-errors" style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                                    <h4 style={{ color: '#f87171', margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>Validation Issues Detected</h4>
                                    <ul style={{ margin: 0, paddingLeft: '1.5rem', fontSize: '0.85rem', color: '#fca5a5' }}>
                                        {previewResult.sample_errors.slice(0, 3).map((err, i) => (
                                            <li key={i}>{err}</li>
                                        ))}
                                        {previewResult.sample_errors.length > 3 && <li>...and {previewResult.sample_errors.length - 3} more</li>}
                                    </ul>
                                </div>
                            )}

                            <div className="preview-actions" style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', justifyContent: 'flex-end' }}>
                                <button
                                    onClick={resetUpload}
                                    style={{
                                        background: 'transparent',
                                        border: '1px solid rgba(255,255,255,0.2)',
                                        color: '#aaa',
                                        padding: '0.75rem 1.5rem',
                                        borderRadius: '8px',
                                        cursor: 'pointer'
                                    }}
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleUpload}
                                    disabled={uploading}
                                    style={{
                                        background: 'linear-gradient(135deg, #e8a87c 0%, #d4683a 100%)',
                                        color: 'white',
                                        border: 'none',
                                        padding: '0.75rem 2rem',
                                        borderRadius: '8px',
                                        fontWeight: '600',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.5rem'
                                    }}
                                >
                                    {uploading ? 'Ingesting...' : 'Confirm & Ingest'}
                                    {!uploading && <CheckCircle size={18} />}
                                </button>
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="upload-error">
                            <AlertCircle size={20} />
                            <span>{error}</span>
                        </div>
                    )}
                </div>
            ) : (
                <div className="upload-result">
                    <div className="result-card">
                        <CheckCircle size={64} className="success-icon" />
                        <h3>Ingestion Successful!</h3>
                        <p>{result.message}</p>

                        <div className="result-stats">
                            <div className="result-stat">
                                <span className="label">Total Records</span>
                                <span className="value">{result.counts?.total || result.ingested_count + result.failed_count || 0}</span>
                            </div>
                            <div className="result-stat">
                                <span className="label">Successfully Ingested</span>
                                <span className="value highlight">{result.ingested_count || result.counts?.success || 0}</span>
                            </div>
                            <div className="result-stat">
                                <span className="label">Failed/Skipped</span>
                                <span className="value warning">{result.failed_count || result.counts?.failed || 0}</span>
                            </div>
                        </div>

                        <div className="result-details">
                            <h4>Dataset Details</h4>
                            <div className="detail-grid">
                                <div className="detail-item">
                                    <span>Dataset ID:</span>
                                    <code>{result.dataset_id}</code>
                                </div>
                                <div className="detail-item">
                                    <span>Source:</span>
                                    <code>{files[0]?.name}</code>
                                </div>
                            </div>
                        </div>

                        <div className="action-buttons" style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                            <button
                                className="visualize-btn"
                                onClick={() => navigate('/skymap')}
                                style={{
                                    background: 'linear-gradient(135deg, #e8a87c 0%, #d4683a 100%)',
                                    color: 'white',
                                    border: 'none',
                                    padding: '0.75rem 1.5rem',
                                    borderRadius: '8px',
                                    fontWeight: '600',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    flex: 1,
                                    justifyContent: 'center'
                                }}
                            >
                                <Map size={18} />
                                Visualize in Sky Map
                            </button>
                            <button
                                className="reset-btn"
                                onClick={resetUpload}
                                style={{ flex: 1 }}
                            >
                                Upload Another File
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UploadView;
