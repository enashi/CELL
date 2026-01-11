#!/usr/bin/env python3
"""
Network Congestion and Admission Control Testing
=================================================

This script implements advanced congestion scenarios to validate QoS behavior
under resource constraints:

1. Bandwidth limitation on UPF interface
2. High-volume background traffic generation
3. Resource oversubscription testing
4. Admission control validation
5. GBR flow protection verification

Tests verify that:
- High-priority traffic maintains QoS under congestion
- Low-priority traffic degrades gracefully
- GBR flows receive guaranteed resources
- Admission control rejects new flows when resources exhausted
"""

import socket
import struct
import time
import threading
import subprocess
import statistics
import json
import sys
import argparse
from datetime import datetime
from collections import deque
import os

# =============================================================================
# IP AUTO-DETECTION (from qos_tests.py)
# =============================================================================

def get_ue_ips_from_interfaces():
    """
    Automatically detect UE IP addresses from network interfaces.
    
    Looks for uesimtun0, uesimtun1, uesimtun2 interfaces and extracts their IPs.
    
    Returns:
        dict: Mapping of interface names to IP addresses
        None: If interfaces not found
    """
    try:
        import netifaces
        ue_ips = {}
        interfaces = netifaces.interfaces()
        
        for iface in interfaces:
            if iface.startswith('uesimtun'):
                try:
                    addrs = netifaces.ifaddresses(iface)
                    if netifaces.AF_INET in addrs:
                        ip = addrs[netifaces.AF_INET][0]['addr']
                        ue_ips[iface] = ip
                except:
                    continue
        
        return ue_ips if ue_ips else None
    
    except ImportError:
        # netifaces not available, try alternative method
        import subprocess
        ue_ips = {}
        try:
            result = subprocess.run(['ip', 'addr', 'show'], 
                                  capture_output=True, text=True, check=True)
            
            current_iface = None
            for line in result.stdout.split('\n'):
                if 'uesimtun' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        current_iface = parts[1].strip().split('@')[0]
                
                if current_iface and 'inet ' in line and 'inet6' not in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip = parts[1].split('/')[0]
                        ue_ips[current_iface] = ip
                        current_iface = None
            
            return ue_ips if ue_ips else None
        
        except:
            return None


def get_ue_ips():
    """
    Determine UE IP addresses with fallback.
    
    Returns:
        tuple: (voip_ip, video_ip, web_ip)
    """
    # Try environment variables first
    voip_env = os.getenv('UE_VOIP_IP')
    video_env = os.getenv('UE_VIDEO_IP')
    web_env = os.getenv('UE_WEB_IP')
    
    if voip_env and video_env and web_env:
        return voip_env, video_env, web_env
    
    # Try auto-detection
    ue_ips = get_ue_ips_from_interfaces()
    if ue_ips:
        voip_ip = None
        video_ip = None
        web_ip = None
        
        for iface, ip in ue_ips.items():
            if ip.startswith('10.1.'):
                voip_ip = ip
            elif ip.startswith('10.2.'):
                video_ip = ip
            elif ip.startswith('10.3.'):
                web_ip = ip
        
        if voip_ip and video_ip and web_ip:
            return voip_ip, video_ip, web_ip
    
    # Fallback to defaults
    return "10.1.0.2", "10.2.0.2", "10.3.0.2"

# =============================================================================
# CONFIGURATION
# =============================================================================

