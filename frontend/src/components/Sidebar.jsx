import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    LayoutDashboard,
    Map,
    Brain,
    Link2,
    Download,
    Search,
    User,
    Database,
    Filter,
    LogOut,
    UploadCloud,
    Target,
    Clock
} from 'lucide-react';

function Sidebar({ 
    activeTab, 
    setActiveTab, 
    filters, 
    setFilters, 
    onResetFilters, 
    isLoading, 
    datasets, 
    onDeleteDataset,
    children // For custom sections like Fast Movers in TimeMachine
}) {
    const navigate = useNavigate();
    const { user, logout } = useAuth();
    
    const navItems = [
        { id: 'overview', icon: LayoutDashboard, label: 'Overview', action: 'tab' },
        { id: 'timemachine', icon: Clock, label: 'Time Machine', link: '/timemachine' },
        { id: 'query', icon: Search, label: 'Query Builder', link: '/query' },
        { id: 'results', icon: Database, label: 'Data Table', action: 'tab' },
        { id: 'upload', icon: UploadCloud, label: 'Ingest Data', action: 'tab' },
        { id: 'skymap', icon: Map, label: 'Sky Map', action: 'tab' },
        { id: 'anomaly', icon: Brain, label: 'AI Lab', action: 'tab' },
        { id: 'harmonize', icon: Link2, label: 'Harmonizer', action: 'tab' },
        { id: 'export', icon: Download, label: 'Export', action: 'tab' },
        { id: 'planet-hunter', icon: Target, label: 'Planet Hunter', link: '/planet-hunter' },
    ];

    const handleNavClick = (item) => {
        if (item.link) {
            navigate(item.link);
        } else if (item.action === 'tab') {
            setActiveTab(item.id);
        }
    };

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
                    item.link ? (
                        <Link
                            key={item.id}
                            to={item.link}
                            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                        >
                            <item.icon size={18} strokeWidth={1.5} />
                            <span>{item.label}</span>
                        </Link>
                    ) : (
                        <button
                            key={item.id}
                            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                            onClick={() => handleNavClick(item)}
                        >
                            <item.icon size={18} strokeWidth={1.5} />
                            <span>{item.label}</span>
                        </button>
                    )
                ))}
            </nav>

            {/* Custom content section (filters, fast movers, etc.) */}
            {children}

            {/* User Section */}
            <div className="sidebar-user">
                <div className="user-avatar">
                    <User size={16} strokeWidth={1.5} />
                </div>
                <div className="user-info">
                    <span className="user-name">{user?.full_name || user?.email || 'Researcher'}</span>
                    <span className="user-role">Astronomer</span>
                </div>
                <button 
                    className="logout-btn" 
                    title="Logout"
                    onClick={() => {
                        logout();
                        navigate('/login');
                    }}
                >
                    <LogOut size={16} strokeWidth={1.5} />
                </button>
            </div>
        </aside>
    );
}

export default Sidebar;
