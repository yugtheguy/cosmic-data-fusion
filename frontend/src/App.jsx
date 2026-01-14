import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignUpPage from './pages/SignUpPage';
import Dashboard from './pages/Dashboard';
import StarDetailPage from './pages/StarDetailPage';

import QueryBuilder from './pages/QueryBuilder';

function App() {
    return (
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
    );
}

export default App;

