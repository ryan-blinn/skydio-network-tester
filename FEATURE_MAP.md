# Feature Map (UI ↔ JS ↔ API)

This document maps every visible UI feature/control to the JavaScript and backend endpoint that powers it.

## Dashboard (`/`) — Desktop UI

- **Start Network Test button**
  - **UI**: `templates/index.html` (`#start-test`)
  - **JS**: `static/js/app.js` → `NetworkTester.startTest()`
  - **API**: `POST /api/start`
  - **Backend**: `app.py` → `start()`

- **Progress bar**
  - **UI**: `#progress-container`, `#progress-fill`, `#progress-text`
  - **JS**: `NetworkTester.checkStatus()` → `GET /api/status/<job_id>`
  - **API**: `GET /api/status/<jid>`
  - **Backend**: `app.py` → `status(jid)`

- **Test card details (DNS/TCP/QUIC/PING/NTP/SPEEDTEST)**
  - **UI**: `.details-btn[data-test=...]`
  - **JS**: `NetworkTester.toggleCardExpansion()` + `updateDetailsContent()`
  - **Data source**: `GET /api/status/<jid>` → `results`

- **Export PDF/CSV/JSON**
  - **UI**: `.export-btn[data-format]`
  - **JS**: `NetworkTester.exportResults(format)`
  - **API**: `POST /api/export/<format>?site_label=...`
  - **Backend**: `app.py` → `export_results(format)`
  - **Download**: `GET /download/<name>`

- **History link**
  - **UI**: dropdown → `/history`
  - **Backend page**: `app.py` → `history()`

- **Settings link**
  - **UI**: dropdown → `/settings`
  - **Backend page**: `app.py` → `settings_page()`

## Mobile UI (`/mobile`)

- **Start / Stop test**
  - **UI**: `templates/mobile.html` → `startTest()` / `stopTest()`
  - **API**: `POST /api/start`, `GET /api/status/<jid>`
  - **Backend**: `app.py` → `start()`, `status(jid)`

- **Progress**
  - **UI**: `#progressFill`, `#progressText`
  - **JS**: uses `data.progress` from `/api/status/<jid>`

- **Result rendering**
  - **UI**: categories rendered from keys in `results` (`dns`, `tcp`, `https`, `quic`, `udp_range`, `ping`, `ntp`, `speedtest`)

## Settings (`/settings`)

### System
- **Device info header**
  - **API**: `GET /api/device-info`

- **System status grid**
  - **API**: `GET /api/system-status`

- **Hostname update**
  - **UI**: `updateHostname()`
  - **API**: `POST /api/system/hostname`

- **Reboot**
  - **UI**: `rebootSystem()`
  - **API**: `POST /api/system/reboot`

- **Update system**
  - **UI**: `updateSystem()`
  - **API**: `POST /api/system/update` (returns “not supported from UI” message)

### Network Configuration
- **Network status panel (IP/interface/gateway/DNS/SSID)**
  - **API**: `GET /api/network/status`

- **WiFi scan**
  - **API**: `GET /api/wifi/scan`

- **WiFi connect**
  - **API**: `POST /api/settings/network` (nmcli connect)

- **WiFi disconnect**
  - **API**: `POST /api/wifi/disconnect`

- **Saved WiFi networks**
  - **API**: `GET /api/wifi/saved`

- **Forget WiFi network**
  - **API**: `DELETE /api/wifi/forget/<network_name>`

### Test Configuration
- **Save test config**
  - **API**: `POST /api/settings/test`

### Export & Upload
- **Save export config**
  - **API**: `POST /api/settings/export`

- **Webhook test**
  - **API**: `POST /api/webhook/test` (compat) or `POST /api/test-webhook`

- **Download logs**
  - **API**: `POST /api/logs/download` → returns `filename` to download

- **Factory reset**
  - **API**: `POST /api/system/factory-reset` (compat also `POST /api/factory-reset`)

### API & Data Integration
- **Save API settings**
  - **API**: `POST /api/settings/api`

- **Cloud test connection**
  - **API**: `POST /api/cloud/test-direct`

- **Databricks test/push/save**
  - **API**:
    - `POST /api/databricks/test`
    - `POST /api/databricks/push`
    - `POST /api/settings/databricks`

## History (`/history`)

- **List tests**
  - **API**: `GET /api/history`

- **View details**
  - **API**: `GET /api/history/<timestamp>`

- **Delete test**
  - **API**: `DELETE /api/history/<timestamp>`

- **Clear all**
  - **API**: `POST /api/history/clear`

## Diagnostics

- **Health**: `GET /health`
- **Self-test**: `GET /api/self-test`
- **WiFi test page**: `/wifi-test`

---

If a UI control is added or removed, update this file to keep UI ↔ backend mapping aligned.
