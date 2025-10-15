# Skydio Network Requirements

This document outlines all network connectivity requirements tested by the Skydio Network Tester.

## Overview

The Skydio Network Tester validates connectivity to all required endpoints for Skydio Dock operations, including:
- Skydio Cloud services
- Livestreaming infrastructure  
- AWS S3 storage buckets
- GPS assistance services
- Time synchronization servers

## Tested Network Rules

### Rule 1: Client Workstations to Skydio Cloud

**Purpose**: Client workstations need access to Skydio Cloud, API, and WebRTC components to manage, launch, and view missions.

**Requirements**:
- **Protocol**: TCP
- **Port**: 443 (HTTPS)
- **Destinations**:
  - `*.skydio.com`
  - `44.237.178.82`
  - `52.39.114.182`
  - `35.84.246.249`
  - `52.89.241.109`
  - `35.84.174.167`

**Tests Performed**:
- DNS resolution for `skydio.com` and `cloud.skydio.com`
- TCP connectivity to all IP addresses on port 443
- HTTPS handshake validation

---

### Rule 2: Client Workstation to Livestreaming Services (TCP 322)

**Purpose**: Client workstations need access to WebRTC components for launching missions, conducting manual flights via Remote Flight Deck, and sending live video streams.

**Requirements**:
- **Protocol**: TCP
- **Port**: 322
- **Destinations**:
  - `52.89.241.109`
  - `35.84.174.167`

**Tests Performed**:
- TCP connectivity to livestreaming servers on port 322

---

### Rule 3: Client Workstation to Livestreaming Services (TCP 7881)

**Purpose**: Additional livestreaming connectivity for video streams.

**Requirements**:
- **Protocol**: TCP
- **Port**: 7881
- **Destinations**:
  - `34.208.18.168`
  - `50.112.181.82`
  - `34.214.163.204`
  - `54.190.113.196`
  - `35.155.8.20`
  - `52.40.22.162`

**Tests Performed**:
- TCP connectivity to all livestreaming servers on port 7881

---

### Rule 5: Dock to Skydio Cloud

**Purpose**: The dock needs access to Skydio Cloud for command and control.

**Requirements**:
- **Protocol**: TCP (HTTPS)
- **Port**: 443
- **Destinations**:
  - `*.skydio.com`
  - `44.237.178.82`
  - `52.39.114.182`
  - `35.84.246.249`
  - `52.89.241.109`
  - `35.84.174.167`

**Tests Performed**:
- DNS resolution for Skydio domains
- TCP/HTTPS connectivity to all cloud IPs
- Latency measurement

---

### Rule 6: Dock to Cloud (TCP 51334)

**Purpose**: Additional dock-to-cloud communication channel.

**Requirements**:
- **Protocol**: TCP
- **Port**: 51334
- **Destinations**:
  - `44.237.178.82`
  - `52.39.114.182`
  - `35.84.246.249`

**Tests Performed**:
- TCP connectivity to Skydio Cloud IPs on port 51334

---

### Rule 7: Dock to Livestreaming Services (QUIC/UDP 443)

**Purpose**: The dock needs access to WebRTC/QUIC components for launching missions, conducting manual flights, and sending live video streams.

**Requirements**:
- **Protocol**: UDP/QUIC
- **Port**: 443
- **Destinations**:
  - `35.166.132.69`
  - `34.214.68.80`
  - `100.20.220.165`
  - `35.85.110.98`
  - `35.164.30.49`
  - `52.32.44.190`

**Tests Performed**:
- QUIC protocol connectivity to all livestreaming servers
- UDP port 443 accessibility

---

### Rule 11: Dock to AWS S3

**Purpose**: The dock needs access to specific AWS S3 bucket endpoints over HTTPS for downloading software updates and uploading media.

**Requirements**:
- **Protocol**: TCP (HTTPS)
- **Port**: 443
- **S3 Buckets Tested**:

#### Vehicle Data
- `skydio-vehicle-data.s3-accelerate.amazonaws.com`
- `skydio-vehicle-data.s3.amazonaws.com`
- `skydio-vehicle-data.s3-us-west-2.amazonaws.com`
- `skydio-vehicle-data.s3-fips.us-west-2.amazonaws.com`
- `skydio-vehicle-data.s3-fips.dualstack.us-west-2.amazonaws.com`

#### Flight Data
- `skydio-flight-data.s3-accelerate.amazonaws.com`
- `skydio-flight-data.s3.amazonaws.com`
- `skydio-flight-data.s3-us-west-2.amazonaws.com`
- `skydio-flight-data.s3-fips.us-west-2.amazonaws.com`
- `skydio-flight-data.s3-fips.dualstack.us-west-2.amazonaws.com`

