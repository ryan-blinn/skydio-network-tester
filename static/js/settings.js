class SettingsManager {
    constructor() {
        this.adminToken = this.getStoredAdminToken();
        this.init();
    }

    getStoredAdminToken() {
        try {
            return localStorage.getItem('skydio_admin_token') || '';
        } catch (e) {
            return '';
        }
    }

    setStoredAdminToken(token) {
        this.adminToken = token || '';
        try {
            if (this.adminToken) {
                localStorage.setItem('skydio_admin_token', this.adminToken);
            } else {
                localStorage.removeItem('skydio_admin_token');
            }
        } catch (e) {
        }
    }

    _jsonHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (this.adminToken) {
            headers['X-Admin-Token'] = this.adminToken;
        }
        return headers;
    }

    async _postJsonWithAdminRetry(url, payload, successMessage) {
        const body = JSON.stringify(payload || {});

        let response = await fetch(url, {
            method: 'POST',
            headers: this._jsonHeaders(),
            body
        });

        if (response.status === 403) {
            let err = 'Remote changes require admin token';
            try {
                const data = await response.json();
                if (data && data.error) err = data.error;
            } catch (e) {
            }

            const entered = prompt(`${err}\n\nEnter admin token to allow remote changes:`, this.adminToken || '');
            if (entered) {
                this.setStoredAdminToken(entered);
                response = await fetch(url, {
                    method: 'POST',
                    headers: this._jsonHeaders(),
                    body
                });
            }
        }

        if (response.ok) {
            if (successMessage) this.showNotification(successMessage, 'success');
            return true;
        }

        let msg = 'Request failed';
        try {
            const data = await response.json();
            if (data && data.error) msg = data.error;
        } catch (e) {
        }
        this.showNotification(msg, 'error');
        return false;
    }

    init() {
        // Setup event listeners immediately since DOM should be ready
        this.setupEventListeners();
        this.loadDeviceInfo();
        this.loadCurrentSettings();
        this.loadSystemStatus();
    }
    
    setupEventListeners() {
        // Navigation - attach directly
        const navItems = document.querySelectorAll('.nav-item');
        console.log('Setting up event listeners for', navItems.length, 'nav items');
        
        if (navItems.length === 0) {
            console.error('No navigation items found!');
            return;
        }
        
        navItems.forEach((item, index) => {
            console.log(`Attaching listener to nav item ${index}:`, item.dataset.section);
            
            // Remove any existing listeners by cloning
            const newItem = item.cloneNode(true);
            item.parentNode.replaceChild(newItem, item);
            
            // Add new listener
            newItem.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const section = newItem.dataset.section;
                console.log('Nav item clicked:', section);
                this.showSection(section);
            });
        });
        
        console.log('Event listeners attached successfully');

        // Interface tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const interface = e.currentTarget.dataset.interface;
                this.showInterface(interface);
            });
        });

        // Checkbox toggles with null checks
        const ftpEnabled = document.getElementById('ftp-enabled');
        if (ftpEnabled) {
            ftpEnabled.addEventListener('change', (e) => {
                const ftpConfig = document.getElementById('ftp-config');
                if (ftpConfig) {
                    ftpConfig.style.display = e.target.checked ? 'block' : 'none';
                }
            });
        }

        const webAuthEnabled = document.getElementById('web-auth-enabled');
        if (webAuthEnabled) {
            webAuthEnabled.addEventListener('change', (e) => {
                const authConfig = document.getElementById('auth-config');
                if (authConfig) {
                    authConfig.style.display = e.target.checked ? 'block' : 'none';
                }
            });
        }

        const databricksEnabled = document.getElementById('databricks-enabled');
        if (databricksEnabled) {
            databricksEnabled.addEventListener('change', (e) => {
                const databricksConfig = document.getElementById('databricks-config');
                if (databricksConfig) {
                    databricksConfig.style.display = e.target.checked ? 'block' : 'none';
                }
            });
        }

        // Settings button in main app
        const settingsBtn = document.getElementById('settings-btn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                window.location.href = '/settings';
            });
        }
    }

    async loadDeviceInfo() {
        try {
            const response = await fetch('/api/device-info');
            const data = await response.json();
            console.log('Device info loaded:', data);
            
            // Update private IP display
            const privateIpEl = document.getElementById('private-ip');
            if (privateIpEl) {
                privateIpEl.textContent = data.private_ip || 'Unknown';
            }
            
            // Update public IP display
            const publicIpEl = document.getElementById('public-ip');
            if (publicIpEl) {
                publicIpEl.textContent = data.public_ip || 'Unknown';
            }
            
            // Set hostname field
            const hostnameField = document.getElementById('hostname');
            if (hostnameField) {
                hostnameField.value = data.hostname || '';
            }
        } catch (error) {
            console.error('Failed to load device info:', error);
            // Set fallback values
            const privateIpEl = document.getElementById('private-ip');
            const publicIpEl = document.getElementById('public-ip');
            if (privateIpEl) privateIpEl.textContent = 'Unknown';
            if (publicIpEl) publicIpEl.textContent = 'Unknown';
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/system-status');
            const data = await response.json();
            console.log('System status loaded:', data);
            
            const cpuEl = document.getElementById('cpu-usage');
            const memEl = document.getElementById('memory-usage');
            const diskEl = document.getElementById('disk-usage');
            const uptimeEl = document.getElementById('uptime');
            
            if (cpuEl) cpuEl.textContent = data.cpu_usage !== undefined ? `${data.cpu_usage}%` : 'N/A';
            if (memEl) memEl.textContent = data.memory_usage !== undefined ? `${data.memory_usage}%` : 'N/A';
            if (diskEl) diskEl.textContent = data.disk_usage !== undefined ? `${data.disk_usage}%` : 'N/A';
            if (uptimeEl) uptimeEl.textContent = data.uptime || 'N/A';
            
            // Auto-refresh system status every 30 seconds
            setTimeout(() => this.loadSystemStatus(), 30000);
        } catch (error) {
            console.error('Failed to load system status:', error);
            // Set fallback values if API fails
            const cpuEl = document.getElementById('cpu-usage');
            const memEl = document.getElementById('memory-usage');
            const diskEl = document.getElementById('disk-usage');
            const uptimeEl = document.getElementById('uptime');
            
            if (cpuEl) cpuEl.textContent = 'N/A';
            if (memEl) memEl.textContent = 'N/A';
            if (diskEl) diskEl.textContent = 'N/A';
            if (uptimeEl) uptimeEl.textContent = 'N/A';
            
            // Retry after 10 seconds on error
            setTimeout(() => this.loadSystemStatus(), 10000);
        }
    }

    async loadCurrentSettings() {
        try {
            console.log('Loading current settings...');
            // Load configuration settings
            const settingsResponse = await fetch('/api/settings');
            const settings = await settingsResponse.json();
            console.log('Loaded settings:', settings);
            
            // Load real device information
            const deviceResponse = await fetch('/api/device-info');
            const deviceInfo = await deviceResponse.json();
            console.log('Loaded device info:', deviceInfo);
            
            // Populate all settings with real data
            this.populateSettings(settings);
            this.populateDeviceInfo(deviceInfo);
            
        } catch (error) {
            console.error('Failed to load settings:', error);
            this.showNotification('Failed to load settings', 'error');
        }
    }
    
    populateDeviceInfo(deviceInfo) {
        // Populate device information fields
        const fields = {
            'device-hostname': deviceInfo.hostname,
            'device-platform': deviceInfo.platform,
            'device-architecture': deviceInfo.architecture,
            'device-uptime': deviceInfo.uptime,
            'cpu-temperature': deviceInfo.temperature
        };
        
        Object.entries(fields).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element && value) {
                element.textContent = value;
            }
        });
    }

    populateSettings(settings) {
        // System settings
        if (document.getElementById('hostname')) {
            document.getElementById('hostname').value = settings.hostname || '';
        }
        
        // Test settings
        if (document.getElementById('auto-test-enabled')) {
            document.getElementById('auto-test-enabled').checked = settings.auto_test_enabled || false;
        }
        if (document.getElementById('max-auto-tests')) {
            document.getElementById('max-auto-tests').value = settings.max_auto_tests || 3;
        }
        if (document.getElementById('test-interval')) {
            document.getElementById('test-interval').value = settings.test_interval_seconds || 300;
        }
        
        // Export settings
        if (document.getElementById('auto-export-enabled')) {
            document.getElementById('auto-export-enabled').checked = settings.auto_export_enabled || false;
        }
        if (document.getElementById('export-format')) {
            document.getElementById('export-format').value = settings.auto_export_format || 'pdf';
        }
        if (document.getElementById('webhook-enabled')) {
            document.getElementById('webhook-enabled').checked = settings.webhook_enabled || false;
        }
        if (document.getElementById('webhook-url')) {
            document.getElementById('webhook-url').value = settings.webhook_url || '';
        }
        if (document.getElementById('webhook-auth')) {
            document.getElementById('webhook-auth').value = settings.webhook_auth || '';
        }

        // API settings
        const webPortEl = document.getElementById('web-port');
        if (webPortEl && settings.web_port) {
            webPortEl.value = settings.web_port;
        }

        const webAuthEnabledEl = document.getElementById('web-auth-enabled');
        if (webAuthEnabledEl) {
            webAuthEnabledEl.checked = settings.web_auth_enabled || false;
        }
        const webUsernameEl = document.getElementById('web-username');
        if (webUsernameEl) {
            webUsernameEl.value = settings.web_username || '';
        }
        const webPasswordEl = document.getElementById('web-password');
        if (webPasswordEl) {
            webPasswordEl.value = settings.web_password || '';
        }

        const authConfig = document.getElementById('auth-config');
        if (authConfig && webAuthEnabledEl) {
            authConfig.style.display = webAuthEnabledEl.checked ? 'block' : 'none';
        }

        const apiEnabledEl = document.getElementById('api-enabled');
        if (apiEnabledEl) {
            apiEnabledEl.checked = settings.api_enabled || false;
        }
        const apiKeyEl = document.getElementById('api-key');
        if (apiKeyEl && settings.api_key) {
            apiKeyEl.value = settings.api_key;
        }
        
        // Cloud push settings
        const cloudPushEnabled = document.getElementById('cloud-push-enabled');
        if (cloudPushEnabled && settings.cloud_push) {
            cloudPushEnabled.checked = settings.cloud_push.enabled || false;
        }
        const cloudApiUrl = document.getElementById('cloud-api-url');
        if (cloudApiUrl && settings.cloud_push) {
            cloudApiUrl.value = settings.cloud_push.api_url || '';
        }
        const cloudApiKey = document.getElementById('cloud-api-key');
        if (cloudApiKey && settings.cloud_push) {
            cloudApiKey.value = settings.cloud_push.api_key || '';
        }
        
        // Databricks settings
        if (settings.databricks) {
            const databricksEnabled = document.getElementById('databricks-enabled');
            if (databricksEnabled) {
                databricksEnabled.checked = settings.databricks.enabled || false;
            }
            
            const databricksWorkspaceUrl = document.getElementById('databricks-workspace-url');
            if (databricksWorkspaceUrl) {
                databricksWorkspaceUrl.value = settings.databricks.workspace_url || '';
            }
            
            const databricksAccessToken = document.getElementById('databricks-access-token');
            if (databricksAccessToken) {
                databricksAccessToken.value = settings.databricks.access_token || '';
            }
            
            const databricksWarehouseId = document.getElementById('databricks-warehouse-id');
            if (databricksWarehouseId) {
                databricksWarehouseId.value = settings.databricks.warehouse_id || '';
            }
            
            const databricksDatabase = document.getElementById('databricks-database');
            if (databricksDatabase) {
                databricksDatabase.value = settings.databricks.database || 'network_tests';
            }
            
            const databricksTable = document.getElementById('databricks-table');
            if (databricksTable) {
                databricksTable.value = settings.databricks.table || 'test_results';
            }
            
            const databricksAutoPush = document.getElementById('databricks-auto-push');
            if (databricksAutoPush) {
                databricksAutoPush.checked = settings.databricks.auto_push || false;
            }
            
            // Show/hide config based on enabled state
            const databricksConfig = document.getElementById('databricks-config');
            if (databricksConfig) {
                databricksConfig.style.display = settings.databricks.enabled ? 'block' : 'none';
            }
        }
        
        // Populate test targets
        if (settings.targets) {
            const dnsTargets = document.getElementById('dns-targets');
            if (dnsTargets && settings.targets.dns) {
                dnsTargets.value = settings.targets.dns.join('\n');
            }
            
            const pingTargets = document.getElementById('ping-targets');
            if (pingTargets && settings.targets.ping) {
                pingTargets.value = settings.targets.ping.join('\n');
            }
            
            const ntpTarget = document.getElementById('ntp-target');
            if (ntpTarget && settings.targets.ntp) {
                ntpTarget.value = settings.targets.ntp;
            }
            
            if (settings.targets.tcp) {
                this.populateTcpTargets(settings.targets.tcp);
            }
        }
    }

    populateTcpTargets(tcpTargets) {
        const container = document.getElementById('tcp-targets');
        container.innerHTML = '';
        
        tcpTargets.forEach((target, index) => {
            this.addTcpTargetRow(target.host, target.port, target.label, index);
        });
    }

    showSection(sectionName) {
        console.log('=== showSection called with:', sectionName, '===');
        
        // Update navigation - remove active from all
        const allNavItems = document.querySelectorAll('.nav-item');
        console.log('Found', allNavItems.length, 'nav items');
        allNavItems.forEach(item => {
            item.classList.remove('active');
            console.log('Removed active from:', item.dataset.section);
        });
        
        // Add active to selected nav item
        const activeNavItem = document.querySelector(`[data-section="${sectionName}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
            console.log('✓ Activated nav item:', sectionName);
        } else {
            console.error('✗ Nav item not found for section:', sectionName);
        }

        // Update panels - hide all first
        const allPanels = document.querySelectorAll('.settings-panel');
        console.log('Found', allPanels.length, 'panels');
        allPanels.forEach(panel => {
            panel.classList.remove('active');
            panel.style.display = 'none';
            console.log('Hidden panel:', panel.id);
        });
        
        // Show the selected panel
        const activePanel = document.getElementById(`${sectionName}-panel`);
        if (activePanel) {
            activePanel.classList.add('active');
            activePanel.style.display = 'block';
            console.log('✓ Showing panel:', `${sectionName}-panel`);
            
            // Scroll to top smoothly
            setTimeout(() => {
                activePanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        } else {
            console.error('✗ Panel not found:', `${sectionName}-panel`);
            console.log('Available panels:', Array.from(allPanels).map(p => p.id));
        }
        
        console.log('=== showSection complete ===');
    }

    showInterface(interfaceName) {
        // Update tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-interface="${interfaceName}"]`).classList.add('active');

        // Update interface configs
        document.querySelectorAll('.interface-config').forEach(config => {
            config.style.display = 'none';
        });
        document.getElementById(`${interfaceName}-config`).style.display = 'block';
    }

    addTcpTargetRow(host = '', port = '', label = '', index = null) {
        const container = document.getElementById('tcp-targets');
        const div = document.createElement('div');
        div.className = 'tcp-target-item';
        div.innerHTML = `
            <input type="text" placeholder="Host" value="${host}" data-field="host">
            <input type="number" placeholder="Port" value="${port}" data-field="port" min="1" max="65535">
            <input type="text" placeholder="Label" value="${label}" data-field="label">
            <button type="button" onclick="this.parentElement.remove()">
                <i class="fas fa-trash"></i>
            </button>
        `;
        container.appendChild(div);
    }

    async saveTestConfig() {
        const config = {
            auto_test_enabled: document.getElementById('auto-test-enabled').checked,
            max_auto_tests: parseInt(document.getElementById('max-auto-tests').value),
            test_interval_seconds: parseInt(document.getElementById('test-interval').value),
            targets: {
                dns: document.getElementById('dns-targets').value.split('\n').filter(s => s.trim()),
                ping: document.getElementById('ping-targets').value.split('\n').filter(s => s.trim()),
                ntp: document.getElementById('ntp-target').value.trim(),
                tcp: this.getTcpTargets()
            }
        };
        await this._postJsonWithAdminRetry('/api/settings/test', config, 'Test configuration saved successfully');
    }

    getTcpTargets() {
        const targets = [];
        document.querySelectorAll('.tcp-target-item').forEach(item => {
            const host = item.querySelector('[data-field="host"]').value.trim();
            const port = parseInt(item.querySelector('[data-field="port"]').value);
            const label = item.querySelector('[data-field="label"]').value.trim();
            
            if (host && port) {
                targets.push({ host, port, label });
            }
        });
        return targets;
    }

    async saveExportConfig() {
        const config = {
            auto_export_enabled: document.getElementById('auto-export-enabled').checked,
            auto_export_format: document.getElementById('auto-export-format').value,
            webhook_enabled: document.getElementById('webhook-enabled').checked,
            webhook_url: document.getElementById('webhook-url').value.trim(),
            webhook_auth: document.getElementById('webhook-auth').value.trim(),
            ftp_enabled: document.getElementById('ftp-enabled').checked,
            ftp_config: {
                host: document.getElementById('ftp-host').value.trim(),
                username: document.getElementById('ftp-username').value.trim(),
                password: document.getElementById('ftp-password').value.trim(),
                path: document.getElementById('ftp-path').value.trim()
            }
        };

        await this._postJsonWithAdminRetry('/api/settings/export', config, 'Export configuration saved successfully');
    }

    async saveNetworkConfig() {
        const config = {
            eth0: {
                mode: document.getElementById('eth0-mode').value,
                ip: document.getElementById('eth0-ip').value.trim(),
                netmask: document.getElementById('eth0-netmask').value.trim(),
                gateway: document.getElementById('eth0-gateway').value.trim(),
                dns: document.getElementById('eth0-dns').value.trim()
            },
            wlan0: {
                mode: document.getElementById('wlan0-mode').value,
                ssid: document.getElementById('wifi-ssid').value.trim(),
                password: document.getElementById('wifi-password').value.trim()
            }
        };

        await this._postJsonWithAdminRetry('/api/settings/network', config, 'Network configuration saved successfully. Reboot required.');
    }

    async saveDatabricksConfig() {
        const config = {
            enabled: document.getElementById('databricks-enabled').checked,
            workspace_url: document.getElementById('databricks-workspace-url').value.trim(),
            access_token: document.getElementById('databricks-access-token').value.trim(),
            warehouse_id: document.getElementById('databricks-warehouse-id').value.trim(),
            database: document.getElementById('databricks-database').value.trim() || 'network_tests',
            table: document.getElementById('databricks-table').value.trim() || 'test_results',
            auto_push: document.getElementById('databricks-auto-push').checked
        };

        await this._postJsonWithAdminRetry('/api/settings/databricks', config, 'Databricks configuration saved successfully');
    }

    async testDatabricksConnection() {
        const config = {
            workspace_url: document.getElementById('databricks-workspace-url').value.trim(),
            access_token: document.getElementById('databricks-access-token').value.trim(),
            warehouse_id: document.getElementById('databricks-warehouse-id').value.trim()
        };

        if (!config.workspace_url || !config.access_token) {
            this.showNotification('Please enter workspace URL and access token first', 'error');
            return;
        }

        try {
            const response = await fetch('/api/databricks/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification(`Connection successful! ${data.message}`, 'success');
            } else {
                this.showNotification('Connection failed: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('Connection test failed: ' + error.message, 'error');
        }
    }

    async pushToDatabricks() {
        try {
            const response = await fetch('/api/databricks/push', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification(`Results pushed successfully! Test ID: ${data.test_id}`, 'success');
            } else {
                this.showNotification('Push failed: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('Push failed: ' + error.message, 'error');
        }
    }

    async updateHostname() {
        const hostname = document.getElementById('hostname').value.trim();
        if (!hostname) return;

        await this._postJsonWithAdminRetry('/api/system/hostname', { hostname }, 'Hostname updated successfully. Reboot required.');
    }

    async rebootSystem() {
        if (!confirm('Are you sure you want to reboot the system?')) return;
        const ok = await this._postJsonWithAdminRetry('/api/system/reboot', {}, 'System will reboot soon');
        if (ok) {
            this.showNotification('System is rebooting...', 'info');
        }
    }

    generateApiKey() {
        const alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        let out = '';
        for (let i = 0; i < 32; i++) {
            out += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
        }
        const apiKeyEl = document.getElementById('api-key');
        if (apiKeyEl) {
            apiKeyEl.value = out;
        }
        this.showNotification('Generated API key (click Save API Configuration)', 'success');
    }

    async saveApiConfig() {
        const config = {
            web_port: parseInt(document.getElementById('web-port').value, 10),
            web_auth_enabled: document.getElementById('web-auth-enabled').checked,
            web_username: (document.getElementById('web-username')?.value || '').trim(),
            web_password: (document.getElementById('web-password')?.value || '').trim(),
            api_enabled: document.getElementById('api-enabled')?.checked || false,
            api_key: (document.getElementById('api-key')?.value || '').trim()
        };

        await this._postJsonWithAdminRetry('/api/settings/api', config, 'API configuration saved successfully');
    }

    async testWebhook() {
        const url = document.getElementById('webhook-url').value.trim();
        if (!url) {
            this.showNotification('Please enter a webhook URL first', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/webhook/test', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Webhook test successful!', 'success');
            } else {
                this.showNotification('Webhook test failed: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('Webhook test failed: ' + error.message, 'error');
        }
    }

    async downloadLogs() {
        try {
            const response = await fetch('/api/logs/download', { method: 'POST' });
            const data = await response.json();
            
            if (data.filename) {
                window.location.href = `/download/${data.filename}`;
                this.showNotification('Logs downloaded successfully', 'success');
            } else {
                this.showNotification('Failed to generate log file', 'error');
            }
        } catch (error) {
            this.showNotification('Download failed: ' + error.message, 'error');
        }
    }

    async factoryReset() {
        if (!confirm('Are you sure you want to reset all settings? This cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/factory-reset', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Factory reset completed. Reloading...', 'success');
                setTimeout(() => window.location.reload(), 2000);
            } else {
                this.showNotification('Factory reset failed: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('Reset failed: ' + error.message, 'error');
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'}"></i>
            ${message}
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Global functions for onclick handlers
function addTcpTarget() {
    const manager = window.settingsManager;
    manager.addTcpTargetRow();
}

function toggleNetworkMode(interface) {
    const mode = document.getElementById(`${interface}-mode`).value;
    const staticConfig = document.getElementById(`${interface}-static`);
    if (staticConfig) {
        staticConfig.style.display = mode === 'static' ? 'block' : 'none';
    }
}

function updateHostname() {
    window.settingsManager.updateHostname();
}

function rebootSystem() {
    window.settingsManager.rebootSystem();
}

function saveTestConfig() {
    window.settingsManager.saveTestConfig();
}

function saveExportConfig() {
    window.settingsManager.saveExportConfig();
}

function saveNetworkConfig() {
    window.settingsManager.saveNetworkConfig();
}

function testWebhook() {
    window.settingsManager.testWebhook();
}

function generateApiKey() {
    window.settingsManager.generateApiKey();
}

function saveApiConfig() {
    window.settingsManager.saveApiConfig();
}

function saveDatabricksConfig() {
    window.settingsManager.saveDatabricksConfig();
}

function testDatabricksConnection() {
    window.settingsManager.testDatabricksConnection();
}

function pushToDatabricks() {
    window.settingsManager.pushToDatabricks();
}

function testCloudConnection() {
    // Implementation for cloud connection test
    console.log('Test cloud connection');
}

function updateSystem() {
    // Implementation for system update
    console.log('Update system');
}

function viewLogs() {
    // Implementation for viewing logs
    window.open('/api/logs', '_blank');
}

function factoryReset() {
    if (confirm('Are you sure you want to factory reset? This cannot be undone.')) {
        fetch('/api/system/factory-reset', { method: 'POST' });
    }
}

function backupConfig() {
    window.location.href = '/api/backup-config';
}

function restoreConfig(input) {
    const file = input.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('config', file);

    fetch('/api/restore-config', {
        method: 'POST',
        body: formData
    }).then(response => {
        if (response.ok) {
            window.settingsManager.showNotification('Configuration restored successfully', 'success');
        } else {
            throw new Error('Restore failed');
        }
    }).catch(error => {
        window.settingsManager.showNotification('Failed to restore configuration', 'error');
    });
}

// Initialize settings manager
function initializeSettings() {
    console.log('Initializing settings manager...');
    console.log('Document ready state:', document.readyState);
    
    // Check if elements exist
    const navItems = document.querySelectorAll('.nav-item');
    const panels = document.querySelectorAll('.settings-panel');
    console.log('Nav items found:', navItems.length);
    console.log('Panels found:', panels.length);
    
    if (navItems.length === 0 || panels.length === 0) {
        console.warn('Elements not ready, retrying in 100ms...');
        setTimeout(initializeSettings, 100);
        return;
    }
    
    window.settingsManager = new SettingsManager();
    console.log('Settings manager initialized successfully');
}

// Wait for DOM to be fully loaded
if (document.readyState === 'loading') {
    console.log('Waiting for DOMContentLoaded...');
    document.addEventListener('DOMContentLoaded', initializeSettings);
} else {
    console.log('DOM already loaded, initializing immediately');
    initializeSettings();
}
