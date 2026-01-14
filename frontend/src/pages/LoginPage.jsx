import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Rocket, Mail, Lock, Eye, EyeOff, ArrowRight } from 'lucide-react';
import './LoginPage.css';

// Cloud Overlay that fades out
function CloudOverlay({ isVisible }) {
    return (
        <div className={`login-cloud-overlay ${!isVisible ? 'fade-out' : ''}`}>
            <div className="login-cloud lc-1"></div>
            <div className="login-cloud lc-2"></div>
            <div className="login-cloud lc-3"></div>
            <div className="login-cloud lc-4"></div>
            <div className="login-cloud lc-5"></div>
        </div>
    );
}

// Login Form Component
function LoginForm({ isVisible }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);

        // Simulate login
        setTimeout(() => {
            setIsLoading(false);
            navigate('/dashboard');
        }, 1500);
    };

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    className="login-form-container"
                    initial={{ opacity: 0, y: 100, scale: 0.9 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{
                        duration: 1,
                        delay: 0.5,
                        ease: [0.25, 0.46, 0.45, 0.94]
                    }}
                >
                    <div className="login-card-3d">
                        {/* Glowing border effect */}
                        <div className="card-glow"></div>

                        {/* Logo */}
                        <div className="login-logo">
                            <div className="logo-icon-wrapper">
                                <Rocket size={20} />
                            </div>
                            <h1 className="logo-text">COSMIC</h1>
                        </div>

                        <h2 className="login-title">Welcome Back</h2>
                        <p className="login-subtitle">Sign in to explore the universe of data</p>

                        {/* Login Form */}
                        <form onSubmit={handleSubmit} className="login-form">
                            <div className="form-group">
                                <label className="form-label">
                                    <Mail size={14} />
                                    Email
                                </label>
                                <input
                                    type="email"
                                    className="form-input"
                                    placeholder="astronaut@cosmic.space"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label">
                                    <Lock size={14} />
                                    Password
                                </label>
                                <div className="password-input-wrapper">
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        className="form-input"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                    />
                                    <button
                                        type="button"
                                        className="password-toggle"
                                        onClick={() => setShowPassword(!showPassword)}
                                    >
                                        {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                    </button>
                                </div>
                            </div>

                            <div className="form-options">
                                <label className="checkbox-label">
                                    <input type="checkbox" />
                                    <span>Remember me</span>
                                </label>
                                <a href="#" className="forgot-link">Forgot password?</a>
                            </div>

                            <button
                                type="submit"
                                className={`login-button ${isLoading ? 'loading' : ''}`}
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <span className="spinner"></span>
                                ) : (
                                    <>
                                        <span>Launch Into COSMIC</span>
                                        <ArrowRight size={16} />
                                    </>
                                )}
                            </button>
                        </form>

                        {/* Divider */}
                        <div className="login-divider">
                            <span>or continue with</span>
                        </div>

                        {/* Social Login */}
                        <div className="social-login">
                            <button className="social-button">
                                <svg viewBox="0 0 24 24" width="18" height="18">
                                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                                    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                                </svg>
                                Google
                            </button>
                            <button className="social-button">
                                <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                                </svg>
                                GitHub
                            </button>
                        </div>

                        {/* Sign Up Link */}
                        <p className="signup-link">
                            New to COSMIC? <Link to="/signup">Create an account</Link>
                        </p>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}

// Main Login Page Component
function LoginPage() {
    const [showClouds, setShowClouds] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [imageLoaded, setImageLoaded] = useState(false);

    useEffect(() => {
        // Preload the Mars facility image
        const img = new Image();
        img.src = '/Assets/Images/mars-facility.png';
        img.onload = () => {
            setImageLoaded(true);

            // Fade out clouds after image loads
            const cloudTimer = setTimeout(() => {
                setShowClouds(false);
            }, 800);

            const formTimer = setTimeout(() => {
                setShowForm(true);
            }, 1200);

            return () => {
                clearTimeout(cloudTimer);
                clearTimeout(formTimer);
            };
        };
    }, []);

    return (
        <div className="login-page-container">
            {/* Mars Sky Background */}
            <div className="mars-sky-bg">
                <div className="mars-mountains"></div>
            </div>

            {/* Mars Facility Image */}
            <div className={`mars-facility-bg ${imageLoaded ? 'loaded' : ''}`}>
                <img
                    src="/Assets/Images/mars-facility.png"
                    alt="Mars Mining Facility"
                />
            </div>

            {/* Cloud Overlay - fades out after loading */}
            <CloudOverlay isVisible={showClouds} />

            {/* Login Form - appears after clouds fade */}
            <LoginForm isVisible={showForm} />

            {/* Back to Landing button */}
            <Link to="/" className="back-link">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M19 12H5M12 19l-7-7 7-7" />
                </svg>
                Back to Home
            </Link>
        </div>
    );
}

export default LoginPage;
