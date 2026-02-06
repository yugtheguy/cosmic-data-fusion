import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import ResultsTable from '../components/ResultsTable';
import { useAuth } from '../context/AuthContext';
import { useDataCache } from '../hooks/useDataCache';
import { searchStars } from '../services/api';
import './Dashboard.css';

const ResultsPage = () => {
    const { user, logout } = useAuth();
    const { getCached, updateCache, CACHE_KEYS } = useDataCache();

    const [stars, setStars] = useState([]);
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

                if (cachedStars && cachedStars.fresh) {
                    setStars(cachedStars.data.records || []);
                    setIsLoading(false);
                    return;
                }

                // Fetch fresh
                const starsResponse = await searchStars({ limit: 10000 });
                updateCache(CACHE_KEYS.STARS, starsResponse);
                setStars(starsResponse.records || []);
            } catch (err) {
                console.error('Failed to fetch results data:', err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, [getCached, updateCache, CACHE_KEYS]);

    return (
        <div className="dashboard">
            <Sidebar
                activeTab="results"
                user={user}
                onLogout={handleLogout}
            />
            <main className="dashboard-main" style={{ padding: '2rem' }}>
                <ResultsTable
                    data={stars}
                    isLoading={isLoading}
                    title="Full Catalog Results"
                    showSearch={true}
                    pageSize={50}
                />
            </main>
        </div>
    );
};

export default ResultsPage;
