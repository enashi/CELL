#!/usr/bin/env python3
"""
VoIP Traffic Test Script - Version avec support loopback
Permet de tester en local avec mesure de jitter
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
        """Generate VoIP traffic"""
        if not self.running:
            return
        
        packet_interval = 1.0 / rate
        payload_size = 160  # G.711 20ms frame
        
        start_time = time.time()
        next_send_time = start_time
        sequence = 0
        
        while self.running and (time.time() - start_time) < duration:
            try:
                relative_timestamp = int((time.time() - start_time) * 1000)
                header = struct.pack('!II', relative_timestamp, sequence)
                payload = b'V' * payload_size
                packet = header + payload
                
                self.socket.sendto(packet, (self.target_ip, self.target_port))
                self.stats['packets_sent'] += 1
                self.stats['bytes_sent'] += len(packet)
                sequence += 1
                
                next_send_time += packet_interval
                sleep_time = next_send_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                self.stats['errors'] += 1
                if self.stats['errors'] < 5:
                    print(f"Error sending packet: {e}")
        
        duration_actual = time.time() - start_time
        bitrate_kbps = (self.stats['bytes_sent'] * 8) / (duration_actual * 1000)
        
        print("\nVoIP Traffic Statistics:")
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
    """Measure latency using ping"""
    print(f"Measuring latency to {target_ip} ({count} packets)...")
    
    try:
        cmd = ['ping', '-c', str(count), '-i', '0.2', target_ip]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"Ping failed: {result.stderr}")
            return {'min': 0, 'max': 0, 'avg': 0, 'stddev': 0, 'loss': 100.0}
        
        output = result.stdout
        
        # Extract packet loss
        loss = 0.0
        for line in output.split('\n'):
            if 'packet loss' in line:
                try:
                    loss = float(line.split('%')[0].split()[-1])
                except:
                    pass
        
        # Extract latency statistics
        min_latency = 0
        max_latency = 0
        avg_latency = 0
        stddev_latency = 0
        
        for line in output.split('\n'):
            if 'min/avg/max' in line or 'rtt' in line:
                try:
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
    
    except Exception as e:
        print(f"Error measuring latency: {e}")
        return {'min': 0, 'max': 0, 'avg': 0, 'stddev': 0, 'loss': 100.0}


def measure_jitter_from_latency(latency_stats):
    """
    Estimate jitter from latency standard deviation
    This is a fallback when packet capture isn't possible
    """
    # Jitter approximation: use stddev as jitter estimate
    # This is not perfect but gives a reasonable estimate
    jitter = latency_stats.get('stddev', 0)
    
    print("Jitter estimation:")
    print("  Method: Derived from latency variance")
    print("  Estimated jitter: {jitter:.2f}ms")
    
    return jitter


def create_echo_server(port=5060, duration=65):
    """
    Create a simple UDP echo server for testing
    This allows local jitter measurement
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', port))
        sock.settimeout(1.0)
        
        print(f"Echo server listening on port {port}...")
        start_time = time.time()
        packets_echoed = 0
        
        while (time.time() - start_time) < duration:
            try:
                data, addr = sock.recvfrom(2048)
                # Echo back
                sock.sendto(data, addr)
                packets_echoed += 1
            except socket.timeout:
                continue
            except Exception as e:
                break
        
        sock.close()
        print(f"Echo server stopped. Echoed {packets_echoed} packets.")
        
    except Exception as e:
        print(f"Echo server error: {e}")


