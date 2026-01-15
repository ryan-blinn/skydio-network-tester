#!/usr/bin/env python3
"""
Automatic Network Tester for Raspberry Pi
Detects network changes and runs network readiness tests automatically
"""

import os
import json
import time
import requests
import netifaces
import subprocess
import threading
import sys
from datetime import datetime
import socket
import netifaces
from network_tests import StepRunner
import report_export as rex

class AutoNetworkTester:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.last_network_state = None
        self.test_count = 0
        self.running = False
        self.max_tests = self.config.get("max_auto_tests", 3)
        self.test_interval = self.config.get("test_interval_seconds", 300)  # 5 minutes
        self.exports_dir = self.config.get("exports_dir", "./exports")
        
    def load_config(self):
        """Load configuration from main config file"""
        default_config = {
            "auto_test_enabled": False,
            "max_auto_tests": 3,
            "test_interval_seconds": 300,
            "auto_export_enabled": True,
            "auto_export_format": "pdf",
            "webhook_enabled": False,
            "webhook_url": "",
            "webhook_auth": "",
            "api_base_url": "http://localhost:5001",
            "network_check_interval": 10,
            "exports_dir": "./exports",
            "targets": {
                "dns": ["cloud.skydio.com", "time.skydio.com", "google.com", "u-blox.com"],
                "tcp": [
                    {"host": "cloud.skydio.com", "port": 443, "label": "Skydio Cloud HTTPS"},
                    {"host": "cloud.skydio.com", "port": 322, "label": "WebRTC TCP 322"},
                    {"host": "cloud.skydio.com", "port": 7881, "label": "WebRTC TCP 7881"},
                    {"host": "www.google.com", "port": 443, "label": "Generic HTTPS"},
                    {"host": "time.skydio.com", "port": 123, "label": "Skydio NTP"}
                ],
                "ping": ["8.8.8.8", "1.1.1.1", "cloud.skydio.com"],
                "ntp": "time.skydio.com"
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            print(f"Error loading config: {e}")
            return default_config
    
    def get_network_state(self):
        """Get current network state (interfaces, IPs, gateway)"""
        try:
            interfaces = netifaces.interfaces()
            active_interfaces = []
            
            for interface in interfaces:
                if interface.startswith(('eth', 'wlan', 'en')):
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET in addrs:
                        ip_info = addrs[netifaces.AF_INET][0]
                        if ip_info.get('addr') and not ip_info['addr'].startswith('169.254'):
                            active_interfaces.append({
                                'interface': interface,
                                'ip': ip_info['addr'],
                                'netmask': ip_info.get('netmask')
                            })
            
            # Get default gateway
            gateways = netifaces.gateways()
            default_gateway = gateways.get('default', {}).get(netifaces.AF_INET)
            
            return {
                'interfaces': active_interfaces,
                'gateway': default_gateway[0] if default_gateway else None,
                'timestamp': time.time()
            }
        except Exception as e:
            print(f"Error getting network state: {e}")
            return None

    def run_network_test(self):
        return self.run_tests()
    
    def network_changed(self, current_state):
        """Check if network configuration has changed"""
        if not self.last_network_state:
            return True
            
        # Compare interface IPs and gateway
        last_ips = {iface['interface']: iface['ip'] for iface in self.last_network_state.get('interfaces', [])}
        current_ips = {iface['interface']: iface['ip'] for iface in current_state.get('interfaces', [])}
        
        if last_ips != current_ips:
            return True
            
        if self.last_network_state.get('gateway') != current_state.get('gateway'):
            return True
            
        return False
    
    def run_tests(self):
        """Run network readiness tests"""
        try:
            print(f"Running network tests (attempt {self.test_count + 1}/{self.config.get('max_auto_tests', 3)})")
            
            # Use StepRunner to run tests
            runner = StepRunner(self.config["targets"])
            results = {}
            
            for test_type, result in runner.run():
                if test_type not in results:
                    results[test_type] = []
                results[test_type].append(result)
            
            # Add metadata
            results["_meta"] = {
                "timestamp": time.time(),
                "device_name": socket.gethostname(),
                "public_ip": self.get_public_ip(),
                "test_count": self.test_count + 1,
                "network_state": self.get_network_state()
            }
            
            print(f"Tests completed. Results: {len(results)} sections")
            
            # Auto export if enabled
            if self.config.get("auto_export_enabled", False):
                self.export_results(results)
            
            # Send webhook if configured
            if self.config.get("webhook_enabled", False) and self.config.get("webhook_url"):
                self.send_webhook(results)
            
            self.test_count += 1
            return results
            
        except Exception as e:
            print(f"Error running tests: {e}")
            return None
    
    def get_public_ip(self):
        """Get public IP address"""
        try:
            response = requests.get("https://api.ipify.org", timeout=5)
            return response.text.strip()
        except:
            return "unknown"
    
    def export_results(self, results):
        """Export test results"""
        try:
            exports_dir = self.config.get("exports_dir", "./exports")
            os.makedirs(exports_dir, exist_ok=True)
            timestamp = int(time.time())
            
            format_type = self.config.get("auto_export_format", "pdf")
            
            if format_type == "csv":
                path = rex.export_csv(results, exports_dir, timestamp)
            elif format_type == "json":
                path = rex.export_json(results, exports_dir, timestamp)
            else:  # default to PDF
                path = rex.export_pdf(results, exports_dir, timestamp)
            
            print(f"Results exported to: {path}")
            return path
            
        except Exception as e:
            print(f"Error exporting results: {e}")
            return None
    
    def send_webhook(self, results):
        """Send results to webhook URL"""
        try:
            webhook_url = self.config['webhook_url']
            payload = {
                'device_name': results['_meta']['device_name'],
                'public_ip': results['_meta']['public_ip'],
                'timestamp': results['_meta']['timestamp'],
                'test_number': results['_meta']['test_number'],
                'results': results
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                print("Results sent to webhook successfully")
            else:
                print(f"Webhook failed with status: {response.status_code}")
                
        except Exception as e:
            print(f"Error sending webhook: {e}")
    
    def start(self):
        """Start the automatic network tester"""
        if self.running:
            print("Auto tester is already running")
            return
        
        # Check if auto testing is enabled
        if not self.config.get("auto_test_enabled", False):
            print("Auto testing is disabled in configuration")
            return
        
        self.running = True
        self.test_count = 0
        max_tests = self.config.get("max_auto_tests", 3)
        test_interval = self.config.get("test_interval_seconds", 300)
        check_interval = self.config.get("network_check_interval", 10)
        
        print("Starting automatic network tester...")
        print(f"Max tests per network change: {max_tests}")
        print(f"Test interval: {test_interval} seconds")
        print(f"Network check interval: {check_interval} seconds")
        
        # Get initial network state
        self.last_network_state = self.get_network_state()
        print(f"Initial network state: {self.last_network_state}")
        
        # Start monitoring loop
        while self.running:
            try:
                # Reload config periodically to pick up changes
                self.config = self.load_config()
                
                # Check if auto testing is still enabled
                if not self.config.get("auto_test_enabled", False):
                    print("Auto testing disabled in configuration, stopping...")
                    break
                
                current_state = self.get_network_state()
                
                # Check if network changed
                if self.network_changed(current_state):
                    print("Network change detected!")
                    print(f"Previous: {self.last_network_state}")
                    print(f"Current: {current_state}")
                    
                    # Reset test count for new network
                    self.test_count = 0
                    self.last_network_state = current_state
                    
                    # Run tests up to max_tests times
                    while self.test_count < max_tests and self.running:
                        results = self.run_tests()
                        
                        if results:
                            print(f"Test {self.test_count}/{max_tests} completed")
                        
                        # Wait before next test (if not the last one)
                        if self.test_count < max_tests and self.running:
                            print(f"Waiting {test_interval} seconds before next test...")
                            time.sleep(test_interval)
                
                # Check every configured interval for network changes
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\nStopping automatic network tester...")
                self.running = False
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Wait before retrying

    def monitor_network(self):
        return self.start()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automatic Network Tester for Raspberry Pi')
    parser.add_argument('--config', default='config.json', 
                       help='Configuration file path')
    parser.add_argument('--single-test', action='store_true',
                       help='Run a single test and exit')
    parser.add_argument('--daemon', action='store_true',
                       help='Run as daemon process')
    
    args = parser.parse_args()
    
    tester = AutoNetworkTester(args.config)
    
    if args.single_test:
        print("Running single network test...")
        results = tester.run_network_test()
        if results:
            print("Test completed successfully")
        else:
            print("Test failed")
            sys.exit(1)
    else:
        if args.daemon:
            # TODO: Implement proper daemon mode
            print("Daemon mode not yet implemented, running in foreground")
        
        tester.monitor_network()

if __name__ == '__main__':
    main()