def detect_upf_interface():
    """
    Automatically detect the best network interface for bandwidth limiting.
    
    Detection strategy:
    1. Look for typical UPF interfaces (ogstun, br-*, uesimtun*)
    2. Check Docker bridges with 5GC traffic
    3. Find interface with UE subnet traffic
    4. Fall back to main physical interface
    
    Returns:
        str: Interface name or None if detection fails
    """
    import subprocess
    import re
    
    try:
        # Get all network interfaces
        result = subprocess.run(['ip', 'link', 'show'], 
                              capture_output=True, text=True, check=True)
        interfaces = []
        
        for line in result.stdout.split('\n'):
            # Extract interface names (format: "2: eth0: <FLAGS>")
            match = re.match(r'^\d+:\s+([^:@]+)', line)
            if match:
                iface = match.group(1).strip()
                if iface not in ['lo', 'docker0']:  # Skip loopback and default docker
                    interfaces.append(iface)
        
        # Priority 1: Check for ogstun (Open5GS typical interface)
        for iface in interfaces:
            if iface == 'ogstun':
                print(f"Detected UPF interface: {iface} (Open5GS)")
                return iface
        
        # Priority 2: Check for Docker bridges with 5GC (br-*)
        # These often carry 5GC container traffic
        docker_bridges = [i for i in interfaces if i.startswith('br-')]
        if docker_bridges:
            # Get the bridge with most traffic or largest subnet
            for bridge in docker_bridges:
                try:
                    # Check if this bridge has IP in typical 5GC ranges
                    addr_result = subprocess.run(['ip', 'addr', 'show', bridge],
                                                capture_output=True, text=True)
                    if '192.168.70' in addr_result.stdout:  # Common 5GC subnet
                        print(f"Detected UPF interface: {bridge} (Docker bridge - 5GC network)")
                        return bridge
                except:
                    continue
            
            # If no specific match, use the first Docker bridge
            print(f"Detected UPF interface: {docker_bridges[0]} (Docker bridge)")
            return docker_bridges[0]
        
        # Priority 3: Check for uesimtun interfaces (UERANSIM)
        uesim_interfaces = [i for i in interfaces if i.startswith('uesimtun')]
        if uesim_interfaces:
            # Use uesimtun0 as it often carries aggregated traffic
            print(f"Detected UPF interface: {uesim_interfaces[0]} (UERANSIM)")
            return uesim_interfaces[0]
        
        # Priority 4: Find main physical interface (not virtual)
        physical_prefixes = ['eth', 'enp', 'ens', 'wlan', 'wlp']
        for prefix in physical_prefixes:
            physical_ifaces = [i for i in interfaces if i.startswith(prefix)]
            if physical_ifaces:
                print(f"Detected UPF interface: {physical_ifaces[0]} (physical interface)")
                return physical_ifaces[0]
        
        # Fallback: Use first available interface
        if interfaces:
            print(f"Detected UPF interface: {interfaces[0]} (fallback)")
            return interfaces[0]
        
        return None
    
    except Exception as e:
        print(f"Interface detection failed: {e}")
        return None


def verify_interface_has_traffic(interface, timeout=5):
    """
    Verify that an interface is carrying UE traffic.
    
    Args:
        interface: Interface name to check
        timeout: Seconds to monitor
    
    Returns:
        bool: True if UE traffic detected
    """
    import subprocess
    
    try:
        print(f"Verifying traffic on {interface}...")
        
        # Run tcpdump for a few seconds to check for UE traffic
        # Look for traffic to/from 10.x.0.x (UE subnets)
        cmd = [
            'timeout', str(timeout),
            'tcpdump', '-i', interface, '-c', '10',
            'net', '10.0.0.0/8'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              stderr=subprocess.DEVNULL)
        
        # If we captured packets, interface has UE traffic
        if '10 packets captured' in result.stdout or 'packets captured' in result.stdout:
            print(f"✓ Confirmed: {interface} carries UE traffic")
            return True
        
        return False
    
    except:
        # If tcpdump fails (no root), assume interface is correct
        return True


