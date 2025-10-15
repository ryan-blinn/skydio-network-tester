class NetworkTester {
    constructor() {
        this.currentJobId = null;
        this.pollInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadDeviceInfo();
    }

    bindEvents() {
        // Start test button
        document.getElementById('start-test').addEventListener('click', () => {
            this.startTest();
        });

        // Details buttons
        document.querySelectorAll('.details-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const testType = e.target.closest('.details-btn').dataset.test;
                const card = document.querySelector(`[data-test="${testType}"]`);
                this.toggleCardExpansion(card);
            });
        });

        // Export buttons
        document.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const format = e.target.closest('.export-btn').dataset.format;
                this.exportResults(format);
            });
        });
    }

    async loadDeviceInfo() {
        try {
            const response = await fetch('/api/device-info');
            const data = await response.json();
            document.getElementById('private-ip').textContent = data.private_ip || 'Unknown';
            document.getElementById('public-ip').textContent = data.public_ip || 'Unknown';
        } catch (error) {
            console.error('Failed to load device info:', error);
            document.getElementById('private-ip').textContent = 'Unknown';
            document.getElementById('public-ip').textContent = 'Unknown';
        }
    }

    async startTest() {
        this.resetTestCards();
        this.resetUI();

        const startBtn = document.getElementById('start-test');
        const progressContainer = document.getElementById('progress-container');

        startBtn.disabled = true;
        startBtn.innerHTML = '⏳ Running Tests...';
        console.log('Progress container display:', progressContainer.style.display);
        progressContainer.style.display = 'block';

        try {
            const response = await fetch('/api/start', { method: 'POST' });
            const data = await response.json();
            this.currentJobId = data.job_id;
            this.startPolling();
        } catch (error) {
            console.error('Failed to start test:', error);
            this.testComplete();
        }
    }

    startPolling() {
        this.pollInterval = setInterval(() => {
            this.checkStatus();
        }, 1000);
    }

    async checkStatus() {
        if (!this.currentJobId) return;

        try {
            const response = await fetch(`/api/status/${this.currentJobId}`);
            const data = await response.json();
            
            this.updateProgress(data.progress);
            
            if (data.results) {
                this.updateTestResults(data.results);
            }
            
            if (data.status === 'completed' || data.done === true) {
                this.testComplete();
            }
        } catch (error) {
            console.error('Failed to check status:', error);
            this.testComplete();
        }
    }

    updateProgress(progress) {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        
        console.log('Updating progress to:', progress + '%');
        if (progressFill) progressFill.style.width = `${progress}%`;
        if (progressText) progressText.textContent = `${progress}%`;
    }

    updateTestResults(results) {
        // Show details buttons when tests start
        document.querySelectorAll('.details-btn').forEach(btn => {
            btn.style.display = 'flex';
        });

        // Update each test type
        if (results.dns && results.dns.length > 0) {
            this.updateTestCard('dns', results.dns);
        }
        if (results.tcp && results.tcp.length > 0) {
            this.updateTestCard('tcp', results.tcp);
        }
        if (results.quic && results.quic.length > 0) {
            this.updateTestCard('quic', results.quic);
        }
        if (results.ping && results.ping.length > 0) {
            this.updateTestCard('ping', results.ping);
        }
        if (results.ntp) {
            this.updateTestCard('ntp', [results.ntp]);
        }
        if (results.speedtest) {
            this.updateTestCard('speedtest', [results.speedtest]);
            this.updateSpeedResults(results.speedtest);
        }
    }

    updateTestCard(testType, testResults) {
        const statusElement = document.getElementById(`${testType}-status`);
        const detailsElement = document.getElementById(`${testType}-details`);
        
        if (!statusElement || !detailsElement) return;

        // Determine overall status
        const allPassed = testResults.every(result => result.status === 'PASS');
        const anyFailed = testResults.some(result => result.status === 'FAIL');
        const anyWarning = testResults.some(result => result.status === 'WARN');
        
        let statusClass = 'running';
        if (allPassed && testResults.length > 0) {
            statusClass = 'pass';
        } else if (anyWarning && !anyFailed) {
            statusClass = 'pass';
        } else if (anyFailed) {
            statusClass = 'fail';
        }

        // Update status indicator
        const indicator = statusElement.querySelector('.status-indicator');
        if (indicator) {
            indicator.className = `status-indicator ${statusClass}`;
        }

        // Update details content
        this.updateDetailsContent(detailsElement, testType, testResults);
    }

    updateDetailsContent(detailsElement, testType, testResults) {
        const content = detailsElement.querySelector('.details-content');
        if (!content) return;

        // Calculate summary stats
        const totalTests = testResults.length;
        const passedTests = testResults.filter(r => r.status === 'PASS').length;
        const failedTests = testResults.filter(r => r.status === 'FAIL').length;
        const warnTests = testResults.filter(r => r.status === 'WARN').length;

        let html = `
            <div class="details-summary">
                <h4>${this.getTestTypeTitle(testType)} Results</h4>
                <div class="summary-stats">
                    <span class="stat-item pass">✓ ${passedTests} Passed</span>
                    ${warnTests > 0 ? `<span class="stat-item warn">⚠ ${warnTests} Warning</span>` : ''}
                    ${failedTests > 0 ? `<span class="stat-item fail">✗ ${failedTests} Failed</span>` : ''}
                </div>
            </div>
            <div class="details-list">
        `;

        testResults.forEach((result, index) => {
            const label = this.getTestLabel(testType, result, index);
            const statusIcon = result.status === 'PASS' ? '✓' : result.status === 'WARN' ? '⚠' : '✗';
            const statusClass = result.status.toLowerCase();

            html += `
                <div class="detail-item">
                    <div class="detail-header">
                        <span class="detail-status ${statusClass}">${statusIcon}</span>
                        <span class="detail-label">${label}</span>
                    </div>
            `;

            // Add specific details based on test type
            if (testType === 'dns' && result.ip) {
                html += `<div class="detail-value">Resolved to: ${result.ip}</div>`;
            } else if (testType === 'tcp' && result.latency_ms) {
                html += `<div class="detail-value">Latency: ${result.latency_ms}ms</div>`;
            } else if (testType === 'quic') {
                if (result.latency_ms) {
                    html += `<div class="detail-value">Latency: ${result.latency_ms}ms</div>`;
                }
                if (result.protocol) {
                    html += `<div class="detail-value">Protocol: ${result.protocol}</div>`;
                }
            } else if (testType === 'ping' && result.output) {
                html += `<div class="detail-value">${result.output}</div>`;
            } else if (testType === 'ntp' && result.offset_ms !== undefined) {
                html += `<div class="detail-value">Offset: ${result.offset_ms}ms</div>`;
            } else if (testType === 'speedtest') {
                if (result.download_mbps) {
                    html += `<div class="detail-value">Download: ${result.download_mbps} Mbps</div>`;
                }
                if (result.upload_mbps) {
                    html += `<div class="detail-value">Upload: ${result.upload_mbps} Mbps</div>`;
                }
            }

            if (result.error) {
                html += `<div class="detail-value error">Error: ${result.error}</div>`;
            }

            html += `</div>`;
        });

        html += `</div>`;
        content.innerHTML = html;
    }

    updateSpeedResults(speedResult) {
        const speedResultsPanel = document.getElementById('speed-results');
        const downloadSpeed = document.getElementById('download-speed');
        const uploadSpeed = document.getElementById('upload-speed');

        if (speedResult && (speedResult.download_mbps || speedResult.upload_mbps)) {
            downloadSpeed.textContent = `${speedResult.download_mbps || '--'} Mbps`;
            uploadSpeed.textContent = `${speedResult.upload_mbps || '--'} Mbps`;
            speedResultsPanel.style.display = 'flex';
        }
    }

    getTestTypeTitle(testType) {
        const titles = {
            'dns': 'DNS Resolution',
            'tcp': 'TCP Connectivity',
            'quic': 'QUIC Protocol',
            'ping': 'Ping Tests',
            'ntp': 'Time Sync',
            'speedtest': 'Speed Test'
        };
        return titles[testType] || 'Test';
    }

    getTestLabel(testType, result, index) {
        switch (testType) {
            case 'dns':
                return result.target || `DNS Test ${index + 1}`;
            case 'tcp':
                return result.label || result.target || `TCP Test ${index + 1}`;
            case 'quic':
                return result.label || result.target || `QUIC Test ${index + 1}`;
            case 'ping':
                return result.target || `Ping Test ${index + 1}`;
            case 'ntp':
                return result.target || 'NTP Server';
            case 'speedtest':
                return result.source || 'Speed Test';
            default:
                return `Test ${index + 1}`;
        }
    }

    toggleCardExpansion(card) {
        const isExpanded = card.classList.contains('expanded');
        
        // Close all other cards
        document.querySelectorAll('.test-card').forEach(c => {
            c.classList.remove('expanded');
        });

        // Toggle current card
        if (!isExpanded) {
            card.classList.add('expanded');
        }
    }

    testComplete() {
        clearInterval(this.pollInterval);
        this.pollInterval = null;

        const startBtn = document.getElementById('start-test');
        const exportPanel = document.getElementById('export-panel');
        const progressContainer = document.getElementById('progress-container');

        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="fas fa-play"></i> Start Network Test';
        exportPanel.style.display = 'block';
        progressContainer.style.display = 'none';

        // Force final status update for all indicators
        document.querySelectorAll('.status-indicator.running').forEach(indicator => {
            indicator.classList.remove('running');
            indicator.classList.add('pending');
        });
    }

    resetTestCards() {
        // Reset status indicators
        document.querySelectorAll('.status-indicator').forEach(indicator => {
            indicator.className = 'status-indicator pending';
        });

        // Collapse all cards
        document.querySelectorAll('.test-card').forEach(card => {
            card.classList.remove('expanded');
        });

        // Clear details content
        document.querySelectorAll('.details-content').forEach(content => {
            content.innerHTML = '';
        });

        // Hide details buttons
        document.querySelectorAll('.details-btn').forEach(btn => {
            btn.style.display = 'none';
        });

        // Hide speed results
        const speedResults = document.getElementById('speed-results');
        if (speedResults) {
            speedResults.style.display = 'none';
        }

        // Reset speed values
        const downloadSpeed = document.getElementById('download-speed');
        const uploadSpeed = document.getElementById('upload-speed');
        if (downloadSpeed) downloadSpeed.textContent = '-- Mbps';
        if (uploadSpeed) uploadSpeed.textContent = '-- Mbps';
    }

    resetUI() {
        const startBtn = document.getElementById('start-test');
        const progressContainer = document.getElementById('progress-container');
        const exportPanel = document.getElementById('export-panel');
        const speedResults = document.getElementById('speed-results');

        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="fas fa-play"></i> Start Network Test';
        progressContainer.style.display = 'none';
        exportPanel.style.display = 'none';
        if (speedResults) speedResults.style.display = 'none';
    }

    async exportResults(format) {
        if (!this.currentJobId) {
            alert('No test results to export');
            return;
        }

        const siteLabel = document.getElementById('site-label').value;
        const url = `/api/export/${format}/${this.currentJobId}${siteLabel ? `?site_label=${encodeURIComponent(siteLabel)}` : ''}`;

        try {
            const response = await fetch(url, { method: 'POST' });
            const data = await response.json();
            
            if (data.filename) {
                // Download the file
                window.location.href = `/download/${data.filename}`;
            }
        } catch (error) {
            console.error('Export failed:', error);
            alert('Export failed. Please try again.');
        }
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new NetworkTester();
    initDropdown();
});

// Dropdown menu functionality
function initDropdown() {
    const moreBtn = document.getElementById('more-btn');
    const dropdown = moreBtn?.closest('.dropdown');
    
    if (!moreBtn || !dropdown) return;
    
    // Toggle dropdown on button click
    moreBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('active');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    });
    
    // Close dropdown when clicking a menu item
    dropdown.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', () => {
            dropdown.classList.remove('active');
        });
    });
}