def measure_jitter_with_echo(duration=10):
    """
    Measure jitter using echo method
    Send packets to localhost and measure round-trip time variance
    """
    print(f"Measuring jitter with echo method ({duration}s)...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        
        rtts = []
        start_time = time.time()
        sequence = 0
        packet_interval = 0.02  # 20ms
        
        while (time.time() - start_time) < duration:
            try:
                # Send packet
                send_time = time.time()
                header = struct.pack('!II', int(send_time * 1000), sequence)
                payload = b'E' * 160
                packet = header + payload
                
                sock.sendto(packet, ('127.0.0.1', 5060))
                
                # Wait for echo
                try:
                    data, addr = sock.recvfrom(2048)
                    recv_time = time.time()
                    rtt = (recv_time - send_time) * 1000  # Convert to ms
                    rtts.append(rtt)
                except socket.timeout:
                    pass
                
                sequence += 1
                
                # Wait for next interval
                time.sleep(max(0, packet_interval - (time.time() - send_time)))
                
            except Exception as e:
                break
        
        sock.close()
        
        if len(rtts) < 2:
            print("  Warning: Not enough RTT samples")
            return 0.0
        
        # Calculate jitter from RTT variance
        # Jitter = average absolute difference between consecutive RTTs
        jitter_samples = []
        for i in range(1, len(rtts)):
            jitter_samples.append(abs(rtts[i] - rtts[i-1]))
        
        jitter = statistics.mean(jitter_samples) if jitter_samples else 0.0
        
        print(f"  Received {len(rtts)} echo responses")
        print(f"  Average RTT: {statistics.mean(rtts):.2f}ms")
        print(f"  RTT variance: {statistics.stdev(rtts):.2f}ms" if len(rtts) > 1 else "  RTT variance: N/A")
        print(f"  Jitter: {jitter:.2f}ms")
        
        return jitter
    
    except Exception as e:
        print(f"Error measuring jitter with echo: {e}")
        return 0.0


# =============================================================================
# MAIN TEST FUNCTION
# =============================================================================

def run_voip_test(target_ip, test_duration=60, rate=50, use_echo=False):
    """
    Run complete VoIP test
    
    Args:
        target_ip: Target IP address for VoIP traffic
        test_duration: Duration of traffic generation in seconds
        rate: Packets per second
        use_echo: Use echo server for local jitter measurement
    """
    print("=" * 70)
    print("Starting VoIP QoS Test")
    print("=" * 70)
    print(f"Target IP: {target_ip}")
    print(f"Duration: {test_duration}s")
    print(f"Packet rate: {rate} pps (20ms packetization)")
    print(f"Echo mode: {'Enabled (local jitter test)' if use_echo else 'Disabled'}")
    
    # Measure baseline latency
    print("\n[1/4] Measuring baseline latency...")
    latency_stats = measure_latency(target_ip, count=50)
    
    jitter = 0.0
    
    if use_echo:
        # Start echo server in background
        print("\n[2/4] Starting echo server for jitter measurement...")
        echo_thread = threading.Thread(
            target=create_echo_server, 
            args=(5060, test_duration + 5),
            daemon=True
        )
        echo_thread.start()
        time.sleep(1)  # Let server start
        
        # Measure jitter with echo
        print("\n[3/4] Measuring jitter with echo method...")
        jitter = measure_jitter_with_echo(duration=min(test_duration, 30))
    else:
        # Use latency-based jitter estimation
        print("\n[2/4] Estimating jitter from latency variance...")
        jitter = measure_jitter_from_latency(latency_stats)
        
        # Generate VoIP traffic (for demonstration)
        print("\n[3/4] Generating VoIP traffic...")
        generator = VoIPTrafficGenerator(target_ip, target_port=5060, source_port=5061)
        
        if generator.start():
            generator.generate_traffic(duration=test_duration, rate=rate)
            generator.stop()
        else:
            print("Failed to start VoIP traffic generator")
    
    # Print results
    print("\n[4/4] Finalizing results...")
    print("\n" + "=" * 70)
    print("VoIP QoS Test Results")
    print("=" * 70)
    print("Latency:")
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
    
    voip_latency_threshold = 150
    voip_jitter_threshold = 30
    voip_loss_threshold = 1.0
    
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
            'packet_rate': rate,
            'echo_mode': use_echo
        },
        'timestamp': time.time(),
        'timestamp_readable': time.strftime('%Y-%m-%d %H:%M:%S'),
        'latency': latency_stats,
        'jitter': jitter,
        'jitter_method': 'echo_rtt' if use_echo else 'latency_stddev',
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


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("=" * 70)
        print("VoIP QoS Test Script - Enhanced Version")
        print("=" * 70)
        print("\nUsage: python3 test_voip_fixed.py <target_ip> [duration] [rate] [--echo]")
        print("\nArguments:")
        print("  target_ip    Target IP address for latency measurement")
        print("  duration     Test duration in seconds (default: 60)")
        print("  rate         Packets per second (default: 50 for 20ms)")
        print("  --echo       Use echo server for local jitter measurement")
        print("\nExamples:")
        print("  # Standard test (jitter from latency variance)")
        print("  python3 test_voip_fixed.py 10.2.0.6")
        print()
        print("  # Echo mode (local jitter measurement)")
        print("  python3 test_voip_fixed.py 127.0.0.1 60 50 --echo")
        print()
        print("  # Remote test with echo server running on target")
        print("  python3 test_voip_fixed.py 10.2.0.6 60 50 --echo")
        print("\nNotes:")
        print("  - Standard mode: jitter estimated from latency variance")
        print("  - Echo mode: requires echo server (or use 127.0.0.1 for local)")
        print("  - ITU-T G.114 thresholds applied")
        sys.exit(1)
    
    target = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    rate = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    use_echo = '--echo' in sys.argv
    
    try:
        success = run_voip_test(target, duration, rate, use_echo)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

