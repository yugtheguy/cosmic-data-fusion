import axios from 'axios';

// API Base URL - uses Vite proxy in development
const API_BASE_URL = '';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to attach the token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add a response interceptor to handle network errors with retry logic
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const config = error.config;

        // Don't retry if we've already retried or if there's no config
        if (!config || config._retry) {
            return Promise.reject(error);
        }

        // Retry on network errors (ECONNRESET, ECONNREFUSED, timeout)
        const shouldRetry = 
            error.code === 'ECONNRESET' ||
            error.code === 'ECONNREFUSED' ||
            error.message?.includes('Network Error') ||
            error.message?.includes('timeout');

        if (shouldRetry) {
            config._retry = true;
            
            // Wait 1 second before retrying
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            console.log('Retrying request after connection error...');
            return api(config);
        }

        return Promise.reject(error);
    }
);

// ============================================
// Authentication APIs
// ============================================
export const login = async (email, password) => {
    const formData = new FormData();
    formData.append('username', email); // OAuth2 expects 'username'
    formData.append('password', password);

    const response = await api.post('/auth/login', formData, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    });
    return response.data;
};

export const register = async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
};

export const getCurrentUser = async () => {
    const response = await api.get('/auth/me');
    return response.data;
};

export const updateProfile = async (userData) => {
    const response = await api.put('/auth/me', userData);
    return response.data;
};

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
    if (params.min_parallax !== undefined) body.min_parallax = params.min_parallax;
    if (params.max_parallax !== undefined) body.max_parallax = params.max_parallax;
    if (params.min_distance !== undefined) body.min_distance = params.min_distance;
    if (params.max_distance !== undefined) body.max_distance = params.max_distance;
    if (params.ra_min !== undefined) body.ra_min = params.ra_min;
    if (params.ra_max !== undefined) body.ra_max = params.ra_max;
    if (params.dec_min !== undefined) body.dec_min = params.dec_min;
    if (params.dec_max !== undefined) body.dec_max = params.dec_max;
    if (params.original_source) body.original_source = params.original_source;
    if (params.dataset_ids) body.dataset_ids = params.dataset_ids;

    const response = await api.post('/query/search', body);
    return response.data;
};

export const boxSearch = async (ra_min, ra_max, dec_min, dec_max, limit = 1000, dataset_ids = null) => {
    // GET /search/box - Bounding box search
    const params = {
        ra_min,
        ra_max,
        dec_min,
        dec_max,
        limit
    };

    // Dataset IDs must be passed as repeated query params or handled by axios serializer
    // By default axios handles array params as key[]=value, but FastAPI expects key=value&key=value
    // We can explicitly add them to URLSearchParams or let axios handle it if configured, 
    // but simpler to just pass it if using standard axios params serializer
    if (dataset_ids && dataset_ids.length > 0) {
        params.dataset_ids = dataset_ids;
    }

    const response = await api.get('/search/box', {
        params,
        paramsSerializer: {
            indexes: null // Result: dataset_ids=1&dataset_ids=2...
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

export const loadSDSSData = async () => {
    // POST /datasets/sdss/load - Load SDSS sample data
    const response = await api.post('/datasets/sdss/load');
    return response.data;
};

export const getConfigurationStatus = async () => {
    // GET /datasets/config/status - Get configuration status
    const response = await api.get('/datasets/config/status');
    return response.data;
};

export const getDatasets = async () => {
    // GET /datasets - List all datasets
    const response = await api.get('/datasets');
    return response.data;
};

export const deleteDataset = async (datasetId) => {
    // DELETE /datasets/{dataset_id} - Delete dataset
    await api.delete(`/datasets/${datasetId}`);
};

// ============================================
// Ingestion APIs
// ============================================
export const uploadData = async (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    // Detect file type from extension
    const fileName = file.name.toLowerCase();
    let endpoint = '/ingest/csv'; // default
    
    if (fileName.endsWith('.fits') || fileName.endsWith('.fit') || fileName.endsWith('.fits.gz')) {
        endpoint = '/ingest/fits';
    } else if (fileName.endsWith('.csv')) {
        endpoint = '/ingest/csv';
    }

    const response = await api.post(endpoint, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        onUploadProgress,
    });
    return response.data;
};

export const previewData = async (file, adapterType = 'auto', limit = 20) => {
    // POST /ingest/preview
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/ingest/preview', formData, {
        params: { adapter_type: adapterType, limit },
        headers: {
            'Content-Type': 'multipart/form-data',
        }
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