#### Organization Files
- `skydio-organization-files.s3-accelerate.amazonaws.com`
- `skydio-organization-files.s3.amazonaws.com`
- `skydio-organization-files.s3-us-west-2.amazonaws.com`
- `skydio-organization-files.s3-fips.us-west-2.amazonaws.com`
- `skydio-organization-files.s3-fips.dualstack.us-west-2.amazonaws.com`

#### OTA Updates
- `skydio-ota-diff-updates.s3-accelerate.amazonaws.com`
- `skydio-ota-diff-updates.s3.amazonaws.com`
- `skydio-ota-diff-updates.s3-us-west-2.amazonaws.com`
- `skydio-ota-diff-updates.s3-fips.us-west-2.amazonaws.com`
- `skydio-ota-diff-updates.s3-fips.dualstack.us-west-2.amazonaws.com`
- `skydio-ota-updates.s3-accelerate.amazonaws.com`
- `skydio-ota-updates.s3.amazonaws.com`
- `skydio-ota-updates.s3-us-west-2.amazonaws.com`
- `skydio-ota-updates.s3-fips.us-west-2.amazonaws.com`
- `skydio-ota-updates.s3-fips.dualstack.us-west-2.amazonaws.com`

#### Controller OTA Updates
- `skydio-controller-ota-updates.s3-accelerate.amazonaws.com`
- `skydio-controller-ota-updates.s3.amazonaws.com`
- `skydio-controller-ota-updates.s3-us-west-2.amazonaws.com`
- `skydio-controller-ota-updates.s3-fips.us-west-2.amazonaws.com`
- `skydio-controller-ota-updates.s3-fips.dualstack.us-west-2.amazonaws.com`

#### Media Thumbnails
- `skydio-media-thumbnails.s3-accelerate.amazonaws.com`
- `skydio-media-thumbnails.s3.amazonaws.com`
- `skydio-media-thumbnails.s3-us-west-2.amazonaws.com`
- `skydio-media-thumbnails.s3-fips.us-west-2.amazonaws.com`
- `skydio-media-thumbnails.s3-fips.dualstack.us-west-2.amazonaws.com`

#### Media Sync Test Files
- `skydio-media-sync-test-files.s3-accelerate.amazonaws.com`
- `skydio-media-sync-test-files.s3.amazonaws.com`
- `skydio-media-sync-test-files.s3-us-west-2.amazonaws.com`
- `skydio-media-sync-test-files.s3-fips.us-west-2.amazonaws.com`
- `skydio-media-sync-test-files.s3-fips.dualstack.us-west-2.amazonaws.com`

**Tests Performed**:
- DNS resolution for all S3 endpoints
- TCP/HTTPS connectivity to S3 buckets
- Connection latency measurement

---

### Rule 12: Dock to u-blox AssistNow

**Purpose**: The vehicle accesses an online service to download additional data to improve time to acquire a GPS fix.

**Requirements**:
- **Protocol**: TCP (HTTPS)
- **Port**: 443
- **Destinations**:
  - `online-live1.services.u-blox.com`
  - `offline-live1.services.u-blox.com`

**Tests Performed**:
- DNS resolution for u-blox services
- TCP/HTTPS connectivity to GPS assistance servers

---

### Rule 13: DNS

**Purpose**: If the network does not provide DNS over DHCP, this firewall rule is needed.

**Requirements**:
- **Protocol**: UDP
- **Port**: 53
- **Destination**: `8.8.8.8` (Google DNS)

**Tests Performed**:
- DNS query functionality
- Resolution of all Skydio domains
- DNS server reachability

---

### Rule 14: NTP (Time Synchronization)

**Purpose**: The dock and vehicle use either DHCP-provided NTP or the `time.skydio.com` NTP server to set the system clock to the correct time.

**Requirements**:
- **Protocol**: UDP
- **Port**: 123
- **Destinations**:
  - `time.skydio.com`
  - `35.162.55.206`
  - `44.237.178.82`
  - `52.39.114.182`
  - `35.84.246.249`

**Tests Performed**:
- NTP synchronization with `time.skydio.com`
- Time offset measurement
- NTP server reachability

---

## Test Categories

### DNS Resolution Tests
Tests the ability to resolve domain names to IP addresses for:
- Core Skydio domains (`skydio.com`, `cloud.skydio.com`)
- AWS S3 bucket endpoints
- u-blox GPS assistance services
- Public DNS servers

### TCP Connectivity Tests
Validates TCP connections on various ports:
- **Port 443**: HTTPS for Skydio Cloud, S3, and u-blox
- **Port 322**: Livestreaming services
- **Port 7881**: Additional livestreaming services
- **Port 51334**: Dock-to-cloud communication

### QUIC Protocol Tests
Tests HTTP/3 (QUIC) connectivity on UDP port 443 for:
- Livestreaming infrastructure
- Skydio Cloud services

