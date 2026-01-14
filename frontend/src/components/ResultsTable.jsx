import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Search,
    ChevronLeft,
    ChevronRight,
    ChevronsLeft,
    ChevronsRight,
    Star,
    Eye,
    Columns3,
    Check,
    Database,
    AlertTriangle,
    Sparkles,
    ArrowUpDown
} from 'lucide-react';
import './ResultsTable.css';

// Column definitions with smart formatting
const COLUMNS = [
    {
        key: 'source_id',
        label: 'Source ID',
        sortable: true,
        default: true,
        format: (val) => val?.substring(0, 16) + (val?.length > 16 ? '...' : '') || '—'
    },
    {
        key: 'ra_deg',
        label: 'RA (°)',
        sortable: true,
        default: true,
        format: (val) => val?.toFixed(4) || '—'
    },
    {
        key: 'dec_deg',
        label: 'Dec (°)',
        sortable: true,
        default: true,
        format: (val) => val?.toFixed(4) || '—'
    },
    {
        key: 'brightness_mag',
        label: 'Mag',
        sortable: true,
        default: true,
        format: (val) => val?.toFixed(2) || '—'
    },
    {
        key: 'parallax_mas',
        label: 'Parallax',
        sortable: true,
        default: false,
        format: (val) => val ? `${val.toFixed(3)} mas` : '—'
    },
    {
        key: 'distance_pc',
        label: 'Distance',
        sortable: true,
        default: false,
        format: (val) => val ? `${val.toFixed(1)} pc` : '—'
    },
    {
        key: 'original_source',
        label: 'Source',
        sortable: true,
        default: true,
        format: (val) => val?.toUpperCase() || 'UNKNOWN'
    },
];

// Get magnitude class for visual indicator
const getMagnitudeClass = (mag) => {
    if (mag === null || mag === undefined) return 'dim';
    if (mag < 6) return 'bright';
    if (mag < 12) return 'medium';
    return 'dim';
};

// Get source class for color coding
const getSourceClass = (source) => {
    const s = source?.toLowerCase() || '';
    if (s.includes('gaia')) return 'gaia';
    if (s.includes('sdss')) return 'sdss';
    if (s.includes('tess')) return 'tess';
    if (s.includes('fits')) return 'fits';
    return 'other';
};

