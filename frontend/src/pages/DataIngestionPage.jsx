import React from 'react';
import Sidebar from '../components/Sidebar';
import UploadView from '../components/UploadView';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css'; // Re-using dashboard styles for consistency

const DataIngestionPage = () => {
    const { user, logout } = useAuth();

    // Placeholder handler since we don't have full dashboard state here
    const handleResetFilters = () => { };
    const handleLogout = () => {
        logout();
        window.location.href = '/login';
    };

    return (
        <div className="dashboard">
            <Sidebar
                activeTab="upload"
                user={user}
                onLogout={handleLogout}
            />
            <main className="dashboard-main" style={{ padding: '2rem' }}>
                <UploadView
                    onUploadSuccess={() => {
                        // Optionally invalidate cache here if we had access to the context
                        // But UploadView logic suggests it might handle some of it or we rely on navigation
                    }}
                />
            </main>
        </div>
    );
};

export default DataIngestionPage;
