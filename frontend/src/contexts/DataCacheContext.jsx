import { createContext, useState, useCallback } from 'react';

export const DataCacheContext = createContext();

export const DataCacheProvider = ({ children }) => {
    const [cache, setCache] = useState({});
    const [metadata, setMetadata] = useState({});

    // Cache keys constants
    const CACHE_KEYS = {
        DATASETS: 'datasets',
        STARS: 'stars',
        ANOMALIES: 'anomalies',
        HARMONIZATION_STATS: 'harmonization_stats',
        ANALYTICS: 'analytics',
    };

    // Get cached data
    const getCached = useCallback((key) => {
        const cached = cache[key];
        if (!cached) return null;

        const meta = metadata[key];
        if (!meta) return null;

        // Check if cache is expired (default 5 minutes)
        const now = Date.now();
        const maxAge = meta.maxAge || 5 * 60 * 1000; // 5 minutes
        if (now - meta.timestamp > maxAge) {
            return null;
        }

        return cached;
    }, [cache, metadata]);

    // Update cache
    const updateCache = useCallback((key, data, maxAge = 5 * 60 * 1000) => {
        setCache(prev => ({
            ...prev,
            [key]: data
        }));
        setMetadata(prev => ({
            ...prev,
            [key]: {
                timestamp: Date.now(),
                maxAge
            }
        }));
    }, []);

    // Invalidate cache
    const invalidateCache = useCallback((key) => {
        if (key) {
            setCache(prev => {
                const newCache = { ...prev };
                delete newCache[key];
                return newCache;
            });
            setMetadata(prev => {
                const newMeta = { ...prev };
                delete newMeta[key];
                return newMeta;
            });
        } else {
            // Clear all cache
            setCache({});
            setMetadata({});
        }
    }, []);

    // Get cache metadata
    const cacheMetadata = useCallback((key) => {
        return metadata[key] || null;
    }, [metadata]);

    const value = {
        getCached,
        updateCache,
        invalidateCache,
        cacheMetadata,
        CACHE_KEYS
    };

    return (
        <DataCacheContext.Provider value={value}>
            {children}
        </DataCacheContext.Provider>
    );
};
