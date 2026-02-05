import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, Loader } from 'lucide-react';
import toast from 'react-hot-toast';
import './SignUpPage.css'; // Reusing styles for consistency

const VerifyEmailPage = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const token = searchParams.get('token');
    const [status, setStatus] = useState('verifying'); // verifying, success, error

    useEffect(() => {
        if (!token) {
            setStatus('error');
            toast.error("Invalid verification link.");
            return;
        }

        const verifyEmail = async () => {
            try {
                // Determine API base URL (handling proxy if needed, but safe to use relative or env)
                // Assuming Vite proxy is set up or using direct URL if defined
                // For this direct implementation, we'll try the relative path first which works with Vite proxy
                await axios.get(`/auth/verify-email?token=${token}`);

                setStatus('success');
                toast.success("Email verified successfully!");
                setTimeout(() => {
                    navigate('/login');
                }, 3000);
            } catch (error) {
                console.error("Verification failed:", error);
                setStatus('error');
                toast.error(error.response?.data?.detail || "Verification failed. Link may be expired.");
            }
        };

        verifyEmail();
    }, [token, navigate]);

    return (
        <div className="signup-page-container">
            <div className="mars-sky-bg">
                <div className="mars-mountains"></div>
            </div>

            <motion.div
                className="signup-form-container"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
            >
                <div className="signup-card-3d" style={{ textAlign: 'center', padding: '40px' }}>
                    <div className="card-glow"></div>

                    {status === 'verifying' && (
                        <div>
                            <Loader className="animate-spin" size={48} color="#d4683a" style={{ margin: '0 auto 20px' }} />
                            <h2>Verifying your email...</h2>
                            <p className="signup-subtitle">Please wait while we confirm your signal.</p>
                        </div>
                    )}

                    {status === 'success' && (
                        <div>
                            <CheckCircle size={48} color="#4ade80" style={{ margin: '0 auto 20px' }} />
                            <h2>Verification Successful!</h2>
                            <p className="signup-subtitle">Your account is now active.</p>
                            <p style={{ marginTop: '20px', color: '#888' }}>Redirecting to login...</p>
                        </div>
                    )}

                    {status === 'error' && (
                        <div>
                            <XCircle size={48} color="#ef4444" style={{ margin: '0 auto 20px' }} />
                            <h2>Verification Failed</h2>
                            <p className="signup-subtitle">The link may be invalid or expired.</p>
                            <button
                                onClick={() => navigate('/login')}
                                className="signup-button"
                                style={{ marginTop: '20px' }}
                            >
                                Return to Login
                            </button>
                        </div>
                    )}
                </div>
            </motion.div>
        </div>
    );
};

export default VerifyEmailPage;
