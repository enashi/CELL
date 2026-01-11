#!/usr/bin/env python3
"""
Video Streaming Test Script - Complete Implementation

Simulates video streaming traffic and measures QoS parameters:
- Throughput
- Buffering events
- Quality degradation

Implementation supports both iperf3 and socket-based traffic generation.
Recommended: Use with iperf3 server for accurate throughput measurement.
"""

import time
import subprocess
import json
import sys
import socket
import threading
import struct

# =============================================================================
# CONFIGURATION
# =============================================================================

class VideoTestConfig:
    """Configuration for video streaming tests"""
    
    # Video streaming profiles (bitrates in Mbps)
    VIDEO_PROFILES = {
        'sd': 2.0,      # SD quality (480p)
        'hd': 5.0,      # HD quality (720p)
        'fhd': 8.0,     # Full HD (1080p)
        '4k': 25.0      # 4K quality
    }
    
    # QoS thresholds
    THROUGHPUT_THRESHOLD = 0.95  # 95% of target bitrate
    
    # iperf3 settings
    IPERF3_PORT = 5201
    
    # Socket-based settings
    SOCKET_PORT = 5070
    PACKET_SIZE = 1400  # bytes (near MTU)


# =============================================================================
# IPERF3-BASED TESTING (RECOMMENDED)
# =============================================================================

