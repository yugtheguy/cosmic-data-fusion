import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import './CosmicChat.css';

const CosmicChat = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [suggestions, setSuggestions] = useState([]);
    const messagesEndRef = useRef(null);
    const location = useLocation();

    // Scroll to bottom when new messages arrive
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Load context-aware suggestions based on current page
    useEffect(() => {
        loadSuggestions();
    }, [location.pathname]);

    // Load suggestions from localStorage on mount
    useEffect(() => {
        const savedMessages = localStorage.getItem('cosmicChatHistory');
        if (savedMessages) {
            try {
                setMessages(JSON.parse(savedMessages));
            } catch (e) {
                console.error('Failed to load chat history:', e);
            }
        }
    }, []);

    // Save messages to localStorage
    useEffect(() => {
        if (messages.length > 0) {
            localStorage.setItem('cosmicChatHistory', JSON.stringify(messages));
        }
    }, [messages]);

    const loadSuggestions = async () => {
        try {
            const context = getPageContext();
            const response = await fetch(`http://localhost:8000/api/nl-query/suggestions?context=${context}`);
            const data = await response.json();
            setSuggestions(data.suggestions);
        } catch (error) {
            console.error('Failed to load suggestions:', error);
            // Fallback suggestions
            setSuggestions([
                "Show me bright stars near Orion",
                "Fast moving stars",
                "Top 10 fastest stars"
            ]);
        }
    };

    const getPageContext = () => {
        const path = location.pathname;
        if (path.includes('dashboard')) return 'dashboard';
        if (path.includes('timemachine')) return 'timemachine';
        if (path.includes('skymap')) return 'skymap';
        if (path.includes('query')) return 'querybuilder';
        return 'default';
    };

    const convertToCSV = (data) => {
        if (!data || data.length === 0) return '';

        // Get headers from first object
        const headers = Object.keys(data[0]);
        const csvHeaders = headers.join(',');

        // Convert each row
        const csvRows = data.map(row =>
            headers.map(header => {
                const value = row[header];
                // Handle null/undefined
                if (value === null || value === undefined) return '';
                // Escape commas and quotes
                if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                    return `"${value.replace(/"/g, '""')}"`;
                }
                return value;
            }).join(',')
        );

        return [csvHeaders, ...csvRows].join('\n');
    };

    const downloadCSV = (csvContent, filename) => {
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleSendMessage = async (text = inputText) => {
        if (!text.trim()) return;

        // Add user message
        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: text,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, userMessage]);
        setInputText('');
        setIsLoading(true);

        try {
            // Call NL Query API
            const response = await fetch('http://localhost:8000/api/nl-query/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: text,
                    page: 1,
                    page_size: 10
                })
            });

            const data = await response.json();

            // Add AI response
            const aiMessage = {
                id: Date.now() + 1,
                type: 'ai',
                content: data.explanation,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                results: data.results,
                totalCount: data.total_count,
                confidence: data.confidence,
                suggestions: data.suggestions,
                intent: data.intent
            };
            setMessages(prev => [...prev, aiMessage]);
        } catch (error) {
            console.error('Query failed:', error);
            const errorMessage = {
                id: Date.now() + 1,
                type: 'ai',
                content: 'Sorry, I encountered an error processing your query. Please try again.',
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                isError: true
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSuggestionClick = (suggestion) => {
        handleSendMessage(suggestion);
    };

    const handleClearChat = () => {
        setMessages([]);
        localStorage.removeItem('cosmicChatHistory');
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <div className="cosmic-chat-widget">
            {!isOpen ? (
                <button className="chat-toggle-button" onClick={() => setIsOpen(true)}>
                    <span className="chat-icon">🤖</span>
                </button>
            ) : (
                <div className="chat-container">
                    {/* Header */}
                    <div className="chat-header">
                        <div className="chat-title">
                            <span className="chat-title-icon">🌌</span>
                            <span>Cosmic AI Assistant</span>
                        </div>
                        <div className="chat-controls">
                            <button
                                className="chat-control-btn"
                                onClick={handleClearChat}
                                title="Clear conversation"
                            >
                                🗑️
                            </button>
                            <button
                                className="chat-control-btn"
                                onClick={() => setIsOpen(false)}
                                title="Minimize"
                            >
                                ➖
                            </button>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="chat-messages">
                        {messages.length === 0 && (
                            <div className="message ai">
                                <div className="message-avatar">🤖</div>
                                <div className="message-content">
                                    <p>Hello! I'm your Cosmic AI Assistant. Ask me anything about stars!</p>
                                    <div className="suggestion-chips">
                                        {suggestions.map((suggestion, idx) => (
                                            <button
                                                key={idx}
                                                className="suggestion-chip"
                                                onClick={() => handleSuggestionClick(suggestion)}
                                            >
                                                {suggestion}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {messages.map((message) => (
                            <div key={message.id} className={`message ${message.type}`}>
                                <div className="message-avatar">
                                    {message.type === 'user' ? '👤' : '🤖'}
                                </div>
                                <div className="message-content">
                                    <p>{message.content}</p>

                                    {/* Results Display - Card Layout */}
                                    {message.results && message.results.length > 0 && (
                                        <div className="results-container">
                                            <div className="results-header">
                                                <span className="results-icon">✨</span>
                                                <span className="results-title">Found {message.totalCount} stars</span>
                                            </div>
                                            <div className="results-cards">
                                                {message.results.slice(0, 3).map((star, idx) => (
                                                    <div key={idx} className="star-card">
                                                        <div className="star-card-header">
                                                            <span className="star-id">#{star.id}</span>
                                                            <span className="star-magnitude">{star.magnitude?.toFixed(2)} mag</span>
                                                        </div>
                                                        <div className="star-coordinates">
                                                            <div className="coord-item">
                                                                <span className="coord-label">RA</span>
                                                                <span className="coord-value">{star.ra?.toFixed(2)}°</span>
                                                            </div>
                                                            <div className="coord-item">
                                                                <span className="coord-label">DEC</span>
                                                                <span className="coord-value">{star.dec?.toFixed(2)}°</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                            {message.totalCount > 3 && (
                                                <div className="results-footer">
                                                    Showing 3 of {message.totalCount} • <span className="view-all-link">View all →</span>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* Action Buttons */}
                                    {message.results && message.results.length > 0 && (
                                        <div className="result-actions">
                                            <button
                                                className="action-btn"
                                                onClick={() => {
                                                    // Navigate to Sky Map (placeholder - would need to implement)
                                                    console.log('Navigate to Sky Map with filters:', message.filters_applied);
                                                }}
                                            >
                                                🗺️ View on Sky Map
                                            </button>
                                            <button
                                                className="action-btn"
                                                onClick={() => {
                                                    // Navigate to Time Machine with filters
                                                    const filters = message.filters_applied || {};
                                                    const params = new URLSearchParams();

                                                    if (filters.ra_min) params.set('raMin', filters.ra_min);
                                                    if (filters.ra_max) params.set('raMax', filters.ra_max);
                                                    if (filters.dec_min) params.set('decMin', filters.dec_min);
                                                    if (filters.dec_max) params.set('decMax', filters.dec_max);
                                                    if (filters.max_magnitude) params.set('maxMagnitude', filters.max_magnitude);
                                                    if (filters.limit) params.set('limit', filters.limit);
                                                    params.set('autoLoad', 'true');

                                                    window.location.href = `/timemachine?${params.toString()}`;
                                                }}
                                            >
                                                ⏰ Open in Time Machine
                                            </button>
                                            <button
                                                className="action-btn"
                                                onClick={() => {
                                                    // Export to CSV
                                                    const csv = convertToCSV(message.results);
                                                    downloadCSV(csv, `stars_${Date.now()}.csv`);
                                                }}
                                            >
                                                📥 Export CSV
                                            </button>
                                        </div>
                                    )}

                                    {/* Follow-up Suggestions */}
                                    {message.suggestions && message.suggestions.length > 0 && (
                                        <div className="suggestion-chips">
                                            {message.suggestions.map((suggestion, idx) => (
                                                <button
                                                    key={idx}
                                                    className="suggestion-chip"
                                                    onClick={() => handleSuggestionClick(suggestion)}
                                                >
                                                    {suggestion}
                                                </button>
                                            ))}
                                        </div>
                                    )}

                                    <div className="message-timestamp">
                                        {message.timestamp}
                                        {message.confidence && ` • ${(message.confidence * 100).toFixed(0)}% confident`}
                                    </div>
                                </div>
                            </div>
                        ))}

                        {/* Typing Indicator */}
                        {isLoading && (
                            <div className="message ai">
                                <div className="message-avatar">🤖</div>
                                <div className="typing-indicator">
                                    <div className="typing-dot"></div>
                                    <div className="typing-dot"></div>
                                    <div className="typing-dot"></div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="chat-input-area">
                        <div className="chat-input-container">
                            <input
                                type="text"
                                className="chat-input"
                                placeholder="Ask about stars..."
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                onKeyPress={handleKeyPress}
                                disabled={isLoading}
                            />
                            <button
                                className="send-button"
                                onClick={() => handleSendMessage()}
                                disabled={isLoading || !inputText.trim()}
                            >
                                ➤
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CosmicChat;
