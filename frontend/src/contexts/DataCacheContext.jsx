import { createContext, useContext, useState, useCallback } from 'react';

const DataCacheContext = createContext(null);

// Cache TTL: 5 minutes
const CACHE_TTL = 5 * 60 * 1000;

export const CACHE_KEYS = {
    STAR_DATA: 'starData',
    FILTERS: 'filters',
    EXOPLANET_DATA: 'exoplanetData',
    TEMPORAL_DATA: 'temporalData',
    ANALYSIS_DATA: 'analysisData'
};

export const DataCacheProvider = ({ children }) => {
    const [cache, setCache] = useState(() => {
        // Try to restore cache from sessionStorage
        try {
            const stored = sessionStorage.getItem('cosmicDataCache');
            if (stored) {
                const parsed = JSON.parse(stored);
                // Check if cache is still valid
                const now = Date.now();
                const validCache = {};
                let hasValidData = false;
                
                Object.entries(parsed).forEach(([key, value]) => {
                    if (value.timestamp && now - value.timestamp < CACHE_TTL) {
                        validCache[key] = value;
                        hasValidData = true;
                    }
                });
                
                return hasValidData ? validCache : {};
            }
        } catch (error) {
            console.error('Failed to restore cache:', error);
        }
        return {};
    });

    const [cacheMetadata, setCacheMetadata] = useState({});

    // Get cached data
    const getCached = useCallback((key) => {
        const cached = cache[key];
        if (!cached) return null;

        const now = Date.now();
        const age = now - cached.timestamp;

        // Check if cache is expired
        if (age > CACHE_TTL) {
            // Remove expired cache
            setCache(prev => {
                const newCache = { ...prev };
                delete newCache[key];
                sessionStorage.setItem('cosmicDataCache', JSON.stringify(newCache));
                return newCache;
            });
            return null;
        }

        return cached.data;
    }, [cache]);

    // Update cache
    const updateCache = useCallback((key, data) => {
        const now = Date.now();
        const newCacheEntry = {
            data,
            timestamp: now
        };

        setCache(prev => {
            const newCache = {
                ...prev,
                [key]: newCacheEntry
            };
            // Persist to sessionStorage
            try {
                sessionStorage.setItem('cosmicDataCache', JSON.stringify(newCache));
            } catch (error) {
                console.error('Failed to persist cache:', error);
            }
            return newCache;
        });

        // Update metadata
        setCacheMetadata(prev => ({
            ...prev,
            [key]: {
                lastUpdated: now,
                size: JSON.stringify(data).length
            }
        }));
    }, []);

    // Invalidate specific cache key
    const invalidateCache = useCallback((key) => {
        setCache(prev => {
            const newCache = { ...prev };
            delete newCache[key];
            try {
                sessionStorage.setItem('cosmicDataCache', JSON.stringify(newCache));
            } catch (error) {
                console.error('Failed to update cache:', error);
            }
            return newCache;
        });

        setCacheMetadata(prev => {
            const newMetadata = { ...prev };
            delete newMetadata[key];
            return newMetadata;
        });
    }, []);

    // Clear all cache
    const clearCache = useCallback(() => {
        setCache({});
        setCacheMetadata({});
        try {
            sessionStorage.removeItem('cosmicDataCache');
        } catch (error) {
            console.error('Failed to clear cache:', error);
        }
    }, []);

    const value = {
        getCached,
        updateCache,
        invalidateCache,
        clearCache,
        cacheMetadata,
        CACHE_KEYS
    };

    return (
        <DataCacheContext.Provider value={value}>
            {children}
        </DataCacheContext.Provider>
    );
};

export const useDataCache = () => {
    const context = useContext(DataCacheContext);
    if (!context) {
        throw new Error('useDataCache must be used within DataCacheProvider');
    }
    return context;
};

export default DataCacheContext;