### Ping Tests
Measures network latency and packet loss to:
- Google DNS (`8.8.8.8`)
- Cloudflare DNS (`1.1.1.1`)
- Skydio Cloud servers
- Core infrastructure IPs

### NTP Synchronization
Validates time synchronization with:
- `time.skydio.com` (primary)
- Skydio Cloud NTP servers (backup)

### Speed Test
Measures available bandwidth:
- **PASS**: ≥20 Mbps download
- **WARN**: 10-20 Mbps download
- **FAIL**: <10 Mbps download

---

## Firewall Configuration

### Required Outbound Rules

```
# DNS
ALLOW UDP 53 to 8.8.8.8

# HTTPS (Skydio Cloud, S3, u-blox)
ALLOW TCP 443 to *.skydio.com
ALLOW TCP 443 to *.amazonaws.com
ALLOW TCP 443 to *.u-blox.com

# Livestreaming
ALLOW TCP 322 to 52.89.241.109, 35.84.174.167
ALLOW TCP 7881 to 34.208.18.168, 50.112.181.82, 34.214.163.204, 54.190.113.196, 35.155.8.20, 52.40.22.162

# Dock Communication
ALLOW TCP 51334 to 44.237.178.82, 52.39.114.182, 35.84.246.249

# QUIC/WebRTC
ALLOW UDP 443 to 35.166.132.69, 34.214.68.80, 100.20.220.165, 35.85.110.98, 35.164.30.49, 52.32.44.190

# NTP
ALLOW UDP 123 to time.skydio.com

# ICMP (for ping tests)
ALLOW ICMP to any
```

---

## Test Results Interpretation

### PASS Criteria
- **DNS**: Domain resolves within 5 seconds
- **TCP**: Connection established within 5 seconds
- **QUIC**: Protocol handshake successful
- **Ping**: Average latency <100ms, packet loss <5%
- **NTP**: Time offset <1000ms
- **Speed**: Download speed ≥20 Mbps

### WARN Criteria
- **Speed**: Download speed 10-20 Mbps

### FAIL Criteria
- **DNS**: Resolution timeout or error
- **TCP**: Connection timeout or refused
- **QUIC**: Protocol handshake failed
- **Ping**: High latency (>100ms) or packet loss (>5%)
- **NTP**: Sync failed or offset >1000ms
- **Speed**: Download speed <10 Mbps

---

## Notes

### WebRTC UDP Port Ranges (Not Tested)
The following port ranges are required for WebRTC but are **not tested** by this tool as they require active WebRTC sessions:
- **Rule 4**: UDP 50000-60000 (Client to livestreaming)
- **Rule 9**: TCP/UDP 40000-41000 (Dock to livestreaming)

These ports should be opened in firewall rules but cannot be validated without an active drone connection.

### S3 Endpoint Variations
AWS S3 buckets are accessible via multiple endpoints:
- **Standard**: `bucket.s3.amazonaws.com`
- **Regional**: `bucket.s3-region.amazonaws.com`
- **Accelerate**: `bucket.s3-accelerate.amazonaws.com` (recommended for better performance)
- **FIPS**: `bucket.s3-fips.region.amazonaws.com` (for compliance requirements)
- **Dual-stack**: `bucket.s3-fips.dualstack.region.amazonaws.com` (IPv4 and IPv6)

The tester validates connectivity to key endpoints. All variations should be accessible if the base endpoint works.

---

## Customization

To add or modify test targets, edit `config.json`:

```json
{
  "targets": {
    "dns": ["domain1.com", "domain2.com"],
    "tcp": [
      {"host": "1.2.3.4", "port": 443, "label": "Description"}
    ],
    "quic": [
      {"host": "1.2.3.4", "port": 443, "label": "Description"}
    ],
    "ping": ["1.2.3.4", "domain.com"],
    "ntp": "time.server.com"
  }
}
```

---

## Troubleshooting

### All Tests Fail
- Check internet connectivity
- Verify firewall allows outbound connections
- Confirm DNS is configured

### Specific Port Fails
- Check firewall rules for that port
- Verify destination IP/domain is correct
- Test manually: `telnet <host> <port>`

### S3 Tests Fail
- Verify AWS endpoints are not blocked
- Check for corporate proxy requirements
- Confirm DNS can resolve `.amazonaws.com` domains

### NTP Fails
- Verify UDP port 123 is open
- Check if corporate NTP server should be used instead
- Test manually: `ntpdate -q time.skydio.com`

---

## References

- Skydio Cloud Documentation
- AWS S3 Endpoint Documentation
- u-blox AssistNow Service Guide
- WebRTC Connectivity Requirements

---

**Last Updated**: October 2025  
**Version**: 2.0
