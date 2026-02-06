import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import SkyMap from '../components/SkyMap';
import { useAuth } from '../context/AuthContext';
import { useDataCache } from '../hooks/useDataCache';
import { searchStars, detectAnomalies, checkHealth } from '../services/api';
import './Dashboard.css';

const SkyMapPage = () => {
    const { user, logout } = useAuth();
    const { getCached, updateCache, CACHE_KEYS } = useDataCache();

    const [stars, setStars] = useState([]);
    const [anomalies, setAnomalies] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    const handleLogout = () => {
        logout();
        window.location.href = '/login';
    };

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                // Check cache first
                const cachedStars = getCached(CACHE_KEYS.STARS);
                const cachedAnomalies = getCached(CACHE_KEYS.ANOMALIES);

                if (cachedStars && cachedStars.fresh) {
                    setStars(cachedStars.data.records || []);
                    if (cachedAnomalies && cachedAnomalies.fresh) {
                        setAnomalies(cachedAnomalies.data || []);
                    }
                    setIsLoading(false);
                    return;
                }

                // Fetch fresh
                await checkHealth();
                const starsResponse = await searchStars({ limit: 10000 });
                updateCache(CACHE_KEYS.STARS, starsResponse);
                setStars(starsResponse.records || []);

                try {
                    const anomaliesResponse = await detectAnomalies(0.05);
                    updateCache(CACHE_KEYS.ANOMALIES, anomaliesResponse.anomalies || []);
                    setAnomalies(anomaliesResponse.anomalies || []);
                } catch (err) {
                    console.warn('Anomaly detection failed:', err);
                }

            } catch (err) {
                console.error('Failed to fetch sky map data:', err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, [getCached, updateCache, CACHE_KEYS]);

    return (
        <div className="dashboard">
            <Sidebar
                activeTab="skymap"
                user={user}
                onLogout={handleLogout}
            />
            <main className="dashboard-main" style={{ height: '100vh', overflow: 'hidden' }}>
                <SkyMap
                    stars={stars}
                    anomalies={anomalies}
                    isLoading={isLoading}
                />
            </main>
        </div>
    );
};

export default SkyMapPage;
