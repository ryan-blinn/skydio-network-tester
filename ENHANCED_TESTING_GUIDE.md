# Enhanced Network Testing Guide

## Overview

The Skydio Network Tester has been enhanced to provide 1:1 testing that matches the actual communication patterns used by Skydio Dock and External Radio hardware when connecting to the network.

## Key Enhancements

### 1. TLS/Certificate Validation

**What Changed:**
- TCP tests on port 443 now perform full TLS handshake validation
- Certificate verification matches Dock's security requirements
- Tests verify that certificates are valid and trusted

**Why It Matters:**
The Dock validates SSL/TLS certificates to ensure secure communication. A network that allows TCP connections but blocks or interferes with TLS handshakes will cause Dock failures.

**Test Configuration:**
```json
{
  "tcp": [
    {
      "host": "cloud.skydio.com",
      "port": 443,
      "label": "Skydio Cloud HTTPS",
      "verify_tls": true
    }
  ]
}
```

### 2. Full HTTPS Validation

**What Changed:**
- New `https` test category performs complete HTTP/HTTPS requests
- Validates TLS handshake + HTTP response
- Mimics Dock's actual connection pattern

**Why It Matters:**
Some networks allow TLS connections but block or modify HTTP traffic (e.g., corporate proxies, MITM inspection). The Dock requires end-to-end encrypted connections without inspection.

**Test Configuration:**
```json
{
  "https": [
    {
      "url": "https://cloud.skydio.com",
      "label": "Skydio Cloud HTTPS"
    }
  ]
}
```

### 3. Enhanced QUIC Testing

**What Changed:**
- QUIC tests now send properly formatted QUIC Initial packets
- Matches Dock's QUIC connection initiation pattern
- Tests for actual QUIC protocol responses

**Why It Matters:**
The Dock uses QUIC (UDP port 443) for low-latency video streaming. Generic UDP tests don't validate that QUIC protocol is actually working.

**Technical Details:**
- Sends QUIC v1 Initial packet with proper header format
- Waits for QUIC server response or connection rejection
- Distinguishes between filtered ports and inactive endpoints

### 4. UDP Port Range Testing

**What Changed:**
- New `udp_ranges` test category for WebRTC port ranges
- Tests ports 40000-41000 (Dock to livestreaming)
- Tests ports 50000-60000 (Client to livestreaming)
- Samples random ports from range for efficiency

**Why It Matters:**
WebRTC requires these UDP port ranges to be open. While full validation requires an active WebRTC session, sampling tests can detect if ports are completely blocked by firewall.

**Test Configuration:**
```json
{
  "udp_ranges": [
    {
      "host": "34.208.18.168",
      "port_start": 40000,
      "port_end": 41000,
      "sample_size": 5,
      "label": "Dock WebRTC Range"
    }
  ]
}
```

**Limitations:**
- Cannot fully validate WebRTC without active drone connection
- Tests check if ports are filtered, not if WebRTC will work
- Firewall rules should still be configured per documentation

### 5. Skydio-Specific Bandwidth Thresholds

**What Changed:**
- Speedtest now uses Skydio's documented requirements
- Minimum: 10 Mbps up / 20 Mbps down
- Recommended: 20 Mbps up / 80 Mbps down

**Why It Matters:**
Generic speedtests use arbitrary thresholds. Skydio has specific bandwidth requirements based on video streaming needs.

**Result Interpretation:**
- **PASS**: Meets minimum or recommended requirements
- **WARN**: Below minimum but may work with degraded performance
- **FAIL**: Insufficient bandwidth for Skydio operations

## Communication Pattern Matching

### How the Dock Connects

1. **DNS Resolution**: Resolves Skydio domains and S3 endpoints
2. **TCP Connection**: Establishes TCP connection to port 443
3. **TLS Handshake**: Performs TLS handshake with certificate validation
4. **HTTP/HTTPS Request**: Sends HTTP requests over TLS connection
5. **QUIC Connection**: Establishes QUIC connection for video streaming
6. **WebRTC Ports**: Uses UDP port ranges for peer-to-peer connections

### How the Tester Validates

The enhanced tester follows the same sequence:

```
DNS Test → TCP Test → TLS Validation → HTTPS Request → QUIC Test → UDP Range Test
```

Each test builds on the previous, ensuring the complete communication path works.

## Test Categories Explained

### DNS Resolution
**Purpose**: Verify domain name resolution  
**Dock Behavior**: Uses DHCP-provided DNS or 8.8.8.8  
**Test Method**: Standard DNS query via `gethostbyname()`

### TCP Connectivity
**Purpose**: Verify TCP port accessibility  
**Dock Behavior**: Opens TCP socket to destination  
**Test Method**: Socket connection with optional TLS validation

### HTTPS Validation
**Purpose**: Verify complete HTTPS communication  
**Dock Behavior**: Full HTTP request over TLS  
**Test Method**: `requests.get()` with certificate verification

### QUIC Protocol
**Purpose**: Verify QUIC/UDP 443 for video streaming  
**Dock Behavior**: Sends QUIC Initial packet, expects response  
**Test Method**: UDP socket with QUIC v1 packet format

### UDP Port Ranges
**Purpose**: Check if WebRTC port ranges are filtered  
**Dock Behavior**: Uses ports dynamically during WebRTC session  
**Test Method**: Sample random ports, send UDP probes

### Network Latency (Ping)
**Purpose**: Measure round-trip time and packet loss  
**Dock Behavior**: ICMP echo requests  
**Test Method**: System `ping` command

### NTP Synchronization
**Purpose**: Verify time synchronization  
**Dock Behavior**: NTP query to time.skydio.com  
**Test Method**: NTP client library query