def test_with_iperf3(target_ip, bitrate_mbps=5, duration=60, port=5201):
    """
    Generate video streaming traffic using iperf3
    
    This is the RECOMMENDED method as it provides:
    - Accurate throughput measurement
    - Standard tool used in industry
    - Real network load simulation
    
    Prerequisites:
    - iperf3 server running on target_ip:port
    - Start server with: iperf3 -s -p 5201
    
    Args:
        target_ip: iperf3 server IP address
        bitrate_mbps: Target bitrate in Mbps
        duration: Test duration in seconds
        port: iperf3 server port
    
    Returns:
        dict: Test results with throughput statistics
    """
    print(f"Testing video streaming with iperf3")
    print(f"  Server: {target_ip}:{port}")
    print(f"  Target bitrate: {bitrate_mbps} Mbps")
    print(f"  Duration: {duration}s")
    
    try:
        # Construct iperf3 command
        # -c: client mode
        # -u: UDP (video streaming)
        # -b: bitrate
        # -t: time
        # -J: JSON output
        # -p: port
        cmd = [
            'iperf3',
            '-c', target_ip,
            '-u',  # UDP for video
            '-b', f'{bitrate_mbps}M',
            '-t', str(duration),
            '-J',  # JSON output for parsing
            '-p', str(port)
        ]
        
        print(f"\nRunning: {' '.join(cmd)}")
        print("Generating traffic...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration+30)
        
        if result.returncode != 0:
            print(f"iperf3 error: {result.stderr}")
            return None
        
        # Parse JSON output
        try:
            data = json.loads(result.stdout)
            
            # Extract results
            end_data = data.get('end', {})
            sum_data = end_data.get('sum', {})
            
            # Throughput in bits per second
            bits_per_second = sum_data.get('bits_per_second', 0)
            throughput_mbps = bits_per_second / 1_000_000
            
            # Packet statistics
            packets_sent = sum_data.get('packets', 0)
            lost_packets = sum_data.get('lost_packets', 0)
            lost_percent = sum_data.get('lost_percent', 0)
            
            # Jitter
            jitter_ms = sum_data.get('jitter_ms', 0)
            
            results = {
                'throughput_mbps': throughput_mbps,
                'bitrate_target_mbps': bitrate_mbps,
                'throughput_ratio': throughput_mbps / bitrate_mbps if bitrate_mbps > 0 else 0,
                'packets_sent': packets_sent,
                'packets_lost': lost_packets,
                'loss_percent': lost_percent,
                'jitter_ms': jitter_ms,
                'duration': duration
            }
            
            print(f"\niperf3 Test Results:")
            print(f"  Throughput: {throughput_mbps:.2f} Mbps")
            print(f"  Target: {bitrate_mbps} Mbps")
            print(f"  Ratio: {results['throughput_ratio']*100:.1f}%")
            print(f"  Packet loss: {lost_percent:.2f}%")
            print(f"  Jitter: {jitter_ms:.2f}ms")
            
            return results
        
        except json.JSONDecodeError as e:
            print(f"Error parsing iperf3 output: {e}")
            print(f"Output: {result.stdout[:500]}")
            return None
    
    except subprocess.TimeoutExpired:
        print("iperf3 timeout")
        return None
    
    except FileNotFoundError:
        print("ERROR: iperf3 not found")
        print("Install with: sudo apt-get install iperf3")
        return None
    
    except Exception as e:
        print(f"Error running iperf3: {e}")
        return None


# =============================================================================
# SOCKET-BASED TESTING (FALLBACK)
# =============================================================================

class VideoTrafficGenerator:
    """
    Generate video streaming traffic using UDP sockets
    
    This is a FALLBACK method if iperf3 is not available.
    Less accurate than iperf3 but provides basic testing.
    """
    
    def __init__(self, target_ip, target_port=5070):
        self.target_ip = target_ip
        self.target_port = target_port
        self.socket = None
        self.running = False
        self.stats = {
            'packets_sent': 0,
            'bytes_sent': 0,
            'errors': 0
        }
    
    def start(self):
        """Initialize socket"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.running = True
            return True
        except Exception as e:
            print(f"Error creating socket: {e}")
            return False
    
    def generate_traffic(self, bitrate_mbps=5, duration=60):
        """
        Generate video streaming traffic
        
        Args:
            bitrate_mbps: Target bitrate in Mbps
            duration: Duration in seconds
        
        Returns:
            dict: Traffic statistics
        """
        if not self.running:
            return None
        
        # Calculate parameters
        target_bps = bitrate_mbps * 1_000_000  # Convert to bits per second
        packet_size = VideoTestConfig.PACKET_SIZE
        packets_per_second = target_bps / (packet_size * 8)
        packet_interval = 1.0 / packets_per_second
        
        print(f"\nGenerating video traffic:")
        print(f"  Target: {bitrate_mbps} Mbps")
        print(f"  Packet size: {packet_size} bytes")
        print(f"  Rate: {packets_per_second:.1f} packets/sec")
        
        start_time = time.time()
        next_send_time = start_time
        sequence = 0
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # Create packet with header (timestamp + sequence)
                timestamp = int(time.time() * 1000)
                header = struct.pack('!II', timestamp, sequence)
                payload = b'V' * (packet_size - len(header))
                packet = header + payload
                
                # Send
                self.socket.sendto(packet, (self.target_ip, self.target_port))
                self.stats['packets_sent'] += 1
                self.stats['bytes_sent'] += len(packet)
                sequence += 1
                
                # Rate limiting
                next_send_time += packet_interval
                sleep_time = next_send_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            except Exception as e:
                self.stats['errors'] += 1
                if self.stats['errors'] < 5:
                    print(f"Send error: {e}")
        
        # Calculate actual throughput
        duration_actual = time.time() - start_time
        throughput_mbps = (self.stats['bytes_sent'] * 8) / (duration_actual * 1_000_000)
        
        return {
            'throughput_mbps': throughput_mbps,
            'bitrate_target_mbps': bitrate_mbps,
            'throughput_ratio': throughput_mbps / bitrate_mbps if bitrate_mbps > 0 else 0,
            'packets_sent': self.stats['packets_sent'],
            'bytes_sent': self.stats['bytes_sent'],
            'duration': duration_actual,
            'errors': self.stats['errors']
        }
    
    def stop(self):
        """Stop traffic generation"""
        self.running = False
        if self.socket:
            self.socket.close()


def test_with_sockets(target_ip, bitrate_mbps=5, duration=60):
    """
    Generate video streaming traffic using sockets (fallback method)
    
    Args:
        target_ip: Target IP
        bitrate_mbps: Target bitrate in Mbps
        duration: Duration in seconds
    
    Returns:
        dict: Test results
    """
    print("Testing video streaming with UDP sockets (fallback method)")
    print("Note: For accurate results, use iperf3 instead")
    
    generator = VideoTrafficGenerator(target_ip, VideoTestConfig.SOCKET_PORT)
    
    if not generator.start():
        return None
    
    results = generator.generate_traffic(bitrate_mbps, duration)
    generator.stop()
    
    if results:
        print(f"\nSocket Test Results:")
        print(f"  Throughput: {results['throughput_mbps']:.2f} Mbps")
        print(f"  Target: {bitrate_mbps} Mbps")
        print(f"  Ratio: {results['throughput_ratio']*100:.1f}%")
        print(f"  Packets sent: {results['packets_sent']}")
    
    return results


# =============================================================================
# MAIN TEST FUNCTION
# =============================================================================

def run_video_test(target_ip, bitrate=5, test_duration=60, use_iperf3=True):
    """
    Run complete video streaming test
    
    Args:
        target_ip: Target IP address
        bitrate: Target bitrate in Mbps
        test_duration: Test duration in seconds
        use_iperf3: Use iperf3 if available (recommended)
    
    Returns:
        bool: True if test passed
    """
    print("=" * 70)
    print("Starting Video Streaming QoS Test")
    print("=" * 70)
    print(f"Target IP: {target_ip}")
    print(f"Bitrate: {bitrate} Mbps")
    print(f"Duration: {test_duration}s")
    
    # Determine video quality profile
    quality = 'custom'
    for profile, profile_bitrate in VideoTestConfig.VIDEO_PROFILES.items():
        if abs(bitrate - profile_bitrate) < 0.5:
            quality = profile
            break
    print(f"Quality profile: {quality.upper()}")
    
    # Run test
    if use_iperf3:
        print("\n" + "-" * 70)
        print("Method: iperf3 (Recommended)")
        print("-" * 70)
        results = test_with_iperf3(target_ip, bitrate, test_duration)
        
        if results is None:
            print("\niperf3 test failed, falling back to socket method...")
            results = test_with_sockets(target_ip, bitrate, test_duration)
    else:
        print("\n" + "-" * 70)
        print("Method: UDP Sockets (Fallback)")
        print("-" * 70)
        results = test_with_sockets(target_ip, bitrate, test_duration)
    
    if results is None:
        print("\n❌ Test failed - could not generate traffic")
        return False
    
    # Evaluate results
    print("\n" + "=" * 70)
    print("Video Streaming QoS Test Results")
    print("=" * 70)
    print(f"Target Bitrate: {bitrate} Mbps")
    print(f"Achieved Throughput: {results['throughput_mbps']:.2f} Mbps")
    print(f"Throughput Ratio: {results['throughput_ratio']*100:.1f}%")
    
    if 'loss_percent' in results:
        print(f"Packet Loss: {results['loss_percent']:.2f}%")
    if 'jitter_ms' in results:
        print(f"Jitter: {results['jitter_ms']:.2f}ms")
    
    # Evaluate against threshold
    print("\n" + "=" * 70)
    print("QoS Evaluation")
    print("=" * 70)
    
    threshold = VideoTestConfig.THROUGHPUT_THRESHOLD
    passed = results['throughput_ratio'] >= threshold
    
    if passed:
        print(f"✓ PASS: Throughput {results['throughput_ratio']*100:.1f}% "
              f">= {threshold*100:.1f}% of target")
    else:
        print(f"❌ FAIL: Throughput {results['throughput_ratio']*100:.1f}% "
              f"< {threshold*100:.1f}% of target")
    
    # Calculate quality score
    throughput_score = min(100, results['throughput_ratio'] * 100)
    loss_score = 100 - (results.get('loss_percent', 0) * 10)  # 1% loss = 10 point deduction
    overall_score = (throughput_score + loss_score) / 2
    
    print(f"\nQuality Score: {overall_score:.1f}/100")
    print(f"  Throughput: {throughput_score:.1f}/100")
    print(f"  Loss: {loss_score:.1f}/100")
    
    # Buffering estimation
    if results['throughput_ratio'] < 1.0:
        buffer_shortage = (1.0 - results['throughput_ratio']) * test_duration
        print(f"\nEstimated buffering time: {buffer_shortage:.1f}s "
              f"({buffer_shortage/test_duration*100:.1f}% of playback)")
    
    print("\n" + "=" * 70)
    print("Overall Result: " + ("✓ PASSED" if passed else "❌ FAILED"))
    print("=" * 70)
    
    # Save results
    test_results = {
        'test_type': 'video',
        'test_config': {
            'target_ip': target_ip,
            'bitrate_target_mbps': bitrate,
            'quality_profile': quality,
            'duration': test_duration,
            'method': 'iperf3' if use_iperf3 else 'sockets'
        },
        'timestamp': time.time(),
        'timestamp_readable': time.strftime('%Y-%m-%d %H:%M:%S'),
        'results': results,
        'threshold': threshold,
        'scores': {
            'throughput': throughput_score,
            'loss': loss_score,
            'overall': overall_score
        },
        'passed': passed
    }
    
    output_file = 'results_video.json'
    with open(output_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    
    return passed


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("=" * 70)
        print("Video Streaming QoS Test Script")
        print("=" * 70)
        print("\nUsage: python3 test_video.py <target_ip> [bitrate_mbps] [duration] [--no-iperf3]")
        print("\nArguments:")
        print("  target_ip      Target IP address (iperf3 server or receiver)")
        print("  bitrate_mbps   Target bitrate in Mbps (default: 5)")
        print("  duration       Test duration in seconds (default: 60)")
        print("  --no-iperf3    Force socket-based method (skip iperf3)")
        print("\nQuality Profiles:")
        print("  SD  (480p):  2 Mbps")
        print("  HD  (720p):  5 Mbps")
        print("  FHD (1080p): 8 Mbps")
        print("  4K:          25 Mbps")
        print("\nExamples:")
        print("  # Test with iperf3 (recommended)")
        print("  iperf3 -s -p 5201  # On server")
        print("  python3 test_video.py 192.168.70.150 5 60")
        print()
        print("  # Test with sockets (fallback)")
        print("  python3 test_video.py 10.2.0.6 5 60 --no-iperf3")
        print("\nNotes:")
        print("  - iperf3 method is RECOMMENDED for accurate results")
        print("  - Start iperf3 server first: iperf3 -s -p 5201")
        print("  - Socket method is fallback if iperf3 unavailable")
        sys.exit(1)
    
    target = sys.argv[1]
    bitrate = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    use_iperf3 = '--no-iperf3' not in sys.argv
    
    try:
        success = run_video_test(target, bitrate, duration, use_iperf3)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

