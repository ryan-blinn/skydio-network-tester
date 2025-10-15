class SkydioNetworkTester {
    constructor() {
        this.currentJobId = null;
        this.pollInterval = null;
        this.init();
    }

    init() {
        this.loadDeviceInfo();
        this.bindEvents();
    }

    async loadDeviceInfo() {
        try {
            const response = await fetch('/api/info');
            const data = await response.json();
            document.getElementById('device-name').textContent = data.device_name;
            document.getElementById('public-ip').textContent = data.public_ip;
        } catch (error) {
            console.error('Failed to load device info:', error);
            document.getElementById('device-name').textContent = 'Unknown';
            document.getElementById('public-ip').textContent = 'Unknown';
        }
    }

    bindEvents() {
        // Start test button
        document.getElementById('start-test').addEventListener('click', () => {
            this.startTest();
        });

        // Details button click handlers
        document.querySelectorAll('.details-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const testType = btn.dataset.test;
                const card = btn.closest('.test-card');
                this.toggleCardExpansion(card);
            });
        });

        // Export button handlers
        document.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const format = btn.dataset.format;
                this.exportResults(format);
            });
        });
    }

    async startTest() {
        const startBtn = document.getElementById('start-test');
        const progressContainer = document.getElementById('progress-container');
        const exportPanel = document.getElementById('export-panel');

        // Reset UI
        startBtn.disabled = true;
        startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting Test...';
        progressContainer.style.display = 'flex';
        exportPanel.style.display = 'none';
        this.resetTestCards();

        try {
            // Start the test
            const response = await fetch('/api/start', { method: 'POST' });
            const data = await response.json();
            this.currentJobId = data.job_id;

            // Start polling for updates
            this.startPolling();

        } catch (error) {
            console.error('Failed to start test:', error);
            this.resetUI();
            alert('Failed to start network test. Please try again.');
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
            
            if (data.status === 'completed') {
                // Force final update of all test results
                if (data.results) {
                    this.finalizeTestResults(data.results);
                }
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
        
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `${progress}%`;
    }

    updateTestResults(results) {
        // Set all cards to running state first
        document.querySelectorAll('.status-indicator').forEach(indicator => {
            if (!indicator.classList.contains('pass') && !indicator.classList.contains('fail')) {
                indicator.className = 'status-indicator running';
            }
        });

        // Update DNS tests
        if (results.dns && results.dns.length > 0) {
            this.updateTestCard('dns', results.dns);
        }

        // Update TCP tests
        if (results.tcp && results.tcp.length > 0) {
            this.updateTestCard('tcp', results.tcp);
        }

        // Update Ping tests
        if (results.ping && results.ping.length > 0) {
            this.updateTestCard('ping', results.ping);
        }

        // Update NTP test
        if (results.ntp) {
            this.updateTestCard('ntp', [results.ntp]);
        }

        // Update Speed test
        if (results.speedtest) {
            this.updateTestCard('speedtest', [results.speedtest]);
            this.updateSpeedResults(results.speedtest);
        }
    }

    finalizeTestResults(results) {
        // Force update all test cards with final results
        if (results.dns && results.dns.length > 0) {
            this.updateTestCard('dns', results.dns);
        }
        if (results.tcp && results.tcp.length > 0) {
            this.updateTestCard('tcp', results.tcp);
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

        // Determine overall status - updated for real data format
        const allPassed = testResults.every(result => result.status === 'PASS');
        const anyFailed = testResults.some(result => result.status === 'FAIL');
        const anyWarning = testResults.some(result => result.status === 'WARN');
        
        let statusClass = 'running';
        if (allPassed && testResults.length > 0) {
            statusClass = 'pass';
        } else if (anyWarning && !anyFailed) {
            statusClass = 'pass'; // Treat WARN as pass but could be different color
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

        // Calculate summary stats - updated for real data format
        const totalTests = testResults.length;
        const passedTests = testResults.filter(r => r.status === 'PASS').length;
        const failedTests = testResults.filter(r => r.status === 'FAIL').length;

        let html = `
            <div class="details-header">
                <span>${this.getTestTypeTitle(testType)} Results</span>
                <div class="details-summary">
                    <div class="summary-item pass">
                        <i class="fas fa-check-circle"></i>
                        ${passedTests} Passed
                    </div>
                    <div class="summary-item fail">
                        <i class="fas fa-times-circle"></i>
                        ${failedTests} Failed
                    </div>
                </div>
            </div>
        `;

        testResults.forEach((result, index) => {
            const isSuccess = result.status === 'PASS';
            const statusIcon = isSuccess ? 'fas fa-check-circle' : 'fas fa-times-circle';
            const statusClass = isSuccess ? 'success' : 'error';

            html += `
                <div class="detail-item">
                    <div class="detail-label">
                        ${this.getTestLabel(testType, result, index)}
                    </div>
                    <div class="detail-status ${statusClass}">
                        <i class="${statusIcon}"></i>
                        ${isSuccess ? 'Pass' : 'Fail'}
                    </div>
                </div>
            `;

            // Add additional details based on test type
            if (testType === 'ping' && result.output) {
                html += `
                    <div class="detail-item">
                        <div class="detail-label">Ping Output</div>
                        <div class="detail-value">${result.output}</div>
                    </div>
                `;
            }

            if (testType === 'dns' && result.ip) {
                html += `
                    <div class="detail-item">
                        <div class="detail-label">Resolved IP</div>
                        <div class="detail-value">${result.ip}</div>
                    </div>
                `;
            }

            if (testType === 'dns' && result.latency_ms !== undefined) {
                html += `
                    <div class="detail-item">
                        <div class="detail-label">DNS Latency</div>
                        <div class="detail-value">${result.latency_ms}ms</div>
                    </div>
                `;
            }

            if (testType === 'tcp' && result.latency_ms !== undefined) {
                html += `
                    <div class="detail-item">
                        <div class="detail-label">Connection Latency</div>
                        <div class="detail-value">${result.latency_ms}ms</div>
                    </div>
                `;
            }

            if (testType === 'ntp' && result.offset_ms !== undefined) {
                html += `
                    <div class="detail-item">
                        <div class="detail-label">Time Offset</div>
                        <div class="detail-value">${result.offset_ms}ms</div>
                    </div>
                `;
            }

            if (testType === 'speedtest' && result.download_mbps !== undefined) {
                html += `
                    <div class="detail-item">
                        <div class="detail-label">Download Speed</div>
                        <div class="detail-value">${result.download_mbps} Mbps</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Upload Speed</div>
                        <div class="detail-value">${result.upload_mbps} Mbps</div>
                    </div>
                `;
                
                if (result.source) {
                    html += `
                        <div class="detail-item">
                            <div class="detail-label">Test Source</div>
                            <div class="detail-value">${result.source}</div>
                        </div>
                    `;
                }
            }

            if (result.error) {
                html += `
                    <div class="detail-item">
                        <div class="detail-label">Error Details</div>
                        <div class="detail-value" style="color: var(--skydio-red);">${result.error}</div>
                    </div>
                `;
            }
        });

        content.innerHTML = html;
    }

    getTestTypeTitle(testType) {
        switch (testType) {
            case 'dns': return 'DNS Resolution';
            case 'tcp': return 'TCP Connectivity';
            case 'ping': return 'Ping Tests';
            case 'ntp': return 'Time Sync';
            case 'speedtest': return 'Speed Test';
            default: return 'Test';
        }
    }

    getTestLabel(testType, result, index) {
        switch (testType) {
            case 'dns':
                return result.target || `DNS Test ${index + 1}`;
            case 'tcp':
                return result.label || result.target || `TCP Test ${index + 1}`;
            case 'ping':
                return result.target || `Ping Test ${index + 1}`;
            case 'ntp':
                return result.target || 'NTP Server';
            case 'speedtest':
                return 'Bandwidth Test';
            default:
                return `Test ${index + 1}`;
        }
    }

    updateSpeedResults(speedResult) {
        const speedResultsPanel = document.getElementById('speed-results');
        const downloadSpeed = document.getElementById('download-speed');
        const uploadSpeed = document.getElementById('upload-speed');

        if (speedResult && speedResult.download_mbps !== undefined && speedResult.upload_mbps !== undefined) {
            downloadSpeed.textContent = `${speedResult.download_mbps} Mbps`;
            uploadSpeed.textContent = `${speedResult.upload_mbps} Mbps`;
            speedResultsPanel.style.display = 'flex';
        }
    }

    toggleCardExpansion(card) {
        const isExpanded = card.classList.contains('expanded');
        
        // Close all other cards
        document.querySelectorAll('.test-card').forEach(c => {
            c.classList.remove('expanded');
        });

        // Toggle this card
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

        // Force update all status indicators to remove running state
        document.querySelectorAll('.status-indicator.running').forEach(indicator => {
            indicator.className = 'status-indicator pending';
        });
    }

    resetTestCards() {
        document.querySelectorAll('.status-indicator').forEach(indicator => {
            indicator.className = 'status-indicator pending';
        });

        document.querySelectorAll('.test-card').forEach(card => {
            card.classList.remove('expanded');
        });

        document.querySelectorAll('.details-content').forEach(content => {
            content.innerHTML = '';
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
                window.open(`/download/${data.filename}`, '_blank');
            } else {
                alert('Export failed: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Export failed:', error);
            alert('Export failed. Please try again.');
        }
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SkydioNetworkTester();
});
