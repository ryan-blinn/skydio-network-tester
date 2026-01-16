// Test History Management
let historyData = [];
let currentTestDetails = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadDeviceInfo();
    loadHistory();
    setupSearchFilter();
});

// Load device information
async function loadDeviceInfo() {
    try {
        const response = await fetch('/api/info');
        const data = await response.json();
        document.getElementById('private-ip').textContent = data.private_ip || 'Unknown';
        document.getElementById('public-ip').textContent = data.public_ip || 'Unknown';
    } catch (error) {
        console.error('Failed to load device info:', error);
    }
}

// Load test history
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        historyData = await response.json();
        
        if (historyData.error) {
            showError('Failed to load history: ' + historyData.error);
            return;
        }
        
        updateStats();
        renderHistory();
    } catch (error) {
        console.error('Failed to load history:', error);
        showError('Failed to load test history');
    }
}

// Update statistics
function updateStats() {
    let totalTests = 0;
    let totalPassed = 0;
    let totalWarnings = 0;
    let totalFailed = 0;
    
    historyData.forEach(entry => {
        if (entry.summary) {
            totalTests += entry.summary.total_tests || 0;
            totalPassed += entry.summary.passed || 0;
            totalWarnings += entry.summary.warnings || 0;
            totalFailed += entry.summary.failed || 0;
        }
    });
    
    document.getElementById('total-tests').textContent = totalTests;
    document.getElementById('total-passed').textContent = totalPassed;
    document.getElementById('total-warnings').textContent = totalWarnings;
    document.getElementById('total-failed').textContent = totalFailed;
}

