#!/usr/bin/env python3
"""
Quick test script to verify automatic detection of IPs and interface
"""

import sys
import os

print("="*70)
print("Auto-Detection Test - IPs and Network Interface")
print("="*70)
print()

# Test 1: IP Detection
print("TEST 1: UE IP Address Detection")
print("-" * 70)

try:
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from qos_tests import get_ue_ips_from_interfaces, TestConfig
    
    detected_ips = get_ue_ips_from_interfaces()
    
    if detected_ips:
        print("✓ Interfaces detected:")
        for iface, ip in detected_ips.items():
            print(f"  {iface}: {ip}")
        print()
        
        print("Mapped to UE roles:")
        print(f"  VoIP UE:  {TestConfig.UE_VOIP_IP}")
        print(f"  Video UE: {TestConfig.UE_VIDEO_IP}")
        print(f"  Data UE:  {TestConfig.UE_WEB_IP}")
    else:
        print("✗ No UE interfaces detected")
        print("  Make sure UERANSIM UEs are running")
except Exception as e:
    print(f"✗ IP detection failed: {e}")

print()

# Test 2: Interface Detection
print("TEST 2: Network Interface Detection")
print("-" * 70)

try:
    from congestion_tests import detect_upf_interface
    
    detected_iface = detect_upf_interface()
    
    if detected_iface:
        print(f"✓ Interface detected: {detected_iface}")
        
        # Get interface info
        import subprocess
        result = subprocess.run(['ip', 'addr', 'show', detected_iface],
                              capture_output=True, text=True)
        
        # Extract IP
        for line in result.stdout.split('\n'):
            if 'inet ' in line and 'inet6' not in line:
                ip = line.strip().split()[1]
                print(f"  IP address: {ip}")
                break
    else:
        print("✗ No interface detected")
        print("  You may need to specify --interface manually")
except Exception as e:
    print(f"✗ Interface detection failed: {e}")

print()
print("="*70)
print("Summary")
print("="*70)

print("""
Your configuration will be:

QoS Tests:
  python3 qos_tests.py
  → Auto-detects UE IPs

Congestion Tests:
  sudo python3 congestion_tests.py --test all
  → Auto-detects UE IPs + network interface

No manual configuration needed!
""")

print("To run a quick test:")
print("  python3 qos_tests.py --scenario mixed")
print()
