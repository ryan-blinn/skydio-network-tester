class SettingsManager {
    constructor() {
        this.init();
    }

    init() {
        // Setup event listeners immediately since DOM should be ready
        this.setupEventListeners();
        this.checkLocalAccess();
        this.loadDeviceInfo();
        this.loadCurrentSettings();
        this.loadSystemStatus();
    }

    async checkLocalAccess() {
        try {
            const response = await fetch('/api/access');
            const data = await response.json();
            const isLocal = !!data.is_local;
            const allowRemoteAdmin = !!data.allow_remote_admin;
            const hasAdminAccess = isLocal || allowRemoteAdmin;

            const warning = document.getElementById('local-access-warning');
            if (warning) {
                warning.style.display = hasAdminAccess ? 'none' : 'block';
            }

            const localOnly = document.querySelectorAll('[data-local-only="true"]');
            localOnly.forEach(el => {
                if (!hasAdminAccess) {
                    el.setAttribute('disabled', 'disabled');
                    el.style.opacity = '0.55';
                    el.style.cursor = 'not-allowed';
                    el.title = 'Local-only control. Open Settings on the device screen (localhost).';
                } else {
                    el.removeAttribute('disabled');
                    el.style.opacity = '';
                    el.style.cursor = '';
                    el.title = '';
                }
            });
        } catch (e) {
            console.error('Failed to check local access:', e);
        }
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
                const iface = e.currentTarget.dataset.interface;
                this.showInterface(iface);
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
            'device-id': deviceInfo.device_id,
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

        const allowRemoteAdminEl = document.getElementById('allow-remote-admin');
        if (allowRemoteAdminEl) {
            allowRemoteAdminEl.checked = !!settings.allow_remote_admin;
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
        const exportFormatEl = document.getElementById('auto-export-format');
        if (exportFormatEl) {
            exportFormatEl.value = settings.auto_export_format || 'pdf';
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
            
            // Load network status when network panel is shown
            if (sectionName === 'network') {
                this.loadNetworkStatus();
            }
            
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

        try {
            const response = await fetch('/api/settings/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                this.showNotification('Test configuration saved successfully', 'success');
            } else {
                throw new Error('Failed to save configuration');
            }
        } catch (error) {
            this.showNotification('Failed to save test configuration', 'error');
            console.error(error);
        }
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

        try {
            const response = await fetch('/api/settings/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                this.showNotification('Export configuration saved successfully', 'success');
            } else {
                throw new Error('Failed to save configuration');
            }
        } catch (error) {
            this.showNotification('Failed to save export configuration', 'error');
            console.error(error);
        }
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

        if (!config.wlan0.ssid) {
            this.showNotification('Please enter a WiFi network name (SSID)', 'error');
            return;
        }

        try {
            const response = await fetch('/api/settings/network', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            const data = await response.json();

            if (response.ok) {
                this.showNotification(data.message || 'Successfully connected to WiFi network', 'success');
                // Refresh current WiFi status
                setTimeout(() => this.loadCurrentWiFi(), 2000);
            } else {
                this.showNotification('Failed to connect: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            this.showNotification('Failed to save network configuration: ' + error.message, 'error');
            console.error(error);
        }
    }

    async scanWiFiNetworks() {
        try {
            this.showNotification('Scanning for WiFi networks...', 'info');
            
            const response = await fetch('/api/wifi/scan');
            const data = await response.json();

            if (response.ok && data.networks) {
                this.displayWiFiNetworks(data.networks);
                this.showNotification(`Found ${data.networks.length} networks`, 'success');
            } else {
                this.showNotification('Failed to scan networks: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            this.showNotification('WiFi scan failed: ' + error.message, 'error');
            console.error(error);
        }
    }

    displayWiFiNetworks(networks) {
        const container = document.getElementById('wifi-networks-list');
        if (!container) return;

        container.innerHTML = '';

        if (networks.length === 0) {
            container.innerHTML = '<p style="color: #666;">No networks found</p>';
            return;
        }

        networks.forEach(network => {
            const div = document.createElement('div');
            div.className = 'wifi-network-item';
            div.innerHTML = `
                <div class="wifi-network-info">
                    <i class="fas fa-${network.secured ? 'lock' : 'wifi'}"></i>
                    <span class="wifi-ssid">${network.ssid}</span>
                    <span class="wifi-signal">${this.getSignalBars(network.signal)}</span>
                </div>
                <button class="btn-secondary btn-small" onclick="window.settingsManager.selectWiFiNetwork('${network.ssid}', ${network.secured})">
                    Connect
                </button>
            `;
            container.appendChild(div);
        });
    }

    getSignalBars(signal) {
        if (signal >= 75) return '▂▄▆█';
        if (signal >= 50) return '▂▄▆';
        if (signal >= 25) return '▂▄';
        return '▂';
    }

    selectWiFiNetwork(ssid, secured) {
        const ssidInput = document.getElementById('wifi-ssid');
        const passwordInput = document.getElementById('wifi-password');
        
        if (ssidInput) ssidInput.value = ssid;
        if (passwordInput) {
            passwordInput.value = '';
            if (secured) {
                passwordInput.focus();
            }
        }

        // Scroll to the form
        const wifiConfig = document.getElementById('wlan0-config');
        if (wifiConfig) {
            wifiConfig.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    async loadCurrentWiFi() {
        try {
            const response = await fetch('/api/wifi/current');
            const data = await response.json();

            const statusEl = document.getElementById('wifi-status');
            if (statusEl) {
                if (data.connected) {
                    statusEl.innerHTML = `
                        <i class="fas fa-wifi" style="color: #00c853;"></i>
                        Connected to: <strong>${data.ssid}</strong> 
                        (Signal: ${this.getSignalBars(data.signal)})
                    `;
                } else {
                    statusEl.innerHTML = `
                        <i class="fas fa-wifi-slash" style="color: #999;"></i>
                        Not connected to WiFi
                    `;
                }
            }
        } catch (error) {
            console.error('Failed to load current WiFi:', error);
        }
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

        try {
            const response = await fetch('/api/settings/databricks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                this.showNotification('Databricks configuration saved successfully', 'success');
            } else {
                throw new Error('Failed to save configuration');
            }
        } catch (error) {
            this.showNotification('Failed to save Databricks configuration', 'error');
            console.error(error);
        }
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

        try {
            const response = await fetch('/api/system/hostname', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ hostname })
            });

            if (response.ok) {
                this.showNotification('Hostname updated successfully. Reboot required.', 'success');
            } else {
                throw new Error('Failed to update hostname');
            }
        } catch (error) {
            this.showNotification('Failed to update hostname', 'error');
            console.error(error);
        }
    }

    async rebootSystem() {
        if (!confirm('Are you sure you want to reboot the system?')) return;

        try {
            await fetch('/api/system/reboot', { method: 'POST' });
            this.showNotification('System is rebooting...', 'info');
        } catch (error) {
            console.error('Reboot request failed:', error);
        }
    }

    async testWebhook() {
        const url = document.getElementById('webhook-url').value.trim();
        if (!url) {
            this.showNotification('Please enter a webhook URL first', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/webhook/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
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
            const response = await fetch('/api/system/factory-reset', { method: 'POST' });
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

    generateApiKey() {
        const apiKeyEl = document.getElementById('api-key');
        if (!apiKeyEl) return;

        // Simple random key; stored in config.json via saveApiConfig()
        const bytes = new Uint8Array(24);
        window.crypto.getRandomValues(bytes);
        const key = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
        apiKeyEl.value = key;
        this.showNotification('API key generated (click Save API Configuration)', 'success');
    }

    async saveApiConfig() {
        try {
            const payload = {
                api_enabled: !!document.getElementById('api-enabled')?.checked,
                api_key: document.getElementById('api-key')?.value?.trim() || '',
                web_port: parseInt(document.getElementById('web-port')?.value || '5001', 10),
                web_auth_enabled: !!document.getElementById('web-auth-enabled')?.checked,
                web_username: document.getElementById('web-username')?.value?.trim() || '',
                web_password: document.getElementById('web-password')?.value?.trim() || '',
                allow_remote_admin: !!document.getElementById('allow-remote-admin')?.checked
            };

            const response = await fetch('/api/settings/api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (response.ok) {
                this.showNotification(data.message || 'API settings saved', 'success');
            } else {
                this.showNotification(data.error || 'Failed to save API settings', 'error');
            }
        } catch (e) {
            this.showNotification('Failed to save API settings: ' + e.message, 'error');
        }
    }

    async testCloudConnection() {
        try {
            const apiUrl = document.getElementById('cloud-api-url')?.value?.trim() || '';
            const apiKey = document.getElementById('cloud-api-key')?.value?.trim() || '';
            if (!apiUrl) {
                this.showNotification('Please enter a Cloud API URL first', 'error');
                return;
            }

            const response = await fetch('/api/cloud/test-direct', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_url: apiUrl, api_key: apiKey })
            });
            const data = await response.json();

            if (response.ok && data.success) {
                this.showNotification(`Cloud test OK (${data.status_code})`, 'success');
            } else {
                this.showNotification('Cloud test failed: ' + (data.error || data.response || 'Unknown error'), 'error');
            }
        } catch (e) {
            this.showNotification('Cloud test failed: ' + e.message, 'error');
        }
    }

    async updateSystem() {
        try {
            const response = await fetch('/api/system/update', { method: 'POST' });
            const data = await response.json();
            this.showNotification(data.message || 'System update not available', response.ok ? 'info' : 'error');
        } catch (e) {
            this.showNotification('System update failed: ' + e.message, 'error');
        }
    }

    async loadNetworkStatus() {
        try {
            const response = await fetch('/api/network/status');
            const data = await response.json();

            const setText = (id, value) => {
                const el = document.getElementById(id);
                if (el) el.textContent = value ?? 'N/A';
            };

            setText('net-hostname', data.hostname || 'N/A');
            setText('net-private-ip', data.private_ip || 'N/A');
            setText('net-public-ip', data.public_ip || 'N/A');

            const conn = data.connection_type ? `${data.connection_type}${data.active_interface ? ` (${data.active_interface})` : ''}` : (data.active_interface || 'N/A');
            setText('net-connection', conn);
            setText('net-gateway', data.gateway || 'N/A');
            setText('net-dns', (data.dns_servers && data.dns_servers.length) ? data.dns_servers.join(', ') : 'N/A');

            // Also keep the existing WiFi status banner updated
            await this.loadCurrentWiFi();

            // Load interface-specific detected details
            await this.loadInterfaceDetails();
        } catch (error) {
            console.error('Failed to load network status:', error);
            const statusEl = document.getElementById('wifi-status');
            if (statusEl) {
                statusEl.innerHTML = `<i class="fas fa-exclamation-triangle" style="color:#f44336;"></i> Failed to load network status`;
            }
        }
    }

    async loadInterfaceDetails() {
        try {
            const response = await fetch('/api/network/interfaces');
            const data = await response.json();

            const setText = (id, value) => {
                const el = document.getElementById(id);
                if (el) el.textContent = value ?? 'N/A';
            };

            const applyDetails = (ifname, d) => {
                if (!d) return;

                setText(`${ifname}-state`, d.state || 'N/A');
                setText(`${ifname}-connection`, d.active_connection || d.connection || 'N/A');
                if (ifname === 'eth0') {
                    setText('eth0-mac', d.mac || 'N/A');
                    setText('eth0-mtu', d.mtu ?? 'N/A');
                }

                const ipv4 = d.ipv4_address ? `${d.ipv4_address}${d.ipv4_prefix !== null && d.ipv4_prefix !== undefined ? `/${d.ipv4_prefix}` : ''}` : 'N/A';
                setText(`${ifname}-ipv4`, ipv4);
                setText(`${ifname}-gw`, d.ipv4_gateway || 'N/A');
                setText(`${ifname}-dns-detected`, (d.dns_servers && d.dns_servers.length) ? d.dns_servers.join(', ') : 'N/A');
                setText(`${ifname}-method`, d.ipv4_method || 'N/A');

                if (ifname === 'wlan0') {
                    const ssid = d.wifi?.connected ? d.wifi.ssid : 'Not connected';
                    setText('wlan0-ssid', ssid);
                    setText('wlan0-signal', d.wifi?.connected ? this.getSignalBars(d.wifi.signal || 0) : 'N/A');
                }

                // Populate form defaults to current settings (best-effort)
                const modeEl = document.getElementById(`${ifname}-mode`);
                if (modeEl) {
                    const method = (d.ipv4_method || '').toLowerCase();
                    modeEl.value = method === 'manual' ? 'static' : 'dhcp';
                }
                if (ifname === 'eth0') {
                    const ipEl = document.getElementById('eth0-ip');
                    const nmEl = document.getElementById('eth0-netmask');
                    const gwEl = document.getElementById('eth0-gateway');
                    const dnsEl = document.getElementById('eth0-dns');
                    if (ipEl && d.ipv4_address) ipEl.value = d.ipv4_address;
                    if (nmEl && d.ipv4_netmask) nmEl.value = d.ipv4_netmask;
                    if (gwEl && d.ipv4_gateway) gwEl.value = d.ipv4_gateway;
                    if (dnsEl && d.dns_servers) dnsEl.value = d.dns_servers.join(', ');
                }
                if (ifname === 'wlan0') {
                    const ipEl = document.getElementById('wlan0-ip');
                    const nmEl = document.getElementById('wlan0-netmask');
                    const gwEl = document.getElementById('wlan0-gateway');
                    const dnsEl = document.getElementById('wlan0-dns');
                    if (ipEl && d.ipv4_address) ipEl.value = d.ipv4_address;
                    if (nmEl && d.ipv4_netmask) nmEl.value = d.ipv4_netmask;
                    if (gwEl && d.ipv4_gateway) gwEl.value = d.ipv4_gateway;
                    if (dnsEl && d.dns_servers) dnsEl.value = d.dns_servers.join(', ');
                }

                toggleNetworkMode(ifname);
            };

            applyDetails('eth0', data.eth0);
            applyDetails('wlan0', data.wlan0);
        } catch (e) {
            console.error('Failed to load interface details:', e);
        }
    }

    async applyInterfaceConfig(ifname) {
        try {
            const mode = document.getElementById(`${ifname}-mode`)?.value || 'dhcp';
            let payload = { mode };

            if (mode === 'static') {
                const ip = document.getElementById(`${ifname}-ip`)?.value?.trim() || '';
                const netmask = document.getElementById(`${ifname}-netmask`)?.value?.trim() || '';
                const gateway = document.getElementById(`${ifname}-gateway`)?.value?.trim() || '';
                const dns = document.getElementById(`${ifname}-dns`)?.value?.trim() || '';
                payload = { mode, ip, netmask, gateway, dns };
            }

            const response = await fetch(`/api/network/interface/${encodeURIComponent(ifname)}/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();

            if (response.ok && data.success) {
                this.showNotification(data.message || 'Applied network settings', 'success');
                setTimeout(() => this.loadNetworkStatus(), 2000);
            } else {
                this.showNotification(data.error || 'Failed to apply settings', 'error');
            }
        } catch (e) {
            this.showNotification('Failed to apply settings: ' + e.message, 'error');
        }
    }

    async disconnectWiFi() {
        try {
            const response = await fetch('/api/wifi/disconnect', { method: 'POST' });
            const data = await response.json();
            if (response.ok && data.success) {
                this.showNotification(data.message || 'Disconnected', 'success');
                setTimeout(() => this.loadNetworkStatus(), 1500);
            } else {
                this.showNotification(data.error || 'Failed to disconnect', 'error');
            }
        } catch (e) {
            this.showNotification('Failed to disconnect: ' + e.message, 'error');
        }
    }

    async loadSavedWiFiNetworks() {
        try {
            const container = document.getElementById('wifi-saved-list');
            if (!container) return;

            const response = await fetch('/api/wifi/saved');
            const data = await response.json();

            container.style.display = 'block';
            container.innerHTML = '';

            const networks = data.networks || [];
            if (networks.length === 0) {
                container.innerHTML = '<p style="color:#666; text-align:center;">No saved WiFi networks</p>';
                return;
            }

            networks.forEach(n => {
                const div = document.createElement('div');
                div.className = 'wifi-network-item';
                div.innerHTML = `
                    <div class="wifi-network-info">
                        <i class="fas fa-wifi"></i>
                        <span class="wifi-ssid">${n.name}</span>
                    </div>
                    <button class="btn-secondary btn-small" onclick="forgetWiFiNetwork('${n.name.replace(/'/g, "\\'")}')">Forget</button>
                `;
                container.appendChild(div);
            });
        } catch (e) {
            this.showNotification('Failed to load saved networks: ' + e.message, 'error');
        }
    }

    async forgetWiFiNetwork(name) {
        try {
            const response = await fetch(`/api/wifi/forget/${encodeURIComponent(name)}`, { method: 'DELETE' });
            const data = await response.json();
            if (response.ok && data.success) {
                this.showNotification(data.message || 'Forgot network', 'success');
                this.loadSavedWiFiNetworks();
            } else {
                this.showNotification(data.error || 'Failed to forget network', 'error');
            }
        } catch (e) {
            this.showNotification('Failed to forget network: ' + e.message, 'error');
        }
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

function disconnectWiFi() {
    window.settingsManager.disconnectWiFi();
}

function loadSavedWiFiNetworks() {
    window.settingsManager.loadSavedWiFiNetworks();
}

function forgetWiFiNetwork(name) {
    window.settingsManager.forgetWiFiNetwork(name);
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
    window.settingsManager.testCloudConnection();
}

function updateSystem() {
    window.settingsManager.updateSystem();
}

function applyInterfaceConfig(ifname) {
    window.settingsManager.applyInterfaceConfig(ifname);
}

function viewLogs() {
    // Implementation for viewing logs
    window.open('/api/logs', '_blank');
}

function downloadLogs() {
    if (window.settingsManager && typeof window.settingsManager.downloadLogs === 'function') {
        window.settingsManager.downloadLogs();
        return;
    }

    fetch('/api/logs/download', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data && data.filename) {
                window.location.href = `/download/${data.filename}`;
            }
        });
}

function factoryReset() {
    if (window.settingsManager && typeof window.settingsManager.factoryReset === 'function') {
        window.settingsManager.factoryReset();
        return;
    }

    if (!confirm('Are you sure you want to factory reset? This cannot be undone.')) {
        return;
    }

    fetch('/api/system/factory-reset', { method: 'POST' });
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
