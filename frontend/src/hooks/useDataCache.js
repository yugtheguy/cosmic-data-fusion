import { useContext } from 'react';
import { DataCacheContext } from '../contexts/DataCacheContext';

/**
 * Custom hook for easy cache access
 */
export const useDataCache = () => {
    const context = useContext(DataCacheContext);
    
    if (!context) {
        throw new Error('useDataCache must be used within DataCacheProvider');
    }

    return context;
};
