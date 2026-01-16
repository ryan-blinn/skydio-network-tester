async function loadDeviceInfo() {
    try {
        const response = await fetch('/api/device-info');
        const data = await response.json();
        const privateIp = document.getElementById('private-ip');
        const publicIp = document.getElementById('public-ip');
        const platform = document.getElementById('platform');
        if (privateIp) privateIp.textContent = data.private_ip || 'Unknown';
        if (publicIp) publicIp.textContent = data.public_ip || 'Unknown';
        if (platform) platform.textContent = data.platform || 'Unknown';
    } catch (e) {
        console.error('Failed to load device info:', e);
    }
}

function setPill(type, text) {
    const pill = document.getElementById('overall-pill');
    if (!pill) return;
    pill.classList.remove('pass', 'warn', 'fail');
    pill.classList.add(type);
    pill.innerHTML = text;
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function renderRows(containerId, rows) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = '';
    if (!rows || rows.length === 0) {
        el.innerHTML = '<div class="row"><div class="left">None</div><div class="right"></div></div>';
        return;
    }

    rows.forEach(r => {
        const div = document.createElement('div');
        div.className = 'row';
        div.innerHTML = `<div class="left">${r.left}</div><div class="right">${r.right || ''}</div>`;
        el.appendChild(div);
    });
}

async function loadSecurity() {
    try {
        const [accessResp, secResp] = await Promise.all([
            fetch('/api/access'),
            fetch('/api/security'),
        ]);

        const access = await accessResp.json();
        const sec = await secResp.json();

        const isLocal = !!access.is_local;
        setText('local-only', isLocal ? 'Enabled (local browser)' : 'Enabled (remote browser: controls disabled)');

        setText('software', sec.software || 'Unknown');

        setText('proxy', sec.proxy?.configured ? 'Yes' : 'No');
        setText('tls-inspection', sec.tls?.suspected ? 'Yes' : 'No');

        const tlsDetails = document.getElementById('tls-details');
        if (tlsDetails) {
            tlsDetails.innerHTML = '';
            (sec.tls?.details || []).forEach(d => {
                const div = document.createElement('div');
                div.className = 'row';
                div.innerHTML = `<div class="left">${d.label}</div><div class="right">${d.value}</div>`;
                tlsDetails.appendChild(div);
            });
        }

        renderRows(
            'listeners',
            (sec.listeners || []).map(l => ({
                left: `${l.proto.toUpperCase()} ${l.local}`,
                right: l.process ? `${l.process}${l.pid ? ` (pid ${l.pid})` : ''}` : (l.pid ? `pid ${l.pid}` : ''),
            }))
        );

        renderRows(
            'outbound',
            (sec.outbound || []).map(o => ({
                left: o,
                right: '',
            }))
        );

        if (sec.ok === true) {
            setPill('pass', '<i class="fas fa-shield"></i> OK');
        } else if (sec.ok === false) {
            setPill('warn', '<i class="fas fa-triangle-exclamation"></i> Review');
        } else {
            setPill('warn', '<i class="fas fa-circle-info"></i> Info');
        }
    } catch (e) {
        console.error('Failed to load security data:', e);
        setPill('fail', '<i class="fas fa-xmark"></i> Error');
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    await loadDeviceInfo();
    await loadSecurity();
});
