import { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, register as apiRegister, getCurrentUser } from '../services/api';
import toast from 'react-hot-toast';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);

    // Check for token on mount
    useEffect(() => {
        const checkAuth = async () => {
            const token = localStorage.getItem('token');
            if (token) {
                try {
                    const userData = await getCurrentUser();
                    setUser(userData);
                    setIsAuthenticated(true);
                } catch (error) {
                    console.error("Session expired or invalid:", error);
                    logout();
                }
            }
            setLoading(false);
        };
        checkAuth();
    }, []);

    const login = async (email, password) => {
        try {
            const data = await apiLogin(email, password);
            localStorage.setItem('token', data.access_token);
            setIsAuthenticated(true);

            // Get user details
            const userData = await getCurrentUser();
            setUser(userData);

            return true;
        } catch (error) {
            console.error("Login error:", error);
            const message = error.response?.data?.detail || "Login failed. Please check your credentials.";
            throw new Error(message);
        }
    };

    const register = async (userData) => {
        try {
            const data = await apiRegister(userData);
            localStorage.setItem('token', data.access_token);
            setIsAuthenticated(true);

            // User data is returned in register response, but getting fresh profile is safer
            // Or use the response data directly if it matches the user profile shape
            setUser({
                id: data.id,
                email: data.email,
                full_name: data.full_name,
                is_active: data.is_active
            });

            return true;
        } catch (error) {
            console.error("Registration error:", error);
            const message = error.response?.data?.detail || "Registration failed.";
            throw new Error(message);
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
        setIsAuthenticated(false);
        // Optional: Redirect or show toast
        toast.success("Logged out successfully");
    };

    return (
        <AuthContext.Provider value={{
            user,
            isAuthenticated,
            loading,
            login,
            register,
            logout
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};