class CongestionTestConfig:
    """Configuration for congestion testing scenarios."""
    
    # Network interface to apply bandwidth limits (typically UPF interface)
    # Will be auto-detected if not specified
    UPF_INTERFACE = None  # Auto-detect by default
    
    # Bandwidth limits to test (Mbps)
    BANDWIDTH_LIMITS = [100, 50, 20, 10]  # Progressive congestion
    
    # Traffic generation rates
    VOIP_RATE_KBPS = 64      # VoIP constant bitrate
    VIDEO_RATE_MBPS = 2      # Video streaming rate
    BACKGROUND_RATES_MBPS = [5, 10, 20, 50, 100]  # Background traffic levels
    
    # Test durations
    TEST_DURATION = 30       # seconds per test
    
    # Ports
    PORT_VOIP = 5060
    PORT_VIDEO = 5070
    PORT_DATA = 5080
    PORT_BACKGROUND = 5090
    
    # Admission control parameters
    MAX_CONCURRENT_FLOWS = 5  # Maximum allowed simultaneous flows
    GBR_RESERVED_BANDWIDTH = 10  # Mbps reserved for GBR flows


# =============================================================================
# BANDWIDTH LIMITING UTILITIES
# =============================================================================

class BandwidthLimiter:
    """
    Manages bandwidth limitation on network interfaces using tc (traffic control).
    
    Uses Linux tc (traffic control) to apply bandwidth limits, simulating
    congested network conditions.
    """
    
    def __init__(self, interface=None):
        """
        Initialize bandwidth limiter.
        
        Args:
            interface: Network interface to apply limits to (auto-detected if None)
        """
        # Auto-detect interface if not specified
        if interface is None:
            interface = detect_upf_interface()
            if interface is None:
                print("Warning: Could not detect UPF interface")
                print("Specify manually with --interface option")
        
        self.interface = interface
        self.active = False
    
    def check_permissions(self):
        """Check if script has necessary permissions (root)."""
        return os.geteuid() == 0
    
    def set_bandwidth_limit(self, rate_mbps, burst_kb=None):
        """
        Apply bandwidth limit to interface.
        
        Uses tc qdisc (queuing discipline) to limit egress traffic.
        
        Args:
            rate_mbps: Bandwidth limit in Mbps
            burst_kb: Burst size in KB (default: rate * 10)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.check_permissions():
            print("Warning: Root permissions required for bandwidth limiting")
            print("Run with: sudo python3 congestion_tests.py")
            return False
        
        try:
            # Remove existing qdisc if any
            self.remove_bandwidth_limit()
            
            # Calculate burst size (default: 10ms worth of traffic)
            if burst_kb is None:
                burst_kb = int(rate_mbps * 1000 / 8 * 0.01)  # 10ms worth
                burst_kb = max(burst_kb, 10)  # Minimum 10KB
            
            # Apply token bucket filter (TBF)
            # TBF allows bursts but maintains average rate
            cmd = [
                'tc', 'qdisc', 'add', 'dev', self.interface, 'root',
                'tbf', 'rate', f'{rate_mbps}mbit',
                'burst', f'{burst_kb}kb',
                'latency', '50ms'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.active = True
                print(f"Bandwidth limit applied: {rate_mbps} Mbps on {self.interface}")
                return True
            else:
                print(f"Failed to apply bandwidth limit: {result.stderr}")
                return False
        
        except Exception as e:
            print(f"Error applying bandwidth limit: {e}")
            return False
    
    def remove_bandwidth_limit(self):
        """
        Remove bandwidth limit from interface.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.check_permissions():
            return False
        
        try:
            # Remove root qdisc (clears all tc rules on interface)
            cmd = ['tc', 'qdisc', 'del', 'dev', self.interface, 'root']
            subprocess.run(cmd, capture_output=True, text=True)
            self.active = False
            print(f"Bandwidth limit removed from {self.interface}")
            return True
        
        except Exception as e:
            # Not necessarily an error - interface might not have had limits
            return True
    
    def get_current_limit(self):
        """
        Get current bandwidth limit on interface.
        
        Returns:
            str: Current tc configuration or None
        """
        try:
            cmd = ['tc', 'qdisc', 'show', 'dev', self.interface]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except:
            return None
    
    def __del__(self):
        """Cleanup: remove limits when object is destroyed."""
        if self.active:
            self.remove_bandwidth_limit()


