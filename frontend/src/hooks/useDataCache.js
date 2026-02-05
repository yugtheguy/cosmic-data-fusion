import { useContext } from 'react';
import DataCacheContext from '../contexts/DataCacheContext';

export const useDataCache = () => {
    const context = useContext(DataCacheContext);
    if (!context) {
        throw new Error('useDataCache must be used within DataCacheProvider');
    }
    return context;
};

export default useDataCache;
