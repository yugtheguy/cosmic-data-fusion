import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignUpPage from './pages/SignUpPage';
import Dashboard from './pages/Dashboard';
import StarDetailPage from './pages/StarDetailPage';

import QueryBuilder from './pages/QueryBuilder';

function App() {
    return (
        <>
            <Router>
                <Routes>
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/signup" element={<SignUpPage />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/query" element={<QueryBuilder />} />
                    <Route path="/star/:id" element={<StarDetailPage />} />
                </Routes>
            </Router>
            <Toaster
                position="top-right"
                toastOptions={{
                    duration: 4000,
                    style: {
                        background: 'rgba(26, 26, 26, 0.95)',
                        color: '#e5e5e5',
                        border: '1px solid #2a2a2a',
                        backdropFilter: 'blur(12px)',
                        borderRadius: '12px',
                        padding: '12px 16px',
                        fontSize: '0.9rem',
                        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
                    },
                    success: {
                        iconTheme: {
                            primary: '#e8a87c',
                            secondary: '#1a1a1a',
                        },
                        style: {
                            borderColor: 'rgba(232, 168, 124, 0.3)',
                        },
                    },
                    error: {
                        iconTheme: {
                            primary: '#ef4444',
                            secondary: '#1a1a1a',
                        },
                        style: {
                            borderColor: 'rgba(239, 68, 68, 0.3)',
                        },
                    },
                    loading: {
                        iconTheme: {
                            primary: '#d4683a',
                            secondary: '#1a1a1a',
                        },
                    },
                }}
            />
        </>
    );
}

export default App;