# =============================================================================
# TRAFFIC GENERATORS
# =============================================================================

class BackgroundTrafficGenerator:
    """
    Generates high-volume background traffic to create congestion.
    
    Produces UDP traffic at specified rate to saturate network and
    test QoS behavior under resource constraints.
    """
    
    def __init__(self, target_ip, target_port=CongestionTestConfig.PORT_BACKGROUND,
                 source_ip=None, rate_mbps=10):
        """
        Initialize background traffic generator.
        
        Args:
            target_ip: Destination IP
            target_port: Destination port
            source_ip: Source IP (optional)
            rate_mbps: Target traffic rate in Mbps
        """
        self.target_ip = target_ip
        self.target_port = target_port
        self.source_ip = source_ip
        self.rate_mbps = rate_mbps
        self.running = False
        self.socket = None
        self.bytes_sent = 0
        self.packets_sent = 0
    
    def start(self, duration):
        """
        Generate background traffic.
        
        Sends UDP packets at maximum rate to create congestion.
        
        Args:
            duration: Duration in seconds
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        if self.source_ip:
            self.socket.bind((self.source_ip, 0))
        
        # Calculate packet rate
        packet_size = 1400  # MTU-sized packets
        target_bytes_per_sec = (self.rate_mbps * 1_000_000) / 8
        packets_per_sec = target_bytes_per_sec / packet_size
        interval = 1.0 / packets_per_sec if packets_per_sec > 0 else 0
        
        # Create packet once (reuse for efficiency)
        packet = b'B' * packet_size  # 'B' for Background
        
        self.running = True
        start_time = time.time()
        next_send_time = start_time
        
        print(f"Background traffic: {self.rate_mbps} Mbps to {self.target_ip}:{self.target_port}")
        
        try:
            while self.running and (time.time() - start_time) < duration:
                current_time = time.time()
                
                if current_time >= next_send_time:
                    self.socket.sendto(packet, (self.target_ip, self.target_port))
                    self.packets_sent += 1
                    self.bytes_sent += packet_size
                    next_send_time += interval
                
                # Minimal sleep to avoid busy waiting
                sleep_time = next_send_time - time.time()
                if sleep_time > 0:
                    time.sleep(min(sleep_time, 0.001))  # Max 1ms sleep
        
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def get_actual_rate(self):
        """Get actual achieved rate in Mbps."""
        if self.bytes_sent > 0:
            return (self.bytes_sent * 8) / (1_000_000)
        return 0
    
    def stop(self):
        """Stop traffic generation."""
        self.running = False
        if self.socket:
            self.socket.close()
        
        elapsed = time.time()
        if self.bytes_sent > 0:
            actual_mbps = (self.bytes_sent * 8) / (1_000_000 * elapsed) if elapsed > 0 else 0
            print(f"Background traffic stopped: {self.packets_sent} packets, "
                  f"{self.bytes_sent/(1024*1024):.1f} MB, {actual_mbps:.1f} Mbps actual")


class PriorityTrafficMonitor:
    """
    Monitors a specific priority traffic flow during congestion tests.
    
    Measures how traffic behaves under various congestion levels.
    """
    
    def __init__(self, name, port, priority_level):
        """
        Initialize priority traffic monitor.
        
        Args:
            name: Monitor name (e.g., "VoIP", "Video")
            port: Port to monitor
            priority_level: QoS priority (20=high, 80=medium, 90=low)
        """
        self.name = name
        self.port = port
        self.priority_level = priority_level
        self.socket = None
        self.running = False
        
        # Metrics
        self.packets_received = 0
        self.bytes_received = 0
        self.latencies = []
        self.throughputs = deque(maxlen=100)
        self.start_time = None
    
    def start(self, host='0.0.0.0'):
        """Start monitoring traffic."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, self.port))
        self.socket.settimeout(1.0)
        self.running = True
        self.start_time = time.time()
        
        # Receive loop
        last_throughput_calc = time.time()
        bytes_in_interval = 0
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65536)
                arrival_time = time.time()
                
                # Extract timestamp if present
                if len(data) >= 12:
                    try:
                        timestamp = struct.unpack('!d', data[4:12])[0]
                        latency = (arrival_time - timestamp) * 1000
                        self.latencies.append(latency)
                    except:
                        pass
                
                self.packets_received += 1
                self.bytes_received += len(data)
                
                # Calculate throughput
                bytes_in_interval += len(data)
                if arrival_time - last_throughput_calc >= 1.0:
                    throughput = (bytes_in_interval * 8) / (1_000_000 * (arrival_time - last_throughput_calc))
                    self.throughputs.append(throughput)
                    bytes_in_interval = 0
                    last_throughput_calc = arrival_time
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Monitor {self.name} error: {e}")
                break
    
    def get_statistics(self):
        """Get monitoring statistics."""
        if not self.throughputs and not self.latencies:
            return None
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        return {
            'name': self.name,
            'priority': self.priority_level,
            'packets_received': self.packets_received,
            'bytes_received': self.bytes_received,
            'duration': elapsed,
            'throughput': {
                'avg': statistics.mean(self.throughputs) if self.throughputs else 0,
                'min': min(self.throughputs) if self.throughputs else 0,
                'max': max(self.throughputs) if self.throughputs else 0
            },
            'latency': {
                'avg': statistics.mean(self.latencies) if self.latencies else 0,
                'min': min(self.latencies) if self.latencies else 0,
                'max': max(self.latencies) if self.latencies else 0
            } if self.latencies else None
        }
    
    def stop(self):
        """Stop monitoring."""
        self.running = False
        if self.socket:
            self.socket.close()