// Render history list
function renderHistory(filteredData = null) {
    const historyList = document.getElementById('history-list');
    const data = filteredData || historyData;
    
    if (data.length === 0) {
        historyList.innerHTML = `
            <div class="empty-message">
                <i class="fas fa-inbox"></i>
                <p>No test history available</p>
                <p style="font-size: 0.9rem; margin-top: 0.5rem;">Run a network test to see results here</p>
            </div>
        `;
        return;
    }
    
    historyList.innerHTML = data.map(entry => `
        <div class="history-item" onclick="viewTestDetails(${entry.timestamp})">
            <div class="history-item-header">
                <div class="history-item-info">
                    <div class="history-item-title">
                        <i class="fas fa-network-wired"></i> Network Test - ${entry.datetime}
                    </div>
                    <div class="history-item-meta">
                        <span><img class="device-info-icon" src="/static/images/skydio-mark.png" alt="Skydio"> ${entry.private_ip || entry.device_name}</span>
                        <span><i class="fas fa-globe"></i> ${entry.public_ip}</span>
                        <span><i class="fas fa-clock"></i> ${formatRelativeTime(entry.timestamp)}</span>
                    </div>
                </div>
                <div class="history-item-actions" onclick="event.stopPropagation()">
                    <button class="icon-btn" onclick="exportTest(${entry.timestamp})" title="Export">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="icon-btn delete" onclick="deleteTest(${entry.timestamp})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="history-item-summary">
                <div class="summary-badge total">
                    <i class="fas fa-clipboard-list"></i>
                    ${entry.summary?.total_tests || 0} Tests
                </div>
                <div class="summary-badge passed">
                    <i class="fas fa-check-circle"></i>
                    ${entry.summary?.passed || 0} Passed
                </div>
                ${entry.summary?.warnings > 0 ? `
                    <div class="summary-badge warnings">
                        <i class="fas fa-exclamation-triangle"></i>
                        ${entry.summary.warnings} Warnings
                    </div>
                ` : ''}
                ${entry.summary?.failed > 0 ? `
                    <div class="summary-badge failed">
                        <i class="fas fa-times-circle"></i>
                        ${entry.summary.failed} Failed
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// Format relative time
function formatRelativeTime(timestamp) {
    const now = Date.now() / 1000;
    const diff = now - timestamp;
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)} days ago`;
    return `${Math.floor(diff / 604800)} weeks ago`;
}

// View test details
async function viewTestDetails(timestamp) {
    try {
        const response = await fetch(`/api/history/${timestamp}`);
        const data = await response.json();
        
        if (data.error) {
            showError('Failed to load test details: ' + data.error);
            return;
        }
        
        currentTestDetails = data;
        showDetailsModal(data);
    } catch (error) {
        console.error('Failed to load test details:', error);
        showError('Failed to load test details');
    }
}

// Show details modal
function showDetailsModal(data) {
    const modal = document.getElementById('details-modal');
    const modalBody = document.getElementById('modal-body');
    
    const results = data.results;
    
    let html = `
        <div class="test-section">
            <h3><i class="fas fa-info-circle"></i> Test Information</h3>
            <div class="test-result-item">
                <div class="test-result-details">
                    <div><strong>Date:</strong> ${data.datetime}</div>
                    <div><strong>Device:</strong> ${data.device_name}</div>
                    <div><strong>Private IP:</strong> ${data.private_ip || 'Unknown'}</div>
                    <div><strong>Public IP:</strong> ${data.public_ip}</div>
                </div>
            </div>
        </div>
    `;
    
    // DNS Results
    if (results.dns && results.dns.length > 0) {
        html += `
            <div class="test-section">
                <h3><i class="fas fa-search"></i> DNS Resolution</h3>
                ${results.dns.map(test => `
                    <div class="test-result-item ${test.status ? test.status.toLowerCase() : ''}">
                        <div class="test-result-header">
                            <div class="test-result-name">${test.target}</div>
                            <span class="status-badge ${test.status.toLowerCase()}">${test.status}</span>
                        </div>
                        <div class="test-result-details">
                            ${test.ip ? `<div><strong>Resolved:</strong> ${test.ip}</div>` : ''}
                            ${test.latency_ms !== undefined ? `<div><strong>Latency:</strong> ${test.latency_ms} ms</div>` : ''}
                            ${test.error ? `<div style="color: #f44336;"><strong>Error:</strong> ${test.error}</div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // TCP Results
    if (results.tcp && results.tcp.length > 0) {
        html += `
            <div class="test-section">
                <h3><i class="fas fa-plug"></i> TCP Connectivity</h3>
                ${results.tcp.map(test => `
                    <div class="test-result-item ${test.status ? test.status.toLowerCase() : ''}">
                        <div class="test-result-header">
                            <div class="test-result-name">${test.label || `${test.host}:${test.port}`}</div>
                            <span class="status-badge ${test.status.toLowerCase()}">${test.status}</span>
                        </div>
                        <div class="test-result-details">
                            <div><strong>Target:</strong> ${test.target || ''}</div>
                            ${test.latency_ms !== undefined ? `<div><strong>Latency:</strong> ${test.latency_ms} ms</div>` : ''}
                            ${test.error ? `<div style="color: #f44336;"><strong>Error:</strong> ${test.error}</div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // QUIC Results
    if (results.quic && results.quic.length > 0) {
        html += `
            <div class="test-section">
                <h3><i class="fas fa-bolt"></i> QUIC Protocol</h3>
                ${results.quic.map(test => `
                    <div class="test-result-item ${test.status ? test.status.toLowerCase() : ''}">
                        <div class="test-result-header">
                            <div class="test-result-name">${test.label || `${test.host}:${test.port}`}</div>
                            <span class="status-badge ${test.status.toLowerCase()}">${test.status}</span>
                        </div>
                        <div class="test-result-details">
                            <div><strong>Host:</strong> ${test.host}:${test.port}</div>
                            ${test.error ? `<div style="color: #f44336;"><strong>Error:</strong> ${test.error}</div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Ping Results
    if (results.ping && results.ping.length > 0) {
        html += `
            <div class="test-section">
                <h3><i class="fas fa-satellite-dish"></i> Ping Tests</h3>
                ${results.ping.map(test => `
                    <div class="test-result-item ${test.status ? test.status.toLowerCase() : ''}">
                        <div class="test-result-header">
                            <div class="test-result-name">${test.target}</div>
                            <span class="status-badge ${test.status.toLowerCase()}">${test.status}</span>
                        </div>
                        <div class="test-result-details">
                            ${test.avg_ms ? `<div><strong>Average:</strong> ${test.avg_ms.toFixed(2)} ms</div>` : ''}
                            ${test.min_ms ? `<div><strong>Min:</strong> ${test.min_ms.toFixed(2)} ms</div>` : ''}
                            ${test.max_ms ? `<div><strong>Max:</strong> ${test.max_ms.toFixed(2)} ms</div>` : ''}
                            ${test.packet_loss !== undefined ? `<div><strong>Packet Loss:</strong> ${test.packet_loss}%</div>` : ''}
                            ${test.error ? `<div style="color: #f44336;"><strong>Error:</strong> ${test.error}</div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // NTP Result
    if (results.ntp) {
        html += `
            <div class="test-section">
                <h3><i class="fas fa-clock"></i> Time Synchronization</h3>
                <div class="test-result-item ${results.ntp.status ? results.ntp.status.toLowerCase() : ''}">
                    <div class="test-result-header">
                        <div class="test-result-name">${results.ntp.target || 'NTP'}</div>
                        <span class="status-badge ${results.ntp.status.toLowerCase()}">${results.ntp.status}</span>
                    </div>
                    <div class="test-result-details">
                        ${results.ntp.offset_ms !== undefined ? `<div><strong>Offset:</strong> ${results.ntp.offset_ms} ms</div>` : ''}
                        ${results.ntp.error ? `<div style="color: #f44336;"><strong>Error:</strong> ${results.ntp.error}</div>` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    // Speed Test Result
    if (results.speedtest) {
        html += `
            <div class="test-section">
                <h3><i class="fas fa-tachometer-alt"></i> Speed Test</h3>
                <div class="test-result-item ${results.speedtest.status ? results.speedtest.status.toLowerCase() : ''}">
                    <div class="test-result-header">
                        <div class="test-result-name">Bandwidth Test</div>
                        <span class="status-badge ${results.speedtest.status.toLowerCase()}">${results.speedtest.status}</span>
                    </div>
                    <div class="test-result-details">
                        ${results.speedtest.download_mbps !== undefined ? `<div><strong>Download:</strong> ${results.speedtest.download_mbps} Mbps</div>` : ''}
                        ${results.speedtest.upload_mbps !== undefined ? `<div><strong>Upload:</strong> ${results.speedtest.upload_mbps} Mbps</div>` : ''}
                        ${results.speedtest.error ? `<div style="color: #f44336;"><strong>Error:</strong> ${results.speedtest.error}</div>` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    modalBody.innerHTML = html;
    modal.style.display = 'flex';
}

// Close details modal
function closeDetailsModal() {
    document.getElementById('details-modal').style.display = 'none';
    currentTestDetails = null;
}

// Export current test from modal
function exportCurrentTest() {
    if (currentTestDetails) {
        exportTest(currentTestDetails.timestamp);
    }
}

// Export test
async function exportTest(timestamp) {
    // For now, just download the JSON
    try {
        const response = await fetch(`/api/history/${timestamp}`);
        const data = await response.json();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `test_${timestamp}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showSuccess('Test exported successfully');
    } catch (error) {
        console.error('Failed to export test:', error);
        showError('Failed to export test');
    }
}

// Delete test
async function deleteTest(timestamp) {
    if (!confirm('Are you sure you want to delete this test?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/history/${timestamp}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.error) {
            showError('Failed to delete test: ' + data.error);
            return;
        }
        
        showSuccess('Test deleted successfully');
        loadHistory();
    } catch (error) {
        console.error('Failed to delete test:', error);
        showError('Failed to delete test');
    }
}

// Clear all history
async function clearAllHistory() {
    if (!confirm('Are you sure you want to clear all test history? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/history/clear', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.error) {
            showError('Failed to clear history: ' + data.error);
            return;
        }
        
        showSuccess('History cleared successfully');
        loadHistory();
    } catch (error) {
        console.error('Failed to clear history:', error);
        showError('Failed to clear history');
    }
}

// Refresh history
function refreshHistory() {
    loadHistory();
    showSuccess('History refreshed');
}

// Setup search filter
function setupSearchFilter() {
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        
        if (!query) {
            renderHistory();
            return;
        }
        
        const filtered = historyData.filter(entry => {
            return entry.device_name.toLowerCase().includes(query) ||
                   (entry.private_ip && entry.private_ip.toLowerCase().includes(query)) ||
                   entry.public_ip.toLowerCase().includes(query) ||
                   entry.datetime.toLowerCase().includes(query);
        });
        
        renderHistory(filtered);
    });
}

// Show success message
function showSuccess(message) {
    // Simple alert for now - could be replaced with a toast notification
    console.log('Success:', message);
}

// Show error message
function showError(message) {
    alert(message);
}

// Close modal on outside click
document.addEventListener('click', (e) => {
    const modal = document.getElementById('details-modal');
    if (e.target === modal) {
        closeDetailsModal();
    }
});
