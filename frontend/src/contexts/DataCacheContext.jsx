import React, { createContext, useState, useEffect, useCallback } from 'react';
import { cacheManager } from '../utils/cacheManager';

export const DataCacheContext = createContext(null);

const CACHE_KEYS = {
    STARS: 'stars',
    DATASETS: 'datasets',
    ANOMALIES: 'anomalies',
    HARMONIZE_STATS: 'harmonize_stats'
};

export const DataCacheProvider = ({ children }) => {
    const [cache, setCache] = useState({
        stars: null,
        datasets: null,
        anomalies: null,
        harmonizeStats: null
    });

    const [cacheMetadata, setCacheMetadata] = useState({});

    // Load cache from sessionStorage on mount
    useEffect(() => {
        const loadedCache = {};
        const metadata = {};

        Object.values(CACHE_KEYS).forEach(key => {
            const cached = cacheManager.get(key);
            if (cached) {
                loadedCache[key] = cached.data;
            }
            metadata[key] = cacheManager.getMetadata(key);
        });

        if (Object.keys(loadedCache).length > 0) {
            setCache(prev => ({ ...prev, ...loadedCache }));
            setCacheMetadata(metadata);
            console.log('✅ Cache loaded:', metadata);
        }
    }, []);

    /**
     * Update cache for specific key
     */
    const updateCache = useCallback((key, data) => {
        setCache(prev => ({ ...prev, [key]: data }));
        cacheManager.set(key, data);
        
        // Update metadata
        setCacheMetadata(prev => ({
            ...prev,
            [key]: cacheManager.getMetadata(key)
        }));
    }, []);

    /**
     * Get cached data with freshness check
     */
    const getCached = useCallback((key) => {
        const cached = cacheManager.get(key);
        return cached ? { data: cached.data, fresh: cached.fresh } : null;
    }, []);

    /**
     * Invalidate specific cache entry
     */
    const invalidateCache = useCallback((key) => {
        setCache(prev => ({ ...prev, [key]: null }));
        cacheManager.remove(key);
        setCacheMetadata(prev => ({
            ...prev,
            [key]: { exists: false }
        }));
    }, []);

    /**
     * Clear all cache
     */
    const clearAllCache = useCallback(() => {
        setCache({
            stars: null,
            datasets: null,
            anomalies: null,
            harmonizeStats: null
        });
        cacheManager.clear();
        setCacheMetadata({});
        console.log('🗑️ All cache cleared');
    }, []);

    /**
     * Refresh metadata
     */
    const refreshMetadata = useCallback(() => {
        const metadata = {};
        Object.values(CACHE_KEYS).forEach(key => {
            metadata[key] = cacheManager.getMetadata(key);
        });
        setCacheMetadata(metadata);
    }, []);

    const value = {
        cache,
        cacheMetadata,
        updateCache,
        getCached,
        invalidateCache,
        clearAllCache,
        refreshMetadata,
        CACHE_KEYS
    };

    return (
        <DataCacheContext.Provider value={value}>
            {children}
        </DataCacheContext.Provider>
    );
};