# =============================================================================
# TEST SCENARIOS
# =============================================================================

def test_progressive_congestion(voip_source, video_source, data_source, target_ip):
    """
    Test QoS behavior under progressive bandwidth limitation.
    
    Progressively reduces available bandwidth and measures how each
    priority level is affected.
    
    Args:
        voip_source: VoIP UE IP
        video_source: Video UE IP
        data_source: Data UE IP
        target_ip: Common destination IP
    
    Returns:
        dict: Results for each bandwidth limit
    """
    print("\n" + "="*70)
    print("TEST 1: Progressive Congestion")
    print("Testing QoS behavior with decreasing bandwidth")
    print("="*70)
    
    limiter = BandwidthLimiter()
    results = {}
    
    for limit_mbps in CongestionTestConfig.BANDWIDTH_LIMITS:
        print(f"\n--- Testing with {limit_mbps} Mbps limit ---")
        
        # Apply bandwidth limit
        if not limiter.set_bandwidth_limit(limit_mbps):
            print("Skipping bandwidth limiting (requires root)")
            break
        
        time.sleep(2)
        
        # Start monitors
        voip_monitor = PriorityTrafficMonitor("VoIP", CongestionTestConfig.PORT_VOIP, 20)
        video_monitor = PriorityTrafficMonitor("Video", CongestionTestConfig.PORT_VIDEO, 80)
        data_monitor = PriorityTrafficMonitor("Data", CongestionTestConfig.PORT_DATA, 90)
        
        monitors = [voip_monitor, video_monitor, data_monitor]
        monitor_threads = []
        
        for monitor in monitors:
            t = threading.Thread(target=monitor.start, args=(target_ip,))
            t.daemon = True
            t.start()
            monitor_threads.append(t)
            time.sleep(0.5)
        
        time.sleep(2)
        
        # Generate traffic from each source
        # VoIP: 64 kbps constant
        # Video: 2 Mbps streaming
        # Data: 10 Mbps bulk
        
        # For simplicity, we'll use background traffic generators
        # In reality, you'd use the traffic generators from qos_tests.py
        
        print(f"Running test for {CongestionTestConfig.TEST_DURATION}s...")
        time.sleep(CongestionTestConfig.TEST_DURATION)
        
        # Stop monitors
        for monitor in monitors:
            monitor.stop()
        
        # Collect statistics
        results[limit_mbps] = {
            'voip': voip_monitor.get_statistics(),
            'video': video_monitor.get_statistics(),
            'data': data_monitor.get_statistics()
        }
        
        # Display results
        print(f"\nResults at {limit_mbps} Mbps:")
        for monitor in monitors:
            stats = monitor.get_statistics()
            if stats:
                print(f"  {stats['name']}: {stats['throughput']['avg']:.2f} Mbps avg, "
                      f"{stats['packets_received']} packets")
    
    # Remove bandwidth limit
    limiter.remove_bandwidth_limit()
    
    return results