const ResultsTable = ({
    data = [],
    isLoading = false,
    onRowClick,
    title = "Stellar Catalog",
    showSearch = true,
    showPagination = true,
    pageSize: initialPageSize = 25,
    highlightAnomalies = false,
    anomalyIds = []
}) => {
    const navigate = useNavigate();

    // State
    const [searchQuery, setSearchQuery] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(initialPageSize);
    const [visibleColumns, setVisibleColumns] = useState(
        COLUMNS.filter(c => c.default).map(c => c.key)
    );
    const [showColumnDropdown, setShowColumnDropdown] = useState(false);
    const [selectedRows, setSelectedRows] = useState(new Set());

    // Reset page when data changes
    useEffect(() => {
        setCurrentPage(1);
    }, [data.length, searchQuery]);

    // Filter data by search
    const filteredData = useMemo(() => {
        if (!searchQuery.trim()) return data;

        const query = searchQuery.toLowerCase();
        return data.filter(row =>
            Object.values(row).some(val =>
                String(val).toLowerCase().includes(query)
            )
        );
    }, [data, searchQuery]);

    // Sort data
    const sortedData = useMemo(() => {
        if (!sortConfig.key) return filteredData;

        return [...filteredData].sort((a, b) => {
            const aVal = a[sortConfig.key];
            const bVal = b[sortConfig.key];

            // Handle nulls
            if (aVal == null && bVal == null) return 0;
            if (aVal == null) return 1;
            if (bVal == null) return -1;

            // Compare
            let comparison = 0;
            if (typeof aVal === 'number' && typeof bVal === 'number') {
                comparison = aVal - bVal;
            } else {
                comparison = String(aVal).localeCompare(String(bVal));
            }

            return sortConfig.direction === 'asc' ? comparison : -comparison;
        });
    }, [filteredData, sortConfig]);

    // Paginate data
    const paginatedData = useMemo(() => {
        const start = (currentPage - 1) * pageSize;
        return sortedData.slice(start, start + pageSize);
    }, [sortedData, currentPage, pageSize]);

    const totalPages = Math.ceil(sortedData.length / pageSize);

    // Handlers
    const handleSort = useCallback((key) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
        }));
    }, []);

    const handleRowClick = useCallback((row) => {
        if (onRowClick) {
            onRowClick(row);
        } else if (row.id) {
            navigate(`/star/${row.id}`);
        }
    }, [onRowClick, navigate]);

    const toggleColumn = useCallback((key) => {
        setVisibleColumns(prev =>
            prev.includes(key)
                ? prev.filter(k => k !== key)
                : [...prev, key]
        );
    }, []);

    const toggleRowSelection = useCallback((e, rowId) => {
        e.stopPropagation();
        setSelectedRows(prev => {
            const next = new Set(prev);
            if (next.has(rowId)) {
                next.delete(rowId);
            } else {
                next.add(rowId);
            }
            return next;
        });
    }, []);

    // Render pagination buttons
    const renderPaginationButtons = () => {
        const buttons = [];
        const maxButtons = 5;
        let start = Math.max(1, currentPage - Math.floor(maxButtons / 2));
        let end = Math.min(totalPages, start + maxButtons - 1);

        if (end - start + 1 < maxButtons) {
            start = Math.max(1, end - maxButtons + 1);
        }

        if (start > 1) {
            buttons.push(
                <button key={1} onClick={() => setCurrentPage(1)} className="page-btn">1</button>
            );
            if (start > 2) {
                buttons.push(<span key="dots1" className="pagination-dots">…</span>);
            }
        }

        for (let i = start; i <= end; i++) {
            buttons.push(
                <button
                    key={i}
                    onClick={() => setCurrentPage(i)}
                    className={`page-btn ${currentPage === i ? 'active' : ''}`}
                >
                    {i}
                </button>
            );
        }

        if (end < totalPages) {
            if (end < totalPages - 1) {
                buttons.push(<span key="dots2" className="pagination-dots">…</span>);
            }
            buttons.push(
                <button key={totalPages} onClick={() => setCurrentPage(totalPages)} className="page-btn">
                    {totalPages}
                </button>
            );
        }

        return buttons;
    };

    // Get active columns
    const activeColumns = COLUMNS.filter(col => visibleColumns.includes(col.key));

    // Loading skeleton
    if (isLoading) {
        return (
            <div className="results-table-container">
                <div className="results-table-header">
                    <div className="results-table-title">
                        <h3>{title}</h3>
                    </div>
                </div>
                <div className="results-loading">
                    <div className="loading-spinner" />
                    <div className="loading-text">
                        <span>L</span><span>o</span><span>a</span><span>d</span><span>i</span><span>n</span><span>g</span>
                        <span> </span>
                        <span>s</span><span>t</span><span>a</span><span>r</span><span>s</span>
                        <span>.</span><span>.</span><span>.</span>
                    </div>
                </div>
            </div>
        );
    }

    // Empty state
    if (data.length === 0) {
        return (
            <div className="results-table-container">
                <div className="results-table-header">
                    <div className="results-table-title">
                        <h3>{title}</h3>
                    </div>
                </div>
                <div className="results-empty">
                    <div className="empty-icon">
                        <Database size={28} />
                    </div>
                    <div className="empty-title">No stellar objects found</div>
                    <div className="empty-description">
                        Try adjusting your search filters or ingesting new data from the upload panel.
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="results-table-container">
            {/* Header */}
            <div className="results-table-header">
                <div className="results-table-title">
                    <h3>{title}</h3>
                    <div className="results-count-badge">
                        <Sparkles size={12} />
                        <span>{sortedData.length.toLocaleString()} objects</span>
                    </div>
                </div>

                <div className="results-table-actions">
                    {showSearch && (
                        <div className="table-search">
                            <Search size={16} className="table-search-icon" />
                            <input
                                type="text"
                                className="table-search-input"
                                placeholder="Search objects..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>
                    )}

                    <div style={{ position: 'relative' }}>
                        <button
                            className="column-toggle-btn"
                            onClick={() => setShowColumnDropdown(!showColumnDropdown)}
                            title="Toggle columns"
                        >
                            <Columns3 size={18} />
                        </button>

                        {showColumnDropdown && (
                            <div className="column-dropdown">
                                <div className="column-dropdown-title">Visible Columns</div>
                                {COLUMNS.map(col => (
                                    <div
                                        key={col.key}
                                        className={`column-option ${visibleColumns.includes(col.key) ? 'checked' : ''}`}
                                        onClick={() => toggleColumn(col.key)}
                                    >
                                        <div className="column-checkbox">
                                            <Check size={12} />
                                        </div>
                                        <span className="column-label">{col.label}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Table */}
            <div className="results-table-scroll">
                <table className="results-table">
                    <thead>
                        <tr>
                            {activeColumns.map(col => (
                                <th
                                    key={col.key}
                                    className={sortConfig.key === col.key ? 'sorted' : ''}
                                    onClick={() => col.sortable && handleSort(col.key)}
                                >
                                    <div className="th-content">
                                        <span>{col.label}</span>
                                        {col.sortable && (
                                            <div className="sort-indicator">
                                                <div className={`sort-arrow up ${sortConfig.key === col.key && sortConfig.direction === 'asc' ? 'active' : ''}`} />
                                                <div className={`sort-arrow down ${sortConfig.key === col.key && sortConfig.direction === 'desc' ? 'active' : ''}`} />
                                            </div>
                                        )}
                                    </div>
                                </th>
                            ))}
                            <th style={{ width: '80px' }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {paginatedData.map((row, index) => {
                            const isAnomaly = highlightAnomalies && anomalyIds.includes(row.id || row.source_id);
                            const isSelected = selectedRows.has(row.id || row.source_id);

                            return (
                                <tr
                                    key={row.id || row.source_id || index}
                                    className={`${isAnomaly ? 'anomaly' : ''} ${isSelected ? 'selected' : ''}`}
                                    style={{ animationDelay: `${index * 30}ms` }}
                                    onClick={() => handleRowClick(row)}
                                >
                                    {activeColumns.map(col => {
                                        const value = row[col.key];
                                        const formatted = col.format(value);

                                        // Special rendering for certain columns
                                        if (col.key === 'source_id') {
                                            return (
                                                <td key={col.key} className="cell-id">
                                                    {isAnomaly && <AlertTriangle size={12} style={{ marginRight: '0.375rem', color: '#ef4444' }} />}
                                                    {formatted}
                                                </td>
                                            );
                                        }

                                        if (col.key === 'ra_deg' || col.key === 'dec_deg') {
                                            return (
                                                <td key={col.key} className="cell-coordinates">
                                                    {formatted}
                                                </td>
                                            );
                                        }

                                        if (col.key === 'brightness_mag') {
                                            const magClass = getMagnitudeClass(value);
                                            return (
                                                <td key={col.key}>
                                                    <div className="cell-magnitude">
                                                        <span className={`magnitude-indicator magnitude-${magClass}`} />
                                                        <span>{formatted}</span>
                                                    </div>
                                                </td>
                                            );
                                        }

                                        if (col.key === 'original_source') {
                                            const sourceClass = getSourceClass(value);
                                            return (
                                                <td key={col.key}>
                                                    <div className="cell-source">
                                                        <span className={`source-dot source-${sourceClass}`} />
                                                        <span>{formatted}</span>
                                                    </div>
                                                </td>
                                            );
                                        }

                                        return <td key={col.key}>{formatted}</td>;
                                    })}
                                    <td className="cell-actions">
                                        <button
                                            className="view-btn"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleRowClick(row);
                                            }}
                                        >
                                            <Eye size={12} />
                                            View
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            {showPagination && totalPages > 1 && (
                <div className="results-pagination">
                    <div className="pagination-info">
                        Showing <span>{((currentPage - 1) * pageSize) + 1}</span> to{' '}
                        <span>{Math.min(currentPage * pageSize, sortedData.length)}</span> of{' '}
                        <span>{sortedData.length.toLocaleString()}</span> results
                    </div>

                    <div className="pagination-controls">
                        <button
                            className="page-btn nav-btn"
                            onClick={() => setCurrentPage(1)}
                            disabled={currentPage === 1}
                            title="First page"
                        >
                            <ChevronsLeft size={16} />
                        </button>
                        <button
                            className="page-btn nav-btn"
                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                            title="Previous page"
                        >
                            <ChevronLeft size={16} />
                        </button>

                        {renderPaginationButtons()}

                        <button
                            className="page-btn nav-btn"
                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                            disabled={currentPage === totalPages}
                            title="Next page"
                        >
                            <ChevronRight size={16} />
                        </button>
                        <button
                            className="page-btn nav-btn"
                            onClick={() => setCurrentPage(totalPages)}
                            disabled={currentPage === totalPages}
                            title="Last page"
                        >
                            <ChevronsRight size={16} />
                        </button>

                        <select
                            className="page-size-select"
                            value={pageSize}
                            onChange={(e) => {
                                setPageSize(Number(e.target.value));
                                setCurrentPage(1);
                            }}
                        >
                            <option value={10}>10 / page</option>
                            <option value={25}>25 / page</option>
                            <option value={50}>50 / page</option>
                            <option value={100}>100 / page</option>
                        </select>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ResultsTable;
