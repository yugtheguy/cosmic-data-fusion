import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import './ResearchMethodology.css';

/**
 * Phase 5: Research Methodology Explanation Page
 * 
 * Purpose: Explain ML methodology without implementation details
 * - No parameters
 * - No controls
 * - No raw ML data
 * - Focus on scientific credibility
 */
const ResearchMethodology = () => {
    const navigate = useNavigate();

    return (
        <div className="research-methodology-page">
            {/* Header */}
            <header className="research-header">
                <div className="header-content">
                    <button 
                        className="back-button" 
                        onClick={() => navigate('/dashboard')}
                        aria-label="Back to Dashboard"
                    >
                        ← Back to Dashboard
                    </button>
                    <motion.h1
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        🧬 Research Methodology
                    </motion.h1>
                    <p className="subtitle">
                        Understanding our AI-powered astronomical analysis
                    </p>
                </div>
            </header>

            {/* Main Content */}
            <div className="methodology-content">
                {/* Section 1: Overview */}
                <motion.section 
                    className="method-section"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.1 }}
                >
                    <h2>🎯 Why Machine Learning for Astronomy?</h2>
                    <div className="section-content">
                        <p>
                            Modern astronomical surveys generate <strong>petabytes of data</strong> containing 
                            millions of stellar observations. Traditional manual analysis becomes impractical 
                            at this scale. COSMIC Data Fusion employs <strong>unsupervised machine learning</strong> 
                            to automatically identify patterns that would be impossible to detect manually.
                        </p>
                        <div className="highlight-box">
                            <h3>Key Principle</h3>
                            <p>
                                We use <strong>unsupervised learning</strong> because we don't know what rare 
                                objects look like in advance. Instead of training on labeled examples, our 
                                algorithms discover patterns naturally present in the data.
                            </p>
                        </div>
                    </div>
                </motion.section>

                {/* Section 2: Anomaly Detection */}
                <motion.section 
                    className="method-section"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                >
                    <h2>🔍 Anomaly Detection: Finding the Unusual</h2>
                    <div className="section-content">
                        <h3>What We Detect</h3>
                        <ul>
                            <li>Stars with <strong>unusual brightness-distance relationships</strong></li>
                            <li>Objects with <strong>unexpected positions</strong> in parameter space</li>
                            <li>Potential <strong>measurement errors</strong> or data quality issues</li>
                            <li>Rare stellar types (binary stars, variable stars, outliers)</li>
                        </ul>

                        <h3>The Algorithm: Isolation Forest</h3>
                        <p>
                            We use <strong>Isolation Forest</strong>, a technique specifically designed 
                            for anomaly detection in multidimensional data. It works on a simple principle:
                        </p>
                        <div className="algorithm-box">
                            <p>
                                <strong>Core Insight:</strong> Anomalies are easier to separate from the 
                                rest of the data. By randomly partitioning the feature space, unusual 
                                objects require fewer splits to isolate than normal objects buried in 
                                dense regions.
                            </p>
                        </div>

                        <h3>Features Analyzed</h3>
                        <div className="features-grid">
                            <div className="feature-card">
                                <span className="feature-icon">📍</span>
                                <strong>Right Ascension (RA)</strong>
                                <p>Sky position (longitude)</p>
                            </div>
                            <div className="feature-card">
                                <span className="feature-icon">📍</span>
                                <strong>Declination (Dec)</strong>
                                <p>Sky position (latitude)</p>
                            </div>
                            <div className="feature-card">
                                <span className="feature-icon">💡</span>
                                <strong>Brightness (Magnitude)</strong>
                                <p>Distance-corrected when possible</p>
                            </div>
                            <div className="feature-card">
                                <span className="feature-icon">📏</span>
                                <strong>Parallax</strong>
                                <p>Distance indicator</p>
                            </div>
                        </div>

                        <div className="info-box">
                            <h4>🌟 Research Enhancement</h4>
                            <p>
                                Our system applies <strong>astronomy-aware normalization</strong>—adjusting 
                                brightness by distance to compare stars at a standard distance. This prevents 
                                false anomalies caused solely by distance effects.
                            </p>
                        </div>
                    </div>
                </motion.section>

                {/* Section 3: Clustering */}
                <motion.section 
                    className="method-section"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                >
                    <h2>🔗 Spatial Clustering: Finding Groups</h2>
                    <div className="section-content">
                        <h3>What We Discover</h3>
                        <ul>
                            <li><strong>Stellar associations</strong> and open clusters</li>
                            <li><strong>Co-moving groups</strong> of stars with similar motion</li>
                            <li><strong>Regions of similar stellar populations</strong></li>
                            <li>Spatially concentrated areas worthy of further study</li>
                        </ul>

                        <h3>The Algorithm: DBSCAN</h3>
                        <p>
                            We use <strong>DBSCAN (Density-Based Spatial Clustering)</strong>, chosen for 
                            its ability to find clusters of arbitrary shape and automatically identify noise.
                        </p>
                        <div className="algorithm-box">
                            <p>
                                <strong>Why DBSCAN?</strong> Unlike algorithms that assume spherical clusters, 
                                DBSCAN finds dense regions of any shape. It doesn't require specifying the 
                                number of clusters in advance—perfect for exploratory astronomical research.
                            </p>
                        </div>

                        <h3>Quality Assurance</h3>
                        <p>Our system applies several research-grade quality checks:</p>
                        <ul className="quality-list">
                            <li>
                                <strong>Cluster Validity Filtering:</strong> Automatically suppresses 
                                clusters that are too small or too sparse to be scientifically meaningful
                            </li>
                            <li>
                                <strong>Proper Motion Consistency:</strong> When available, checks if 
                                stars in a cluster move together (indicating a physical association)
                            </li>
                            <li>
                                <strong>Silhouette Score Analysis:</strong> Internal metric measuring 
                                cluster cohesion and separation (not exposed to users but tracked for quality)
                            </li>
                        </ul>
                    </div>
                </motion.section>

                {/* Section 4: Limitations & Honesty */}
                <motion.section 
                    className="method-section warning-section"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.4 }}
                >
                    <h2>⚠️ Known Limitations</h2>
                    <div className="section-content">
                        <p>
                            Scientific honesty requires acknowledging what our methods <strong>cannot</strong> do:
                        </p>
                        <div className="limitations-grid">
                            <div className="limitation-card">
                                <h4>🔢 Data Dependency</h4>
                                <p>
                                    Results are only as good as the input data. Small datasets 
                                    ({"<"}100 stars) produce less reliable patterns. You'll see a 
                                    warning when data is limited.
                                </p>
                            </div>
                            <div className="limitation-card">
                                <h4>🎯 Statistical Nature</h4>
                                <p>
                                    Anomaly detection is inherently probabilistic. Not every flagged 
                                    star is scientifically interesting—some are measurement uncertainties.
                                </p>
                            </div>
                            <div className="limitation-card">
                                <h4>🌐 2D Projections</h4>
                                <p>
                                    Spatial clustering uses sky coordinates (RA, Dec), which are 2D 
                                    projections. Some clusters may be chance alignments along the line of sight.
                                </p>
                            </div>
                            <div className="limitation-card">
                                <h4>🔧 Parameter Sensitivity</h4>
                                <p>
                                    Default parameters work well for typical datasets, but unusual 
                                    data distributions may benefit from adjustment.
                                </p>
                            </div>
                        </div>

                        <div className="honesty-box">
                            <h4>🛡️ Our Commitment to Transparency</h4>
                            <p>
                                When our system detects potential issues—sparse data, low clustering 
                                confidence, or unusual score distributions—it provides <strong>soft 
                                warnings</strong>. These help you interpret results critically without 
                                blocking your work.
                            </p>
                        </div>
                    </div>
                </motion.section>

                {/* Section 5: Example Discoveries */}
                <motion.section 
                    className="method-section success-section"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.5 }}
                >
                    <h2>✨ Real Discoveries from COSMIC Data</h2>
                    <div className="section-content">
                        <p>
                            Our methodology has successfully identified real patterns in astronomical data:
                        </p>
                        <div className="discoveries-grid">
                            <div className="discovery-card">
                                <h4>📊 459 Cross-Matched Pairs</h4>
                                <p>
                                    Linked observations of the same stars across Gaia DR3 and TESS 
                                    catalogs using spatial cross-matching
                                </p>
                            </div>
                            <div className="discovery-card">
                                <h4>🌟 50 Anomalous Objects</h4>
                                <p>
                                    Flagged unusual stars in the Pleiades test dataset, including 
                                    known binary systems and variable stars
                                </p>
                            </div>
                            <div className="discovery-card">
                                <h4>🔗 8 Stellar Clusters</h4>
                                <p>
                                    Identified dense groupings consistent with known open cluster 
                                    regions in our test data
                                </p>
                            </div>
                        </div>
                    </div>
                </motion.section>

                {/* Section 6: How to Use */}
                <motion.section 
                    className="method-section guide-section"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.6 }}
                >
                    <h2>🚀 Best Practices for Researchers</h2>
                    <div className="section-content">
                        <div className="practices-list">
                            <div className="practice-item">
                                <span className="practice-number">1</span>
                                <div>
                                    <h4>Start with Default Parameters</h4>
                                    <p>
                                        Our system uses research-tested defaults (5% contamination 
                                        for anomalies, eps=0.5 for clustering). These work well for 
                                        most astronomical datasets.
                                    </p>
                                </div>
                            </div>
                            <div className="practice-item">
                                <span className="practice-number">2</span>
                                <div>
                                    <h4>Review Warnings Carefully</h4>
                                    <p>
                                        If you see an analysis note about limited data or low confidence, 
                                        consider loading more stars or adjusting your query filters.
                                    </p>
                                </div>
                            </div>
                            <div className="practice-item">
                                <span className="practice-number">3</span>
                                <div>
                                    <h4>Validate Interesting Findings</h4>
                                    <p>
                                        ML is a discovery tool, not a final verdict. Cross-reference 
                                        flagged anomalies with catalogs like SIMBAD or check cluster 
                                        coordinates against known stellar associations.
                                    </p>
                                </div>
                            </div>
                            <div className="practice-item">
                                <span className="practice-number">4</span>
                                <div>
                                    <h4>Use Export Features</h4>
                                    <p>
                                        Export results to CSV or VOTable format for further analysis 
                                        in your preferred tools (TopCat, Python, R).
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </motion.section>

                {/* Footer */}
                <motion.section 
                    className="method-footer"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.8, delay: 0.7 }}
                >
                    <div className="footer-content">
                        <p>
                            <strong>Research-Grade ML, User-Friendly Interface</strong>
                        </p>
                        <p>
                            COSMIC Data Fusion combines rigorous statistical methods with an intuitive 
                            interface—so you can focus on science, not algorithms.
                        </p>
                        <button 
                            className="cta-button"
                            onClick={() => navigate('/dashboard')}
                        >
                            Explore the Data →
                        </button>
                    </div>
                </motion.section>
            </div>
        </div>
    );
};

export default ResearchMethodology;