### Bandwidth Test
**Purpose**: Measure available bandwidth  
**Dock Behavior**: Continuous video streaming  
**Test Method**: Ookla speedtest or Cloudflare speed test

## Network Requirements Summary

Based on Skydio X10 Networking Guide:

| Rule | Protocol | Port | Purpose | Test Type |
|------|----------|------|---------|-----------|
| 1 | TCP | 443 | Skydio Cloud | HTTPS |
| 2 | TCP | 322 | Livestreaming | TCP |
| 3 | TCP | 7881 | Livestreaming | TCP |
| 5 | TCP | 443 | Dock to Cloud | HTTPS |
| 6 | TCP | 51334 | Dock Communication | TCP |
| 7 | UDP | 443 | QUIC/Livestreaming | QUIC |
| 9 | UDP | 40000-41000 | Dock WebRTC | UDP Range |
| 4 | UDP | 50000-60000 | Client WebRTC | UDP Range |
| 11 | TCP | 443 | AWS S3 | HTTPS |
| 12 | TCP | 443 | u-blox GPS | HTTPS |
| 13 | UDP | 53 | DNS | DNS |
| 14 | UDP | 123 | NTP | NTP |

## What Cannot Be Tested

### WebRTC Full Validation
**Why**: Requires active drone connection and WebRTC session  
**Alternative**: UDP port range sampling detects firewall blocks  
**Recommendation**: Configure firewall rules per documentation

### MTU Size
**Why**: Requires packet fragmentation testing  
**Requirement**: 1500 bytes (per Skydio documentation)  
**Recommendation**: Verify network MTU configuration separately

### Flow Control
**Why**: Requires network equipment configuration  
**Requirement**: Enable on all switches/routers  
**Recommendation**: Configure per Skydio documentation

### Traffic Inspection
**Why**: Cannot detect MITM proxies that replace certificates  
**Requirement**: No traffic inspection or certificate replacement  
**Recommendation**: Disable SSL inspection for Skydio traffic

## Interpreting Results

### PASS
- All tests completed successfully
- Network meets Skydio requirements
- Dock should connect without issues

### WARN
- Some tests passed with warnings
- Network may work but with degraded performance
- Review specific warnings and consider improvements

### FAIL
- Critical tests failed
- Network does not meet requirements
- Dock will likely fail to connect
- Review firewall rules and network configuration

## Common Failure Scenarios

### TLS Validation Fails
**Symptom**: TCP connects but TLS fails  
**Cause**: SSL inspection, invalid certificates, or MITM proxy  
**Solution**: Disable SSL inspection for Skydio domains

### HTTPS Fails but TCP Works
**Symptom**: TCP port 443 accessible but HTTPS fails  
**Cause**: HTTP proxy, content filtering, or firewall rules  
**Solution**: Allow direct HTTPS connections without inspection

### QUIC Tests Fail
**Symptom**: UDP port 443 blocked or no response  
**Cause**: Firewall blocks UDP 443 or QUIC protocol  
**Solution**: Configure firewall to allow UDP 443 to Skydio IPs

### UDP Range Tests Fail
**Symptom**: WebRTC port ranges blocked  
**Cause**: Firewall doesn't allow UDP port ranges  
**Solution**: Open UDP ports 40000-41000 and 50000-60000

### Bandwidth Test Fails
**Symptom**: Speed below minimum requirements  
**Cause**: Insufficient internet bandwidth or network congestion  
**Solution**: Upgrade internet connection or reduce network load

## Best Practices

1. **Run Tests Multiple Times**: Network conditions vary, run 3-5 tests
2. **Test at Different Times**: Test during peak and off-peak hours
3. **Document Results**: Save test reports for troubleshooting
4. **Compare with Dock**: If Dock fails, compare with test results
5. **Monitor Latency**: Latency should be <100ms, ideally <50ms

## Advanced Configuration

### Custom Test Targets

Edit `config.json` to add custom endpoints:

```json
{
  "targets": {
    "https": [
      {
        "url": "https://custom-endpoint.example.com",
        "label": "Custom HTTPS Test"
      }
    ],
    "tcp": [
      {
        "host": "192.168.1.100",
        "port": 443,
        "label": "Internal Server",
        "verify_tls": true
      }
    ]
  }
}
```

### Adjust Test Timeouts

Modify `network_tests.py`:

```python
# Increase timeout for slow networks
def tcp_check(host, port, timeout=10, label=None, verify_tls=False):
    # ...
```

### Disable Specific Tests

Remove test categories from config:

```json
{
  "targets": {
    "dns": [...],
    "tcp": [...],
    // Remove "udp_ranges" if not needed
    "ping": [...]
  }
}
```

## Troubleshooting

### Tests Timeout
- Increase timeout values in `network_tests.py`
- Check network connectivity
- Verify firewall allows outbound connections

### TLS Errors
- Check system time (NTP must be working)
- Verify CA certificates are installed: `sudo apt-get install ca-certificates`
- Update certificates: `sudo update-ca-certificates`

### QUIC Tests Always Warn
- Normal if QUIC servers don't respond to probes
- Verify UDP 443 is not blocked by firewall
- Check with Skydio support if Dock also fails

### UDP Range Tests Unreliable
- Expected - cannot fully validate without WebRTC session
- Focus on ensuring firewall rules are configured
- Use as indicator, not definitive test

## Additional Information

For more details on network requirements, see:
- `NETWORK_REQUIREMENTS.md` - Complete network requirements
- `KIOSK_MODE_SETUP.md` - Raspberry Pi kiosk mode setup
- Skydio X10 Networking Guide - Official documentation

---

**Version**: 2.0  
**Last Updated**: January 2026  
**Compatibility**: Skydio X10 Flight System