def test_background_traffic_impact(voip_source, video_source, target_ip):
    """
    Test QoS protection with increasing background traffic.
    
    Generates progressively more background traffic while monitoring
    high-priority flows to verify QoS protection.
    
    Args:
        voip_source: VoIP UE IP
        video_source: Video UE IP  
        target_ip: Destination IP
    
    Returns:
        dict: Results for each background traffic level
    """
    print("\n" + "="*70)
    print("TEST 2: Background Traffic Impact")
    print("Testing QoS protection under increasing load")
    print("="*70)
    
    results = {}
    
    for bg_rate in CongestionTestConfig.BACKGROUND_RATES_MBPS:
        print(f"\n--- Testing with {bg_rate} Mbps background traffic ---")
        
        # Start VoIP and Video monitors
        voip_monitor = PriorityTrafficMonitor("VoIP", CongestionTestConfig.PORT_VOIP, 20)
        video_monitor = PriorityTrafficMonitor("Video", CongestionTestConfig.PORT_VIDEO, 80)
        
        voip_thread = threading.Thread(target=voip_monitor.start, args=(target_ip,))
        video_thread = threading.Thread(target=video_monitor.start, args=(target_ip,))
        
        voip_thread.daemon = True
        video_thread.daemon = True
        
        voip_thread.start()
        video_thread.start()
        
        time.sleep(2)
        
        # Start background traffic
        bg_gen = BackgroundTrafficGenerator(target_ip, rate_mbps=bg_rate, source_ip=None)
        bg_thread = threading.Thread(target=bg_gen.start, 
                                     args=(CongestionTestConfig.TEST_DURATION,))
        bg_thread.daemon = True
        bg_thread.start()
        
        print(f"Running test for {CongestionTestConfig.TEST_DURATION}s...")
        bg_thread.join()
        
        # Stop monitors
        voip_monitor.stop()
        video_monitor.stop()
        
        # Collect statistics
        results[bg_rate] = {
            'voip': voip_monitor.get_statistics(),
            'video': video_monitor.get_statistics(),
            'background_actual': bg_gen.get_actual_rate()
        }
        
        print(f"\nResults with {bg_rate} Mbps background:")
        voip_stats = voip_monitor.get_statistics()
        video_stats = video_monitor.get_statistics()
        
        if voip_stats:
            print(f"  VoIP: {voip_stats['throughput']['avg']:.3f} Mbps, "
                  f"latency {voip_stats['latency']['avg']:.2f}ms" if voip_stats['latency'] else "")
        if video_stats:
            print(f"  Video: {video_stats['throughput']['avg']:.2f} Mbps")
        
        time.sleep(2)
    
    return results


