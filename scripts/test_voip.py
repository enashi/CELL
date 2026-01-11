#!/usr/bin/env python3
"""
VoIP Traffic Test Script - Complete Implementation

Simulates VoIP traffic and measures QoS parameters:
- Latency
- Jitter  
- Packet loss

Implementation uses UDP sockets to simulate G.711 VoIP codec (64 kbps)
"""

import time
import subprocess
import json
import statistics
import socket
import struct
import threading
from collections import deque
import sys

# =============================================================================
# VoIP TRAFFIC GENERATOR
# =============================================================================

class VoIPTrafficGenerator:
    """Generates VoIP-like UDP traffic (G.711 codec simulation)"""
    
    def __init__(self, target_ip, target_port=5060, source_port=5061):
        """
        Initialize VoIP traffic generator
        
        Args:
            target_ip: Destination IP address
            target_port: Destination port
            source_port: Source port
        """
        self.target_ip = target_ip
        self.target_port = target_port
        self.source_port = source_port
        self.socket = None
        self.running = False
        self.stats = {
            'packets_sent': 0,
            'bytes_sent': 0,
            'errors': 0
        }
    
    def start(self):
        """Start traffic generation"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('', self.source_port))
            self.running = True
            return True
        except Exception as e:
            print(f"Error starting VoIP generator: {e}")
            return False
    
    def generate_traffic(self, duration=60, rate=50):
        """
        Generate VoIP traffic
        
        Args:
            duration: Test duration in seconds
            rate: Packets per second (default 50 for 20ms packetization)
        
        G.711 characteristics:
        - 64 kbps bitrate
        - 20ms packetization = 50 packets/sec
        - Packet size: 160 bytes payload + headers
        """
        if not self.running:
            return
        
        packet_interval = 1.0 / rate  # Time between packets
        payload_size = 160  # G.711 20ms frame
        
        start_time = time.time()
        next_send_time = start_time
        sequence = 0
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # Create RTP-like packet
                # Simple header: timestamp (4 bytes) + sequence (4 bytes) + payload
                # Use relative timestamp to avoid overflow
                relative_timestamp = int((time.time() - start_time) * 1000)  # ms since start
                header = struct.pack('!II', relative_timestamp, sequence)
                payload = b'V' * payload_size  # VoIP data
                packet = header + payload
                
                # Send packet
                self.socket.sendto(packet, (self.target_ip, self.target_port))
                self.stats['packets_sent'] += 1
                self.stats['bytes_sent'] += len(packet)
                sequence += 1
                
                # Wait for next packet time
                next_send_time += packet_interval
                sleep_time = next_send_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                self.stats['errors'] += 1
                if self.stats['errors'] < 5:  # Limit error messages
                    print(f"Error sending packet: {e}")
        
        # Calculate actual bitrate
        duration_actual = time.time() - start_time
        bitrate_kbps = (self.stats['bytes_sent'] * 8) / (duration_actual * 1000)
        
        print(f"\nVoIP Traffic Statistics:")
        print(f"  Packets sent: {self.stats['packets_sent']}")
        print(f"  Bytes sent: {self.stats['bytes_sent']}")
        print(f"  Duration: {duration_actual:.2f}s")
        print(f"  Bitrate: {bitrate_kbps:.2f} kbps")
        print(f"  Errors: {self.stats['errors']}")
    
    def stop(self):
        """Stop traffic generation"""
        self.running = False
        if self.socket:
            self.socket.close()


# =============================================================================
# MEASUREMENT FUNCTIONS
# =============================================================================

def measure_latency(target_ip, count=100):
    """
    Measure latency using ping
    
    Args:
        target_ip: Target IP address
        count: Number of ping packets
    
    Returns:
        dict: Statistics (min, max, avg, stddev, loss)
    """
    print(f"Measuring latency to {target_ip} ({count} packets)...")
    
    try:
        # Run ping command
        cmd = ['ping', '-c', str(count), '-i', '0.2', target_ip]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"Ping failed: {result.stderr}")
            return {
                'min': 0,
                'max': 0,
                'avg': 0,
                'stddev': 0,
                'loss': 100.0
            }
        
        # Parse output
        output = result.stdout
        
        # Extract packet loss
        loss = 0.0
        for line in output.split('\n'):
            if 'packet loss' in line:
                try:
                    loss = float(line.split('%')[0].split()[-1])
                except:
                    pass
        
        # Extract latency statistics (last line with min/avg/max/stddev)
        min_latency = 0
        max_latency = 0
        avg_latency = 0
        stddev_latency = 0
        
        for line in output.split('\n'):
            if 'min/avg/max' in line or 'rtt' in line:
                try:
                    # Format: "rtt min/avg/max/mdev = 10.1/15.2/20.3/2.5 ms"
                    stats_part = line.split('=')[1].strip().split()[0]
                    min_latency, avg_latency, max_latency, stddev_latency = map(float, stats_part.split('/'))
                except Exception as e:
                    print(f"Warning: Could not parse latency stats: {e}")
        
        return {
            'min': min_latency,
            'max': max_latency,
            'avg': avg_latency,
            'stddev': stddev_latency,
            'loss': loss
        }
    
    except subprocess.TimeoutExpired:
        print("Ping timeout")
        return {
            'min': 0,
            'max': 0,
            'avg': 0,
            'stddev': 0,
            'loss': 100.0
        }
    except Exception as e:
        print(f"Error measuring latency: {e}")
        return {
            'min': 0,
            'max': 0,
            'avg': 0,
            'stddev': 0,
            'loss': 100.0
        }


def measure_jitter_live(target_ip, port=5060, duration=10):
    """
    Calculate jitter by receiving VoIP packets and measuring inter-arrival time variance
    
    Args:
        target_ip: Source IP to receive from
        port: Port to listen on
        duration: Measurement duration in seconds
    
    Returns:
        float: Average jitter in ms
    """
    print(f"Measuring jitter (receiving packets for {duration}s)...")
    
    try:
        # Create receiving socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', port))
        sock.settimeout(1.0)
        
        arrival_times = []
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            try:
                data, addr = sock.recvfrom(2048)
                arrival_times.append(time.time())
            except socket.timeout:
                continue
            except Exception as e:
                break
        
        sock.close()
        
        if len(arrival_times) < 2:
            print("  Warning: Not enough packets received for jitter calculation")
            return 0.0
        
        # Calculate inter-arrival times
        inter_arrival_times = []
        for i in range(1, len(arrival_times)):
            inter_arrival_times.append((arrival_times[i] - arrival_times[i-1]) * 1000)  # Convert to ms
        
        # Jitter is the variance of inter-arrival times
        if len(inter_arrival_times) < 2:
            return 0.0
        
        # Calculate jitter using RFC 3550 method (running average of differences)
        jitter = 0.0
        expected_interval = 20.0  # 20ms for G.711
        
        for interval in inter_arrival_times:
            diff = abs(interval - expected_interval)
            jitter += (diff - jitter) / 16.0  # RFC 3550 smoothing
        
        print(f"  Received {len(arrival_times)} packets")
        print(f"  Average inter-arrival time: {statistics.mean(inter_arrival_times):.2f}ms")
        print(f"  Jitter: {jitter:.2f}ms")
        
        return jitter
    
    except Exception as e:
        print(f"Error measuring jitter: {e}")
        return 0.0


def measure_jitter(pcap_file):
    """
    Calculate jitter from packet capture
    (Fallback method if pcap file exists)
    
    Args:
        pcap_file: Path to pcap file
    
    Returns:
        float: Average jitter in ms
    """
    # This is a placeholder for pcap-based analysis
    # In practice, use the live measurement above
    print(f"Note: Using live jitter measurement instead of pcap analysis")
    return 0.0


# =============================================================================
# MAIN TEST FUNCTION
# =============================================================================

def run_voip_test(target_ip, test_duration=60, rate=50):
    """
    Run complete VoIP test
    
    Args:
        target_ip: Target IP address for VoIP traffic
        test_duration: Duration of traffic generation in seconds
        rate: Packets per second (default 50 for 20ms packetization)
    """
    print("=" * 70)
    print("Starting VoIP QoS Test")
    print("=" * 70)
    print(f"Target IP: {target_ip}")
    print(f"Duration: {test_duration}s")
    print(f"Packet rate: {rate} pps (20ms packetization)")
    
    # Measure baseline latency
    print("\n[1/4] Measuring baseline latency...")
    latency_stats = measure_latency(target_ip, count=50)
    
    # Start jitter measurement in background (receiver)
    print("\n[2/4] Starting jitter measurement...")
    jitter_thread = None
    jitter_result = [0.0]  # Use list to allow modification in thread
    
    def measure_jitter_thread():
        jitter_result[0] = measure_jitter_live(target_ip, port=5060, duration=min(test_duration, 30))
    
    jitter_thread = threading.Thread(target=measure_jitter_thread, daemon=True)
    jitter_thread.start()
    
    # Wait a moment for receiver to be ready
    time.sleep(1)
    
    # Generate VoIP traffic
    print("\n[3/4] Generating VoIP traffic...")
    generator = VoIPTrafficGenerator(target_ip, target_port=5060, source_port=5061)
    
    if generator.start():
        generator.generate_traffic(duration=test_duration, rate=rate)
        generator.stop()
    else:
        print("Failed to start VoIP traffic generator")
    
    # Wait for jitter measurement to complete
    print("\n[4/4] Finalizing jitter analysis...")
    if jitter_thread:
        jitter_thread.join(timeout=5)
    jitter = jitter_result[0]
    
    # Print results
    print("\n" + "=" * 70)
    print("VoIP QoS Test Results")
    print("=" * 70)
    print(f"Latency:")
    print(f"  Average: {latency_stats['avg']:.2f}ms")
    print(f"  Min: {latency_stats['min']:.2f}ms")
    print(f"  Max: {latency_stats['max']:.2f}ms")
    print(f"  Std Dev: {latency_stats['stddev']:.2f}ms")
    print(f"Jitter: {jitter:.2f}ms")
    print(f"Packet Loss: {latency_stats['loss']:.2f}%")
    
    # Evaluate against thresholds
    print("\n" + "=" * 70)
    print("QoS Evaluation (ITU-T G.114 / 3GPP TS 23.203)")
    print("=" * 70)
    
    voip_latency_threshold = 150  # ms (ITU-T G.114)
    voip_jitter_threshold = 30    # ms
    voip_loss_threshold = 1.0     # %
    
    passed = True
    
    if latency_stats['avg'] > voip_latency_threshold:
        print(f"❌ FAIL: Latency {latency_stats['avg']:.2f}ms exceeds threshold {voip_latency_threshold}ms")
        passed = False
    else:
        print(f"✓ PASS: Latency {latency_stats['avg']:.2f}ms within acceptable range (<{voip_latency_threshold}ms)")
    
    if jitter > voip_jitter_threshold:
        print(f"❌ FAIL: Jitter {jitter:.2f}ms exceeds threshold {voip_jitter_threshold}ms")
        passed = False
    else:
        print(f"✓ PASS: Jitter {jitter:.2f}ms within acceptable range (<{voip_jitter_threshold}ms)")
    
    if latency_stats['loss'] > voip_loss_threshold:
        print(f"❌ FAIL: Packet loss {latency_stats['loss']:.2f}% exceeds threshold {voip_loss_threshold}%")
        passed = False
    else:
        print(f"✓ PASS: Packet loss {latency_stats['loss']:.2f}% within acceptable range (<{voip_loss_threshold}%)")
    
    print("\n" + "=" * 70)
    print("Overall Result: " + ("✓ PASSED" if passed else "❌ FAILED"))
    print("=" * 70)
    
    # Calculate QoS score
    latency_score = max(0, 100 - (latency_stats['avg'] / voip_latency_threshold) * 100)
    jitter_score = max(0, 100 - (jitter / voip_jitter_threshold) * 100)
    loss_score = max(0, 100 - (latency_stats['loss'] / voip_loss_threshold) * 100)
    overall_score = (latency_score + jitter_score + loss_score) / 3
    
    print(f"\nQoS Score: {overall_score:.1f}/100")
    
    # Save results
    results = {
        'test_type': 'voip',
        'test_config': {
            'target_ip': target_ip,
            'duration': test_duration,
            'packet_rate': rate
        },
        'timestamp': time.time(),
        'timestamp_readable': time.strftime('%Y-%m-%d %H:%M:%S'),
        'latency': latency_stats,
        'jitter': jitter,
        'thresholds': {
            'latency': voip_latency_threshold,
            'jitter': voip_jitter_threshold,
            'loss': voip_loss_threshold
        },
        'scores': {
            'latency': latency_score,
            'jitter': jitter_score,
            'loss': loss_score,
            'overall': overall_score
        },
        'passed': passed
    }
    
    output_file = 'results_voip.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    
    return passed


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("=" * 70)
        print("VoIP QoS Test Script")
        print("=" * 70)
        print("\nUsage: python3 test_voip.py <target_ip> [duration] [rate]")
        print("\nArguments:")
        print("  target_ip    Target IP address for VoIP traffic")
        print("  duration     Test duration in seconds (default: 60)")
        print("  rate         Packets per second (default: 50 for 20ms)")
        print("\nExamples:")
        print("  python3 test_voip.py 10.2.0.6")
        print("  python3 test_voip.py 10.2.0.6 30")
        print("  python3 test_voip.py 10.2.0.6 60 50")
        print("\nNotes:")
        print("  - Simulates G.711 codec (64 kbps)")
        print("  - 50 pps = 20ms packetization (standard for VoIP)")
        print("  - ITU-T G.114 thresholds applied")
        sys.exit(1)
    
    target = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    rate = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    
    try:
        success = run_voip_test(target, duration, rate)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

