import re
import ipaddress

def parse_excel_config_from_image():
    """
    Simplified configuration for general *.skydio.com domain testing.
    Tests main Skydio domains that are known to exist.
    """
    
    config = {
        "dns": [],
        "tcp": [],
        "quic": [],
        "ping": [],
        "ntp": "time.skydio.com"
    }
    
    # Main Skydio domains that are known to exist
    skydio_domains = [
        "skydio.com",
        "cloud.skydio.com"
    ]
    
    # Add external DNS targets for comparison
    external_dns = ["google.com", "8.8.8.8", "1.1.1.1"]
    
    config["dns"] = skydio_domains + external_dns
    config["ping"] = ["8.8.8.8", "1.1.1.1", "skydio.com"]
    
    # TCP targets - focus on main domains and essential ports
    tcp_targets = [
        {"host": "skydio.com", "port": 443, "label": "Skydio Main HTTPS"},
        {"host": "cloud.skydio.com", "port": 443, "label": "Skydio Cloud HTTPS"}
    ]
    
    # QUIC targets - test main Skydio domains for HTTP/3 support
    quic_targets = [
        {"host": "skydio.com", "port": 443, "label": "Skydio Main QUIC"},
        {"host": "cloud.skydio.com", "port": 443, "label": "Skydio Cloud QUIC"}
    ]
    
    config["tcp"] = tcp_targets
    config["quic"] = quic_targets
    
    return config

def validate_target(target):
    """Validate if a target should be included in testing"""
    if isinstance(target, dict):
        host = target.get("host", "")
        # Skip if contains "error" or "name" in IP field
        if "error" in host.lower() or "name" in host.lower():
            return False
        # Skip if not a valid domain or IP
        if not host or host == "N/A":
            return False
    elif isinstance(target, str):
        # Skip if contains "error" or "name"
        if "error" in target.lower() or "name" in target.lower() or target == "N/A":
            return False
    
    return True

def get_enhanced_targets():
    """Get the enhanced target configuration"""
    config = parse_excel_config_from_image()
    
    # Filter out invalid targets
    for test_type in ["dns", "tcp", "quic", "ping"]:
        if test_type in config:
            if isinstance(config[test_type], list):
                config[test_type] = [t for t in config[test_type] if validate_target(t)]
    
    return config
