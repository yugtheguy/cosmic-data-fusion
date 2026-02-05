/**
 * Cache Manager for Dashboard Data
 * Handles sessionStorage persistence with TTL
 */

const CACHE_PREFIX = 'cosmic_cache_';
const DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes in milliseconds

export const cacheManager = {
    /**
     * Save data to cache with timestamp
     */
    set(key, data, ttl = DEFAULT_TTL) {
        try {
            const cacheItem = {
                data,
                timestamp: Date.now(),
                ttl
            };
            sessionStorage.setItem(CACHE_PREFIX + key, JSON.stringify(cacheItem));
            return true;
        } catch (error) {
            console.warn('Cache set failed:', error);
            // Handle quota exceeded
            if (error.name === 'QuotaExceededError') {
                this.clear();
            }
            return false;
        }
    },

    /**
     * Get data from cache if not expired
     */
    get(key) {
        try {
            const item = sessionStorage.getItem(CACHE_PREFIX + key);
            if (!item) return null;

            const cacheItem = JSON.parse(item);
            const age = Date.now() - cacheItem.timestamp;

            // Check if expired
            if (age > cacheItem.ttl) {
                this.remove(key);
                return null;
            }

            return {
                data: cacheItem.data,
                age,
                fresh: age < (cacheItem.ttl / 2) // Fresh if less than half TTL
            };
        } catch (error) {
            console.warn('Cache get failed:', error);
            return null;
        }
    },

    /**
     * Remove specific cache entry
     */
    remove(key) {
        try {
            sessionStorage.removeItem(CACHE_PREFIX + key);
        } catch (error) {
            console.warn('Cache remove failed:', error);
        }
    },

    /**
     * Clear all cache entries
     */
    clear() {
        try {
            const keys = Object.keys(sessionStorage);
            keys.forEach(key => {
                if (key.startsWith(CACHE_PREFIX)) {
                    sessionStorage.removeItem(key);
                }
            });
        } catch (error) {
            console.warn('Cache clear failed:', error);
        }
    },

    /**
     * Get cache metadata
     */
    getMetadata(key) {
        const cached = this.get(key);
        if (!cached) {
            return { exists: false };
        }

        const ageMinutes = Math.floor(cached.age / 60000);
        const ageSeconds = Math.floor((cached.age % 60000) / 1000);

        return {
            exists: true,
            age: cached.age,
            ageDisplay: ageMinutes > 0 ? `${ageMinutes}m ago` : `${ageSeconds}s ago`,
            fresh: cached.fresh
        };
    }
};