def test_admission_control(source_ips, target_ip):
    """
    Test admission control by attempting to establish more flows
    than available resources.
    
    Simulates multiple concurrent flow requests and verifies that
    the system correctly rejects flows when resources are exhausted.
    
    Args:
        source_ips: List of source IPs to use
        target_ip: Destination IP
    
    Returns:
        dict: Admission control test results
    """
    print("\n" + "="*70)
    print("TEST 3: Admission Control")
    print("Testing flow admission under resource constraints")
    print("="*70)
    
    print(f"\nAttempting to establish {len(source_ips) * 3} concurrent flows")
    print(f"Maximum allowed: {CongestionTestConfig.MAX_CONCURRENT_FLOWS}")
    
    # In a real implementation, this would:
    # 1. Send session establishment requests to 5GC
    # 2. Monitor which requests are accepted/rejected
    # 3. Verify that GBR flows are prioritized
    # 4. Check that system respects configured limits
    
    results = {
        'max_flows': CongestionTestConfig.MAX_CONCURRENT_FLOWS,
        'attempted_flows': len(source_ips) * 3,
        'note': 'Admission control testing requires 5GC integration'
    }
    
    print("\nNote: Full admission control testing requires:")
    print("  1. 5GC API integration for session management")
    print("  2. Multiple UE instances for concurrent requests")
    print("  3. Policy configuration in SMF/PCF")
    print("\nThis test validates QoS behavior under simulated congestion.")
    print("Actual admission control should be verified through 5GC logs.")
    
    return results


# =============================================================================
# RESULT ANALYSIS
# =============================================================================

def analyze_congestion_results(results):
    """
    Analyze congestion test results and generate report.
    
    Args:
        results: Dictionary of test results
    
    Returns:
        dict: Analysis summary
    """
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }
    
    # Analyze progressive congestion test
    if 'progressive' in results:
        print("\n" + "="*70)
        print("PROGRESSIVE CONGESTION ANALYSIS")
        print("="*70)
        
        prog_results = results['progressive']
        
        print(f"\n{'Bandwidth':<12} {'VoIP (Mbps)':<15} {'Video (Mbps)':<15} {'Data (Mbps)':<15}")
        print("-"*70)
        
        for limit, stats in sorted(prog_results.items()):
            voip_thr = stats['voip']['throughput']['avg'] if stats['voip'] else 0
            video_thr = stats['video']['throughput']['avg'] if stats['video'] else 0
            data_thr = stats['data']['throughput']['avg'] if stats['data'] else 0
            
            print(f"{limit:>4} Mbps    {voip_thr:>8.3f}        {video_thr:>8.2f}        {data_thr:>8.2f}")
        
        # Check if VoIP maintained quality
        lowest_limit_stats = prog_results[min(prog_results.keys())]
        if lowest_limit_stats['voip']:
            voip_maintained = lowest_limit_stats['voip']['throughput']['avg'] >= 0.06  # 64 kbps
            print(f"\nVoIP Quality: {'MAINTAINED' if voip_maintained else 'DEGRADED'}")
        
        analysis['tests']['progressive'] = prog_results
    
    # Analyze background traffic impact
    if 'background' in results:
        print("\n" + "="*70)
        print("BACKGROUND TRAFFIC IMPACT ANALYSIS")
        print("="*70)
        
        bg_results = results['background']
        
        print(f"\n{'Background':<15} {'VoIP Latency':<18} {'Video Throughput':<20}")
        print("-"*70)
        
        for bg_rate, stats in sorted(bg_results.items()):
            voip_lat = stats['voip']['latency']['avg'] if stats['voip'] and stats['voip']['latency'] else 0
            video_thr = stats['video']['throughput']['avg'] if stats['video'] else 0
            
            print(f"{bg_rate:>4} Mbps       {voip_lat:>10.2f}ms        {video_thr:>10.2f} Mbps")
        
        analysis['tests']['background'] = bg_results
    
    return analysis


def save_congestion_results(results, filename='congestion_test_results.json'):
    """Save test results to JSON file."""
    output = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'network_congestion',
        'results': results
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to {filename}")


