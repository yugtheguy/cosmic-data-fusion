import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Rocket, Mail, Lock, Eye, EyeOff, ArrowRight, User, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import './SignUpPage.css';

// SignUp Form Component
function SignUpForm() {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();
    const { register } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            toast.error("Passwords do not match!");
            return;
        }

        setIsLoading(true);

        try {
            await register({
                email,
                password,
                full_name: name
            });
            toast.success("Account created successfully!");
            navigate('/dashboard');
        } catch (error) {
            toast.error(error.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <motion.div
            className="signup-form-container"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
                duration: 0.6,
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
                        <label className="form-label" >
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
                    <button 
                        className="social-button"
                        onClick={() => window.location.href = 'http://localhost:8000/auth/google/login'}
                        type="button"
                    >
                        <img src="https://www.google.com/favicon.ico" alt="Google" width="18" height="18" style={{ filter: 'grayscale(100%) brightness(200%)' }} />
                        Google
                    </button>
                    <button className="social-button" type="button">
                        <img src="https://github.com/favicon.ico" alt="GitHub" width="18" height="18" style={{ filter: 'invert(1)' }} />
                        GitHub
                    </button>
                </div>

                <div className="login-link">
                    Already have an account? <Link to="/login">Log in</Link>
                </div>
            </div>
        </motion.div>
    );
}

// Main SignUp Page Component
function SignUpPage() {
    const [imageLoaded, setImageLoaded] = useState(false);

    useEffect(() => {
        // Preload the Mars facility image
        const img = new Image();
        img.src = '/Assets/Images/mars-facility.png';
        img.onload = () => {
            setImageLoaded(true);
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

            <SignUpForm />

            <Link to="/" className="back-link">
                <ArrowRight size={16} style={{ transform: 'rotate(180deg)' }} />
                Back to Home
            </Link>
        </div>
    );
}

export default SignUpPage;
