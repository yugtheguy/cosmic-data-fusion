import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { getCurrentUser } from '../services/api';

/**
 * OAuth Callback Handler
 * 
 * Handles the redirect from Google OAuth, extracts the JWT token,
 * stores it, and redirects to the dashboard.
 */
function AuthCallback() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    useEffect(() => {
        const handleCallback = async () => {
            const token = searchParams.get('token');
            const error = searchParams.get('error');

            if (error) {
                toast.error(`Authentication failed: ${error}`);
                navigate('/login');
                return;
            }

            if (token) {
                try {
                    // Store token
                    localStorage.setItem('token', token);

                    // Get user info
                    const userData = await getCurrentUser();
                    
                    // Update auth context (if you expose these methods)
                    // For now, the AuthContext useEffect will pick this up
                    
                    toast.success('Successfully logged in with Google!');
                    navigate('/dashboard');
                } catch (err) {
                    console.error('Failed to authenticate:', err);
                    toast.error('Authentication failed. Please try again.');
                    localStorage.removeItem('token');
                    navigate('/login');
                }
            } else {
                toast.error('No authentication token received');
                navigate('/login');
            }
        };

        handleCallback();
    }, [searchParams, navigate]);

    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100vh',
            background: 'linear-gradient(135deg, #1a1a1a 0%, #2d1810 100%)',
            color: '#e5e5e5',
            fontFamily: 'Inter, sans-serif'
        }}>
            <div style={{ textAlign: 'center' }}>
                <div style={{
                    width: '48px',
                    height: '48px',
                    border: '4px solid rgba(232, 168, 124, 0.3)',
                    borderTop: '4px solid #e8a87c',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                    margin: '0 auto 1rem'
                }}></div>
                <p style={{ fontSize: '1.1rem' }}>Completing sign in...</p>
                <style>{`
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                `}</style>
            </div>
        </div>
    );
}

export default AuthCallback;