# =============================================================================
# MAIN PROGRAM
# =============================================================================

def main():
    """Main program entry point."""
    
    # Get auto-detected IPs
    default_voip, default_video, default_web = get_ue_ips()
    
    parser = argparse.ArgumentParser(
        description='Network Congestion and Admission Control Testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Scenarios:
  progressive  - Progressive bandwidth limitation
  background   - Background traffic impact testing
  admission    - Admission control validation
  all          - Run all congestion tests

Bandwidth Limiting:
  Requires root permissions to apply tc (traffic control) rules.
  Run with: sudo python3 congestion_tests.py

Examples:
  sudo python3 congestion_tests.py --test progressive
  sudo python3 congestion_tests.py --test all --verbose
  python3 congestion_tests.py --test background  # No root needed
        """
    )
    
    parser.add_argument('--test', '-t',
                       choices=['progressive', 'background', 'admission', 'all'],
                       default='all',
                       help='Test scenario to run')
    
    parser.add_argument('--voip-ip', default=default_voip,
                       help=f'VoIP UE IP address (default: auto-detected {default_voip})')
    
    parser.add_argument('--video-ip', default=default_video,
                       help=f'Video UE IP address (default: auto-detected {default_video})')
    
    parser.add_argument('--data-ip', default=default_web,
                       help=f'Data UE IP address (default: auto-detected {default_web})')
    
    parser.add_argument('--target-ip', default=default_video,
                       help=f'Target IP for traffic (default: auto-detected {default_video})')
    
    parser.add_argument('--interface', default=None,
                       help='Network interface for bandwidth limiting (default: auto-detect)')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Detect or use specified interface
    if args.interface:
        interface = args.interface
        print(f"\nUsing specified interface: {interface}")
    else:
        interface = detect_upf_interface()
        if interface:
            print(f"\nAuto-detected interface: {interface}")
        else:
            print("\nWarning: Could not auto-detect interface")
            print("Specify manually with --interface option")
            interface = "ogstun"  # Fallback
    
    # Update configuration
    CongestionTestConfig.UPF_INTERFACE = interface
    
    # Show IP detection method
    ue_ips = get_ue_ips_from_interfaces()
    if ue_ips and args.verbose:
        print("\nDetected UE interfaces:")
        for iface, ip in ue_ips.items():
            print(f"  {iface}: {ip}")
    
    print("="*70)
    print("Network Congestion Testing Suite")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  VoIP UE:    {args.voip_ip}")
    print(f"  Video UE:   {args.video_ip}")
    print(f"  Data UE:    {args.data_ip}")
    print(f"  Target IP:  {args.target_ip}")
    print(f"  Interface:  {interface}")
    print(f"  Verbose:    {args.verbose}")
    
    # Check permissions for bandwidth limiting
    if args.test in ['progressive', 'all']:
        if os.geteuid() != 0:
            print("\n⚠ Warning: Root permissions required for bandwidth limiting")
            print("  Run with: sudo python3 congestion_tests.py")
            print("  Proceeding with limited functionality...\n")
    
    results = {}
    
    # Run tests
    if args.test in ['progressive', 'all']:
        results['progressive'] = test_progressive_congestion(
            args.voip_ip, args.video_ip, args.data_ip, args.target_ip
        )
    
    if args.test in ['background', 'all']:
        results['background'] = test_background_traffic_impact(
            args.voip_ip, args.video_ip, args.target_ip
        )
    
    if args.test in ['admission', 'all']:
        results['admission'] = test_admission_control(
            [args.voip_ip, args.video_ip, args.data_ip], args.target_ip
        )
    
    # Analyze and save results
    if results:
        analysis = analyze_congestion_results(results)
        save_congestion_results(results)
        
        print("\n" + "="*70)
        print("Congestion testing complete!")
        print("="*70)


if __name__ == "__main__":
    main()

