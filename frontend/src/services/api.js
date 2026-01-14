import axios from 'axios';

// API Base URL - uses Vite proxy in development
const API_BASE_URL = '';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// ============================================
// Health Check
// ============================================
export const checkHealth = async () => {
    const response = await api.get('/health');
    return response.data;
};

// ============================================
// Star Query APIs
// ============================================
export const searchStars = async (params = {}) => {
    // POST /query/search - Advanced multi-filter search
    const body = {
        limit: params.limit || 1000,
        offset: params.offset || 0,
    };

    // Only add optional params if they have values
    if (params.min_mag !== undefined) body.min_mag = params.min_mag;
    if (params.max_mag !== undefined) body.max_mag = params.max_mag;
    if (params.ra_min !== undefined) body.ra_min = params.ra_min;
    if (params.ra_max !== undefined) body.ra_max = params.ra_max;
    if (params.dec_min !== undefined) body.dec_min = params.dec_min;
    if (params.dec_max !== undefined) body.dec_max = params.dec_max;
    if (params.original_source) body.original_source = params.original_source;

    const response = await api.post('/query/search', body);
    return response.data;
};

export const boxSearch = async (ra_min, ra_max, dec_min, dec_max, limit = 1000) => {
    // GET /search/box - Bounding box search
    const response = await api.get('/search/box', {
        params: {
            ra_min,
            ra_max,
            dec_min,
            dec_max,
            limit
        }
    });
    return response.data;
};

export const coneSearch = async (ra, dec, radius, limit = 1000) => {
    // GET /search/cone - Cone search around a point
    const response = await api.get('/search/cone', {
        params: {
            ra,
            dec,
            radius,
            limit
        }
    });
    return response.data;
};

export const getStarById = async (starId) => {
    // GET /search/star/{id} - Get single star by ID
    const response = await api.get(`/search/star/${starId}`);
    return response.data;
};

export const getNearbyStars = async (starId, radius = 0.5, limit = 50) => {
    // GET /search/star/{id}/nearby - Find nearby stars
    const response = await api.get(`/search/star/${starId}/nearby`, {
        params: { radius, limit }
    });
    return response.data;
};

// ============================================
// AI Discovery APIs
// ============================================
export const detectAnomalies = async (contamination = 0.05) => {
    // POST /ai/anomalies - Detect anomalous stars
    const response = await api.post('/ai/anomalies', { contamination });
    return response.data;
};

export const findClusters = async (eps = 0.5, min_samples = 5) => {
    // POST /ai/clusters - Find spatial clusters with DBSCAN
    const response = await api.post('/ai/clusters', { eps, min_samples });
    return response.data;
};

export const checkStarAnomaly = async (starId) => {
    // GET /ai/anomaly-check/{star_id} - Check if star is an anomaly
    const response = await api.get(`/ai/anomaly-check/${starId}`);
    return response.data;
};

export const refreshStarFromGaia = async (starId) => {
    // POST /search/star/{id}/refresh-gaia - Refresh data from ESA Gaia Archive
    const response = await api.post(`/search/star/${starId}/refresh-gaia`);
    return response.data;
};

// ============================================
// Harmonization APIs
// ============================================
export const getHarmonizationStats = async () => {
    // GET /harmonize/stats - Cross-match statistics
    const response = await api.get('/harmonize/stats');
    return response.data;
};

export const runCrossMatch = async (radius_arcsec = 2.0, reset_existing = false) => {
    // POST /harmonize/cross-match - Run cross-matching
    const response = await api.post('/harmonize/cross-match', { radius_arcsec, reset_existing });
    return response.data;
};

export const validateCoordinates = async () => {
    // POST /harmonize/validate - Validate coordinate consistency
    const response = await api.post('/harmonize/validate');
    return response.data;
};

export const getFusionGroup = async (groupId) => {
    // GET /harmonize/fusion-group/{group_id} - Get stars in a fusion group
    const response = await api.get(`/harmonize/fusion-group/${groupId}`);
    return response.data;
};

export const getFusionGroups = async (limit = 100) => {
    // GET /harmonize/groups - List fusion groups
    const response = await api.get('/harmonize/groups', { params: { limit } });
    return response.data;
};

// ============================================
// Data Export APIs
// ============================================
export const exportData = async (format = 'json') => {
    // GET /query/export - Export data in various formats
    const response = await api.get('/query/export', {
        params: { format },
        responseType: format === 'json' ? 'json' : 'blob',
    });
    return response.data;
};

export const downloadExport = async (format = 'csv') => {
    // Download file directly
    const response = await api.get('/query/export', {
        params: { format },
        responseType: 'blob',
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `cosmic_export.${format === 'votable' ? 'vot' : format}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
};

// ============================================
// Dataset APIs
// ============================================
export const loadGaiaData = async () => {
    // POST /datasets/gaia/load - Load Gaia sample data
    const response = await api.post('/datasets/gaia/load');
    return response.data;
};

// ============================================
// Ingestion APIs
// ============================================
export const uploadData = async (file, onUploadProgress) => {
    // POST /ingest/auto - Auto-detect and ingest file
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/ingest/auto', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        onUploadProgress,
    });
    return response.data;
};

export const ingestCSV = async (file, mapping, onUploadProgress) => {
    // POST /ingest/csv - Ingest CSV with mapping
    const formData = new FormData();
    formData.append('file', file);
    if (mapping) {
        formData.append('column_mapping', JSON.stringify(mapping));
    }

    const response = await api.post('/ingest/csv', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        onUploadProgress,
    });
    return response.data;
};

// ============================================
// Schema Mapper APIs
// ============================================
export const suggestMapping = async (columns, existingMapping = {}) => {
    const response = await api.post('/api/mapper/suggest/headers', {
        columns,
        existing_mapping: existingMapping
    });
    return response.data;
};

export const previewMapping = async (filePath) => {
    const response = await api.post('/api/mapper/preview', {
        file_path: filePath,
        sample_size: 5
    });
    return response.data;
};

export const validateMapping = async (mapping) => {
    const response = await api.post('/api/mapper/validate', {
        mapping,
        min_confidence: 0.0
    });
    return response.data;
};

export const applyMapping = async (datasetId, mapping) => {
    const response = await api.post('/api/mapper/apply', {
        dataset_id: datasetId,
        mapping
    });
    return response.data;
};

export default api;
