import React from 'react';
import Sidebar from '../components/Sidebar';
import Harmonizer from '../components/Harmonizer';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

const HarmonizerPage = () => {
    const { user, logout } = useAuth();

    const handleLogout = () => {
        logout();
        window.location.href = '/login';
    };

    return (
        <div className="dashboard">
            <Sidebar
                activeTab="harmonize"
                user={user}
                onLogout={handleLogout}
            />
            <main className="dashboard-main" style={{ height: '100vh', overflow: 'hidden' }}>
                <Harmonizer />
            </main>
        </div>
    );
};

export default HarmonizerPage;
