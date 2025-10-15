import requests
import json
import time
from typing import Dict, Any, Optional

class DatabricksIntegration:
    """Databricks API integration for network test results"""
    
    def __init__(self, workspace_url: str, access_token: str, cluster_id: Optional[str] = None):
        self.workspace_url = workspace_url.rstrip('/')
        self.access_token = access_token
        self.cluster_id = cluster_id
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Databricks workspace"""
        try:
            url = f"{self.workspace_url}/api/2.0/clusters/list"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                clusters = response.json().get('clusters', [])
                return {
                    'success': True,
                    'message': f'Connected successfully. Found {len(clusters)} clusters.',
                    'clusters': [{'id': c['cluster_id'], 'name': c['cluster_name'], 'state': c['state']} 
                               for c in clusters[:5]]  # Limit to first 5
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Connection failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def create_table_if_not_exists(self, database: str, table: str) -> Dict[str, Any]:
        """Create network test results table if it doesn't exist"""
        sql_query = f"""
        CREATE TABLE IF NOT EXISTS {database}.{table} (
            test_id STRING,
            timestamp TIMESTAMP,
            device_name STRING,
            public_ip STRING,
            site_label STRING,
            dns_results ARRAY<STRUCT<
                target: STRING,
                status: STRING,
                ip: STRING,
                latency_ms: INT,
                error: STRING
            >>,
            tcp_results ARRAY<STRUCT<
                target: STRING,
                status: STRING,
                latency_ms: INT,
                label: STRING,
                error: STRING
            >>,
            quic_results ARRAY<STRUCT<
                target: STRING,
                status: STRING,
                latency_ms: INT,
                protocol: STRING,
                label: STRING,
                error: STRING
            >>,
            ping_results ARRAY<STRUCT<
                target: STRING,
                status: STRING,
                output: STRING,
                error: STRING
            >>,
            ntp_result STRUCT<
                target: STRING,
                status: STRING,
                offset_ms: INT,
                error: STRING
            >,
            speedtest_result STRUCT<
                source: STRING,
                download_mbps: DOUBLE,
                upload_mbps: DOUBLE,
                status: STRING,
                server: STRING,
                error: STRING
            >,
            overall_status STRING,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        )
        USING DELTA
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        """
        
        return self._execute_sql(sql_query)
    
    def insert_test_results(self, database: str, table: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Insert network test results into Databricks table"""
        try:
            # Generate test ID
            test_id = f"test_{int(time.time())}_{results.get('_meta', {}).get('device_name', 'unknown')}"
            
            # Extract metadata
            meta = results.get('_meta', {})
            device_name = meta.get('device_name', 'unknown')
            public_ip = meta.get('public_ip', 'unknown')
            
            # Process results for SQL insertion
            dns_results = self._format_dns_results(results.get('dns', []))
            tcp_results = self._format_tcp_results(results.get('tcp', []))
            quic_results = self._format_quic_results(results.get('quic', []))
            ping_results = self._format_ping_results(results.get('ping', []))
            ntp_result = self._format_ntp_result(results.get('ntp', {}))
            speedtest_result = self._format_speedtest_result(results.get('speedtest', {}))
            
            # Calculate overall status
            overall_status = self._calculate_overall_status(results)
            
            # Create INSERT SQL
            sql_query = f"""
            INSERT INTO {database}.{table} (
                test_id, timestamp, device_name, public_ip, site_label,
                dns_results, tcp_results, quic_results, ping_results,
                ntp_result, speedtest_result, overall_status
            ) VALUES (
                '{test_id}',
                CURRENT_TIMESTAMP(),
                '{device_name}',
                '{public_ip}',
                '{meta.get("site_label", "")}',
                {dns_results},
                {tcp_results},
                {quic_results},
                {ping_results},
                {ntp_result},
                {speedtest_result},
                '{overall_status}'
            )
            """
            
            result = self._execute_sql(sql_query)
            if result.get('success'):
                result['test_id'] = test_id
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to insert results: {str(e)}'
            }
    
    def _execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query using Databricks SQL API"""
        try:
            url = f"{self.workspace_url}/api/2.0/sql/statements/"
            
            payload = {
                "statement": sql_query,
                "warehouse_id": self.cluster_id,
                "wait_timeout": "30s"
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status', {}).get('state') == 'SUCCEEDED':
                    return {
                        'success': True,
                        'result': result.get('result', {})
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Query failed: {result.get('status', {}).get('error', 'Unknown error')}"
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'SQL execution failed: {str(e)}'
            }
    
    def _format_dns_results(self, dns_results: list) -> str:
        """Format DNS results for SQL insertion"""
        if not dns_results:
            return "ARRAY()"
        
        formatted = []
        for result in dns_results:
            formatted.append(f"""
                STRUCT(
                    '{result.get("target", "")}' as target,
                    '{result.get("status", "")}' as status,
                    '{result.get("ip", "")}' as ip,
                    {result.get("latency_ms", 0)} as latency_ms,
                    '{result.get("error", "")}' as error
                )
            """)
        
        return f"ARRAY({', '.join(formatted)})"
    
    def _format_tcp_results(self, tcp_results: list) -> str:
        """Format TCP results for SQL insertion"""
        if not tcp_results:
            return "ARRAY()"
        
        formatted = []
        for result in tcp_results:
            formatted.append(f"""
                STRUCT(
                    '{result.get("target", "")}' as target,
                    '{result.get("status", "")}' as status,
                    {result.get("latency_ms", 0)} as latency_ms,
                    '{result.get("label", "")}' as label,
                    '{result.get("error", "")}' as error
                )
            """)
        
        return f"ARRAY({', '.join(formatted)})"
    
    def _format_quic_results(self, quic_results: list) -> str:
        """Format QUIC results for SQL insertion"""
        if not quic_results:
            return "ARRAY()"
        
        formatted = []
        for result in quic_results:
            formatted.append(f"""
                STRUCT(
                    '{result.get("target", "")}' as target,
                    '{result.get("status", "")}' as status,
                    {result.get("latency_ms", 0)} as latency_ms,
                    '{result.get("protocol", "")}' as protocol,
                    '{result.get("label", "")}' as label,
                    '{result.get("error", "")}' as error
                )
            """)
        
        return f"ARRAY({', '.join(formatted)})"
    
    def _format_ping_results(self, ping_results: list) -> str:
        """Format ping results for SQL insertion"""
        if not ping_results:
            return "ARRAY()"
        
        formatted = []
        for result in ping_results:
            formatted.append(f"""
                STRUCT(
                    '{result.get("target", "")}' as target,
                    '{result.get("status", "")}' as status,
                    '{result.get("output", "").replace("'", "''")}' as output,
                    '{result.get("error", "")}' as error
                )
            """)
        
        return f"ARRAY({', '.join(formatted)})"
    
    def _format_ntp_result(self, ntp_result: dict) -> str:
        """Format NTP result for SQL insertion"""
        if not ntp_result:
            return "NULL"
        
        return f"""
            STRUCT(
                '{ntp_result.get("target", "")}' as target,
                '{ntp_result.get("status", "")}' as status,
                {ntp_result.get("offset_ms", 0)} as offset_ms,
                '{ntp_result.get("error", "")}' as error
            )
        """
    
    def _format_speedtest_result(self, speedtest_result: dict) -> str:
        """Format speedtest result for SQL insertion"""
        if not speedtest_result:
            return "NULL"
        
        return f"""
            STRUCT(
                '{speedtest_result.get("source", "")}' as source,
                {speedtest_result.get("download_mbps", 0.0)} as download_mbps,
                {speedtest_result.get("upload_mbps", 0.0)} as upload_mbps,
                '{speedtest_result.get("status", "")}' as status,
                '{speedtest_result.get("server", "")}' as server,
                '{speedtest_result.get("error", "")}' as error
            )
        """
    
    def _calculate_overall_status(self, results: Dict[str, Any]) -> str:
        """Calculate overall test status"""
        failed_tests = []
        
        # Check DNS results
        dns_results = results.get('dns', [])
        if any(r.get('status') == 'FAIL' for r in dns_results):
            failed_tests.append('DNS')
        
        # Check TCP results
        tcp_results = results.get('tcp', [])
        if any(r.get('status') == 'FAIL' for r in tcp_results):
            failed_tests.append('TCP')
        
        # Check QUIC results
        quic_results = results.get('quic', [])
        if any(r.get('status') == 'FAIL' for r in quic_results):
            failed_tests.append('QUIC')
        
        # Check ping results
        ping_results = results.get('ping', [])
        if any(r.get('status') == 'FAIL' for r in ping_results):
            failed_tests.append('PING')
        
        # Check NTP result
        ntp_result = results.get('ntp', {})
        if ntp_result.get('status') == 'FAIL':
            failed_tests.append('NTP')
        
        # Check speedtest result
        speedtest_result = results.get('speedtest', {})
        if speedtest_result.get('status') == 'FAIL':
            failed_tests.append('SPEEDTEST')
        
        if not failed_tests:
            return 'PASS'
        elif len(failed_tests) <= 2:
            return 'WARN'
        else:
            return 'FAIL'

def create_databricks_client(config: Dict[str, Any]) -> Optional[DatabricksIntegration]:
    """Create Databricks client from configuration"""
    try:
        databricks_config = config.get('databricks', {})
        if not databricks_config.get('enabled', False):
            return None
        
        workspace_url = databricks_config.get('workspace_url', '').strip()
        access_token = databricks_config.get('access_token', '').strip()
        warehouse_id = databricks_config.get('warehouse_id', '').strip()
        
        if not workspace_url or not access_token:
            return None
        
        return DatabricksIntegration(
            workspace_url=workspace_url,
            access_token=access_token,
            cluster_id=warehouse_id if warehouse_id else None
        )
    except Exception:
        return None
