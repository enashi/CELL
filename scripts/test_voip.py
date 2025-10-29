#!/usr/bin/env python3
"""
VoIP Traffic Test Script

Simulates VoIP traffic and measures QoS parameters:
- Latency
- Jitter
- Packet loss

Students should implement:
- Traffic generation (small packets, constant rate)
- Metric collection
- Result analysis
"""

import time
import subprocess
import json
import statistics

def generate_voip_traffic(duration=60, rate=50):
    """
    Generate VoIP-like traffic
    
    Args:
        duration: Test duration in seconds
        rate: Packets per second
    """
    print(f"Generating VoIP traffic for {duration} seconds at {rate} pps")
    # TODO: Implement VoIP traffic generation
    # Suggestion: Use UDP packets, 160 bytes payload (20ms G.711 audio)
    pass

def measure_latency(target_ip, count=100):
    """
    Measure latency using ping
    
    Args:
        target_ip: Target IP address
        count: Number of ping packets
    
    Returns:
        dict: Statistics (min, max, avg, stddev)
    """
    print(f"Measuring latency to {target_ip}")
    # TODO: Implement latency measurement
    # Suggestion: Use subprocess to run ping command, parse output
    
    return {
        'min': 0,
        'max': 0,
        'avg': 0,
        'stddev': 0,
        'loss': 0
    }

def measure_jitter(pcap_file):
    """
    Calculate jitter from packet capture
    
    Args:
        pcap_file: Path to pcap file
    
    Returns:
        float: Average jitter in ms
    """
    print(f"Analyzing jitter from {pcap_file}")
    # TODO: Implement jitter calculation
    # Suggestion: Parse pcap, calculate inter-arrival time variance
    
    return 0.0

def run_voip_test(target_ip, test_duration=60):
    """
    Run complete VoIP test
    """
    print("=" * 50)
    print("Starting VoIP QoS Test")
    print("=" * 50)
    
    # Measure baseline latency
    print("\n[1/3] Measuring baseline latency...")
    latency_stats = measure_latency(target_ip)
    
    # Generate VoIP traffic and capture packets
    print("\n[2/3] Generating VoIP traffic...")
    generate_voip_traffic(duration=test_duration)
    
    # Analyze jitter
    print("\n[3/3] Analyzing jitter...")
    jitter = measure_jitter("voip_capture.pcap")
    
    # Print results
    print("\n" + "=" * 50)
    print("VoIP QoS Test Results")
    print("=" * 50)
    print(f"Latency - Avg: {latency_stats['avg']:.2f}ms, "
          f"Min: {latency_stats['min']:.2f}ms, "
          f"Max: {latency_stats['max']:.2f}ms")
    print(f"Jitter: {jitter:.2f}ms")
    print(f"Packet Loss: {latency_stats['loss']:.2f}%")
    
    # Evaluate against thresholds
    print("\n" + "=" * 50)
    print("QoS Evaluation")
    print("=" * 50)
    
    voip_latency_threshold = 150  # ms (ITU-T G.114)
    voip_jitter_threshold = 30    # ms
    voip_loss_threshold = 1.0     # %
    
    passed = True
    if latency_stats['avg'] > voip_latency_threshold:
        print(f"❌ FAIL: Latency {latency_stats['avg']:.2f}ms exceeds threshold {voip_latency_threshold}ms")
        passed = False
    else:
        print(f"✓ PASS: Latency within acceptable range")
    
    if jitter > voip_jitter_threshold:
        print(f"❌ FAIL: Jitter {jitter:.2f}ms exceeds threshold {voip_jitter_threshold}ms")
        passed = False
    else:
        print(f"✓ PASS: Jitter within acceptable range")
    
    if latency_stats['loss'] > voip_loss_threshold:
        print(f"❌ FAIL: Packet loss {latency_stats['loss']:.2f}% exceeds threshold {voip_loss_threshold}%")
        passed = False
    else:
        print(f"✓ PASS: Packet loss within acceptable range")
    
    print("\nOverall: " + ("✓ PASSED" if passed else "❌ FAILED"))
    
    # Save results
    results = {
        'test_type': 'voip',
        'timestamp': time.time(),
        'latency': latency_stats,
        'jitter': jitter,
        'passed': passed
    }
    
    with open('results_voip.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to results_voip.json")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 test_voip.py <target_ip> [duration]")
        print("Example: python3 test_voip.py 192.168.70.135 60")
        sys.exit(1)
    
    target = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    
    run_voip_test(target, duration)

