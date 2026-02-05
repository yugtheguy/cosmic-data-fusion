import React from 'react';
import { useNavigate } from 'react-router-dom';
import { User, LogOut } from 'lucide-react';
import './Sidebar.css';

/**
 * Shared Sidebar Component
 * 
 * @param {Object} props
 * @param {string} props.activeTab - The ID of the currently active tab
 * @param {Function} [props.setActiveTab] - Callback to set the active tab (if standard dashboard navigation)
 * @param {Array} props.navItems - Array of navigation items { id, icon, label, link?, external? }
 * @param {React.ReactNode} [props.children] - Additional content to render (filters, etc.)
 */
function Sidebar({ activeTab, setActiveTab, navItems, children }) {
    const navigate = useNavigate();

    return (
        <aside className="dashboard-sidebar">
            {/* Logo */}
            <div className="sidebar-logo">
                <div className="logo-mark">C</div>
                <span className="logo-text">COSMIC</span>
            </div>

            {/* Navigation */}
            <nav className="sidebar-nav">
                <div className="nav-section-label">Navigation</div>
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                        onClick={() => {
                            if (item.external) {
                                window.location.href = item.link || '#';
                            } else if (item.link) {
                                navigate(item.link);
                            } else if (setActiveTab) {
                                setActiveTab(item.id);
                            }
                        }}
                    >
                        <item.icon size={18} strokeWidth={1.5} />
                        <span>{item.label}</span>
                    </button>
                ))}
            </nav>

            {/* Custom Content (Filters, Fast Movers, etc.) */}
            {children}

            {/* User Section */}
            <div className="sidebar-user">
                <div className="user-avatar">
                    <User size={16} strokeWidth={1.5} />
                </div>
                <div className="user-info">
                    <span className="user-name">Researcher</span>
                    <span className="user-role">Astronomer</span>
                </div>
                <button className="logout-btn" title="Logout">
                    <LogOut size={16} strokeWidth={1.5} />
                </button>
            </div>
        </aside>
    );
}

export default Sidebar;
