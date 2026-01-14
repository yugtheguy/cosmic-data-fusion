import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Rocket, Mail, Lock, Eye, EyeOff, ArrowRight, User, CheckCircle } from 'lucide-react';
import './SignUpPage.css';

// Cloud Overlay that fades out
function CloudOverlay({ isVisible }) {
    return (
        <div className={`signup-cloud-overlay ${!isVisible ? 'fade-out' : ''}`}>
            <div className="signup-cloud lc-1"></div>
            <div className="signup-cloud lc-2"></div>
            <div className="signup-cloud lc-3"></div>
            <div className="signup-cloud lc-4"></div>
            <div className="signup-cloud lc-5"></div>
        </div>
    );
}

// SignUp Form Component
function SignUpForm({ isVisible }) {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            alert("Passwords do not match!");
            return;
        }

        setIsLoading(true);

        // Simulate signup
        setTimeout(() => {
            setIsLoading(false);
            // In a real app, you'd auto-login or redirect to login. 
            // Here, let's redirect to dashboard for seamless demo experience.
            navigate('/dashboard');
        }, 1500);
    };

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    className="signup-form-container"
                    initial={{ opacity: 0, y: 100, scale: 0.9 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{
                        duration: 1,
                        delay: 0.5,
                        ease: [0.25, 0.46, 0.45, 0.94]
                    }}
                >
                    <div className="signup-card-3d">
                        {/* Glowing border effect */}
                        <div className="card-glow"></div>

                        {/* Logo */}
                        <div className="signup-logo">
                            <div className="logo-icon-wrapper">
                                <Rocket size={20} />
                            </div>
                            <h1 className="logo-text">COSMIC</h1>
                        </div>

                        <h2 className="signup-title">Join the Mission</h2>
                        <p className="signup-subtitle">Embark on your journey into the data cosmos</p>

                        {/* Signup Form */}
                        <form onSubmit={handleSubmit} className="signup-form">
                            <div className="form-group">
                                <label className="form-label">
                                    <User size={14} />
                                    Full Name
                                </label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="Major Tom"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label">
                                    <Mail size={14} />
                                    Email Address
                                </label>
                                <input
                                    type="email"
                                    className="form-input"
                                    placeholder="explorer@cosmic.space"
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
                                        placeholder="Min 8 chars"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        minLength={8}
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

                            <div className="form-group">
                                <label className="form-label">
                                    <CheckCircle size={14} />
                                    Confirm Password
                                </label>
                                <input
                                    type="password"
                                    className="form-input"
                                    placeholder="Confirm password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required
                                />
                            </div>

                            <button
                                type="submit"
                                className="signup-button"
                                disabled={isLoading}
                            >
                                {isLoading ? 'Creating Profile...' : (
                                    <>
                                        <span>Create Account</span>
                                        <ArrowRight size={16} />
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="divider">
                            <span>or sign up with</span>
                        </div>

                        <div className="social-login">
                            <button className="social-button">
                                <img src="https://www.google.com/favicon.ico" alt="Google" width="18" height="18" style={{ filter: 'grayscale(100%) brightness(200%)' }} />
                                Google
                            </button>
                            <button className="social-button">
                                <img src="https://github.com/favicon.ico" alt="GitHub" width="18" height="18" style={{ filter: 'invert(1)' }} />
                                GitHub
                            </button>
                        </div>

                        <div className="login-link">
                            Already have an account? <Link to="/login">Log in</Link>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}

// Main SignUp Page Component
function SignUpPage() {
    const [showClouds, setShowClouds] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [imageLoaded, setImageLoaded] = useState(false);

    useEffect(() => {
        // Preload the Mars facility image (reusing same asset)
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
        <div className="signup-page-container">
            {/* Reuse Mars Background */}
            <div className="mars-sky-bg">
                <div className="mars-mountains"></div>
            </div>

            <div className={`mars-facility-bg ${imageLoaded ? 'loaded' : ''}`}>
                <img src="/Assets/Images/mars-facility.png" alt="Mars Mining Facility" />
            </div>

            <CloudOverlay isVisible={showClouds} />
            <SignUpForm isVisible={showForm} />

            <Link to="/" className="back-link">
                <ArrowRight size={16} style={{ transform: 'rotate(180deg)' }} />
                Back to Home
            </Link>
        </div>
    );
}

export default SignUpPage;
