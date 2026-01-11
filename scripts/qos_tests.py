#!/usr/bin/env python3
"""
Comprehensive 5G QoS Testing Suite
===================================

This script implements all 4 test scenarios for validating QoS differentiation
in a 5G Core Network deployment:

Scenario 1: VoIP Traffic - Tests real-time traffic protection (Priority 20)
Scenario 2: Video Streaming - Tests adaptive streaming (Priority 80)
Scenario 3: Best-Effort - Tests background data traffic (Priority 90)
Scenario 4: Mixed Traffic - Tests simultaneous traffic prioritization

Author: 5G QoS Testing Framework
Purpose: Master's Thesis - CELL Course, Sorbonne University
"""

import socket
import struct
import time
import threading
import statistics
import json
import sys
import argparse
from datetime import datetime
from collections import deque

# =============================================================================
# CONFIGURATION SECTION
# =============================================================================

def get_ue_ips_from_interfaces():
    """
    Automatically detect UE IP addresses from network interfaces.
    
    Looks for uesimtun0, uesimtun1, uesimtun2 interfaces and extracts their IPs.
    Typically:
    - uesimtun0 = Web UE (10.3.0.2)
    - uesimtun1 = Video UE (10.2.0.2)
    - uesimtun2 = VoIP UE (10.1.0.2)
    
    Returns:
        dict: Mapping of interface names to IP addresses
        None: If interfaces not found
    """
    import netifaces
    
    ue_ips = {}
    
    try:
        # Get all network interfaces
        interfaces = netifaces.interfaces()
        
        # Look for uesimtun interfaces
        for iface in interfaces:
            if iface.startswith('uesimtun'):
                try:
                    # Get IPv4 addresses for this interface
                    addrs = netifaces.ifaddresses(iface)
                    if netifaces.AF_INET in addrs:
                        ip = addrs[netifaces.AF_INET][0]['addr']
                        ue_ips[iface] = ip
                except:
                    continue
        
        return ue_ips if ue_ips else None
    
    except ImportError:
        # netifaces not available, try alternative method using subprocess
        import subprocess
        try:
            # Use ip command to get interface IPs
            result = subprocess.run(['ip', 'addr', 'show'], 
                                  capture_output=True, text=True, check=True)
            
            current_iface = None
            for line in result.stdout.split('\n'):
                # Look for uesimtun interfaces
                if 'uesimtun' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        current_iface = parts[1].strip().split('@')[0]
                
                # Extract IP address
                if current_iface and 'inet ' in line and 'inet6' not in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip = parts[1].split('/')[0]
                        ue_ips[current_iface] = ip
                        current_iface = None
            
            return ue_ips if ue_ips else None
        
        except:
            return None


def load_config_from_file(filename='qos_config.json'):
    """
    Load configuration from external JSON file.
    
    Expected format:
    {
        "ue_voip_ip": "10.1.0.2",
        "ue_video_ip": "10.2.0.2",
        "ue_web_ip": "10.3.0.2"
    }
    
    Args:
        filename: Path to configuration file
    
    Returns:
        dict: Configuration values or None if file doesn't exist
    """
    import os
    
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        return config
    except:
        return None


class TestConfig:
    """
    Central configuration for all test scenarios.
    
    IP addresses are automatically detected from network interfaces.
    Override by creating qos_config.json file or setting environment variables.
    
    Priority order:
    1. Environment variables (UE_VOIP_IP, UE_VIDEO_IP, UE_WEB_IP)
    2. Configuration file (qos_config.json)
    3. Automatic detection from interfaces
    4. Hardcoded defaults (fallback)
    """
    
    # Default fallback IPs
    _DEFAULT_VOIP_IP = "10.1.0.2"
    _DEFAULT_VIDEO_IP = "10.2.0.2"
    _DEFAULT_WEB_IP = "10.3.0.2"
    
    @staticmethod
    def _get_ue_ips():
        """
        Determine UE IP addresses using priority order.
        
        Returns:
            tuple: (voip_ip, video_ip, web_ip)
        """
        import os
        
        # Priority 1: Environment variables
        env_voip = os.getenv('UE_VOIP_IP')
        env_video = os.getenv('UE_VIDEO_IP')
        env_web = os.getenv('UE_WEB_IP')
        
        if env_voip and env_video and env_web:
            return env_voip, env_video, env_web
        
        # Priority 2: Configuration file
        config = load_config_from_file()
        if config and all(k in config for k in ['ue_voip_ip', 'ue_video_ip', 'ue_web_ip']):
            return config['ue_voip_ip'], config['ue_video_ip'], config['ue_web_ip']
        
        # Priority 3: Automatic detection
        ue_ips = get_ue_ips_from_interfaces()
        if ue_ips:
            # Map interfaces to roles based on IP pattern
            # Typically: 10.1.0.x = VoIP, 10.2.0.x = Video, 10.3.0.x = Web
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
        
        # Priority 4: Hardcoded defaults
        return TestConfig._DEFAULT_VOIP_IP, TestConfig._DEFAULT_VIDEO_IP, TestConfig._DEFAULT_WEB_IP
    
    # Initialize UE IPs
    UE_VOIP_IP, UE_VIDEO_IP, UE_WEB_IP = _get_ue_ips()
    
    # Port assignments for different traffic types
    PORT_VOIP = 5060           # VoIP traffic port
    PORT_VIDEO = 5070          # Video streaming port
    PORT_DATA = 5080           # Best-effort data port
    
    # Test durations (seconds)
    VOIP_TEST_DURATION = 30
    VIDEO_TEST_DURATION = 30
    DATA_TEST_DURATION = 30
    MIXED_TEST_DURATION = 30
    
    # VoIP parameters (G.711 codec simulation)
    VOIP_PACKET_SIZE = 160     # bytes (20ms of audio at 64 kbps)
    VOIP_PACKET_RATE = 50      # packets per second (20ms interval)
    VOIP_BITRATE = 64          # kbps
    
    # Video streaming parameters
    VIDEO_FPS = 30             # frames per second
    VIDEO_BITRATES = [500, 1000, 2000, 5000]  # kbps to test
    VIDEO_BUFFER_MAX = 10      # seconds
    
    # Best-effort data parameters
    DATA_RATE_MBPS = 10        # Target data rate in Mbps
    DATA_PACKET_SIZE = 1400    # MTU-sized packets
    
    # Congestion generation parameters
    CONGESTION_RATE_MBPS = 100 # Mbps for congestion tests
    
    # Socket buffer sizes (increase for high-throughput tests)
    SOCKET_BUFFER_SIZE = 2 * 1024 * 1024  # 2 MB


# =============================================================================
# SCENARIO 1: VoIP TRAFFIC TESTING
# =============================================================================

class VoIPServer:
    """
    VoIP traffic receiver and analyzer.
    
    Simulates a VoIP receiver that measures:
    - One-way latency (delay from sender to receiver)
    - Jitter (variation in latency between consecutive packets)
    - Packet loss rate
    
    The server receives UDP packets containing sequence numbers and timestamps,
    calculates metrics in real-time, and provides statistics at the end.
    """
    
    def __init__(self, host='0.0.0.0', port=TestConfig.PORT_VOIP, verbose=False):
        """
        Initialize VoIP server.
        
        Args:
            host: IP address to bind to (0.0.0.0 = all interfaces)
            port: UDP port to listen on
            verbose: Enable detailed logging
        """
        self.host = host
        self.port = port
        self.verbose = verbose
        self.socket = None
        self.running = False
        
        # Statistics tracking
        self.packets_received = 0
        self.packets_expected = 0  # Based on highest sequence number seen
        self.latencies = []        # List of one-way delays in ms
        self.jitters = []          # List of jitter values in ms
        self.last_packet_time = None
        self.last_latency = None
    
    def start(self):
        """
        Start the VoIP server and begin receiving packets.
        Creates UDP socket, binds to specified address, and enters receive loop.
        """
        # Create UDP socket for receiving VoIP packets
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.running = True
        
        if self.verbose:
            print(f"VoIP Server listening on {self.host}:{self.port}")
        
        self.receive_loop()
    
    def receive_loop(self):
        """
        Main packet reception loop.
        Continuously receives packets and processes them until stopped.
        Uses timeout to allow clean shutdown.
        """
        self.socket.settimeout(1.0)  # 1 second timeout for clean shutdown
        
        while self.running:
            try:
                # Receive packet (max 2048 bytes for VoIP)
                data, addr = self.socket.recvfrom(2048)
                arrival_time = time.time()
                
                # Process the received packet
                self.process_packet(data, arrival_time)
                
            except socket.timeout:
                # Timeout is normal, allows checking self.running flag
                continue
            except Exception as e:
                if self.running:
                    print(f"VoIP Server error: {e}")
    
    def process_packet(self, data, arrival_time):
        """
        Process a received VoIP packet and update statistics.
        
        Packet format (12 bytes header + payload):
        - Bytes 0-3: Sequence number (uint32)
        - Bytes 4-11: Send timestamp (double)
        - Bytes 12+: Payload (voice data)
        
        Args:
            data: Raw packet bytes
            arrival_time: Time when packet was received
        """
        try:
            # Verify minimum packet size
            if len(data) < 12:
                return
            
            # Extract header fields
            # '!I' = network byte order, unsigned int (4 bytes)
            seq_num = struct.unpack('!I', data[0:4])[0]
            
            # '!d' = network byte order, double (8 bytes)
            send_timestamp = struct.unpack('!d', data[4:12])[0]
            
            # Update packet counters
            self.packets_received += 1
            self.packets_expected = max(self.packets_expected, seq_num + 1)
            
            # Calculate one-way latency in milliseconds
            latency = (arrival_time - send_timestamp) * 1000
            self.latencies.append(latency)
            
            # Calculate jitter (variation between consecutive packet latencies)
            # Jitter is the absolute difference in latency between consecutive packets
            if self.last_latency is not None:
                jitter = abs(latency - self.last_latency)
                self.jitters.append(jitter)
            
            self.last_latency = latency
            self.last_packet_time = arrival_time
            
            # Periodic status update (every 500 packets)
            if self.verbose and self.packets_received % 500 == 0:
                avg_lat = statistics.mean(self.latencies[-100:]) if len(self.latencies) >= 100 else statistics.mean(self.latencies)
                print(f"VoIP: {self.packets_received} packets, latency {avg_lat:.2f}ms")
        
        except Exception as e:
            if self.verbose:
                print(f"Packet processing error: {e}")
    
    def get_statistics(self):
        """
        Calculate and return comprehensive VoIP statistics.
        
        Returns:
            dict: Statistics including latency, jitter, and packet loss metrics
            None: If no data was collected
        """
        if not self.latencies:
            return None
        
        # Calculate packet loss percentage
        # Packets lost = expected (based on sequence numbers) - received
        packets_lost = self.packets_expected - self.packets_received
        loss_percent = (packets_lost / self.packets_expected * 100) if self.packets_expected > 0 else 0
        
        return {
            'packets_sent': self.packets_expected,
            'packets_received': self.packets_received,
            'packets_lost': packets_lost,
            'packet_loss_percent': loss_percent,
            'latency': {
                'min': min(self.latencies),
                'max': max(self.latencies),
                'avg': statistics.mean(self.latencies),
                'median': statistics.median(self.latencies),
                'stdev': statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0
            },
            'jitter': {
                'min': min(self.jitters) if self.jitters else 0,
                'max': max(self.jitters) if self.jitters else 0,
                'avg': statistics.mean(self.jitters) if self.jitters else 0,
                'median': statistics.median(self.jitters) if self.jitters else 0,
                'stdev': statistics.stdev(self.jitters) if len(self.jitters) > 1 else 0
            }
        }
    
    def stop(self):
        """Stop the VoIP server and close socket."""
        self.running = False
        if self.socket:
            self.socket.close()


class VoIPClient:
    """
    VoIP traffic generator.
    
    Generates simulated VoIP traffic matching G.711 codec characteristics:
    - 64 kbps constant bitrate
    - 160 byte packets (20ms of audio)
    - 50 packets per second (one every 20ms)
    
    Each packet includes sequence number and timestamp for latency calculation.
    """
    
    def __init__(self, server_ip, server_port=TestConfig.PORT_VOIP, 
                 source_ip=None, verbose=False):
        """
        Initialize VoIP client.
        
        Args:
            server_ip: Destination IP address
            server_port: Destination port
            source_ip: Source IP to bind to (optional)
            verbose: Enable detailed logging
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.source_ip = source_ip
        self.verbose = verbose
        self.socket = None
        self.running = False
        self.packets_sent = 0
        
        # VoIP packet parameters (G.711 codec)
        self.packet_size = TestConfig.VOIP_PACKET_SIZE
        self.packet_rate = TestConfig.VOIP_PACKET_RATE
        self.interval = 1.0 / self.packet_rate  # Time between packets (20ms)
    
    def start(self, duration):
        """
        Generate VoIP traffic for specified duration.
        
        Uses precise timing to maintain constant packet rate.
        Each packet is sent at exact intervals to simulate real VoIP traffic.
        
        Args:
            duration: Test duration in seconds
        """
        # Create UDP socket for sending
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Bind to specific source IP if specified
        if self.source_ip:
            self.socket.bind((self.source_ip, 0))
        
        self.running = True
        
        if self.verbose:
            print(f"VoIP Client sending to {self.server_ip}:{self.server_port}")
        
        # Calculate precise send times
        start_time = time.time()
        next_send_time = start_time
        
        try:
            while self.running and (time.time() - start_time) < duration:
                current_time = time.time()
                
                # Send packet if it's time
                if current_time >= next_send_time:
                    self.send_packet()
                    next_send_time += self.interval
                
                # Sleep until next packet time (precise timing)
                sleep_time = next_send_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def send_packet(self):
        """
        Send a single VoIP packet with sequence number and timestamp.
        
        Packet structure:
        - 4 bytes: sequence number
        - 8 bytes: timestamp
        - remaining bytes: payload (to reach packet_size)
        """
        try:
            # Create packet header
            timestamp = time.time()
            header = struct.pack('!I', self.packets_sent)  # Sequence number
            header += struct.pack('!d', timestamp)          # Timestamp
            
            # Add payload to reach desired packet size
            payload_size = self.packet_size - len(header)
            payload = b'V' * payload_size  # 'V' for Voice
            
            packet = header + payload
            
            # Send packet
            self.socket.sendto(packet, (self.server_ip, self.server_port))
            self.packets_sent += 1
        
        except Exception as e:
            if self.verbose:
                print(f"Send error: {e}")
    
    def stop(self):
        """Stop the VoIP client and close socket."""
        self.running = False
        if self.socket:
            self.socket.close()


class CongestionGenerator:
    """
    Network congestion generator for testing QoS under load.
    
    Generates high-rate UDP traffic to create network congestion.
    Used to verify that high-priority traffic (VoIP) is protected
    when competing with lower-priority traffic.
    """
    
    def __init__(self, target_ip, target_port, source_ip=None, 
                 rate_mbps=TestConfig.CONGESTION_RATE_MBPS, verbose=False):
        """
        Initialize congestion generator.
        
        Args:
            target_ip: Where to send congestion traffic
            target_port: Destination port
            source_ip: Source IP to bind to
            rate_mbps: Target rate in Mbps
            verbose: Enable detailed logging
        """
        self.target_ip = target_ip
        self.target_port = target_port
        self.source_ip = source_ip
        self.rate_mbps = rate_mbps
        self.verbose = verbose
        self.socket = None
        self.running = False
        self.bytes_sent = 0
    
    def start(self, duration):
        """
        Generate congestion traffic for specified duration.
        
        Calculates packet rate needed to achieve target Mbps,
        then sends packets at that rate.
        
        Args:
            duration: Test duration in seconds
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        if self.source_ip:
            self.socket.bind((self.source_ip, 0))
        
        self.running = True
        
        # Calculate required packets per second to achieve target rate
        # rate_mbps Mbps = rate_mbps * 1,000,000 bits/sec = rate_mbps * 125,000 bytes/sec
        packet_size = 1400  # MTU-sized packets
        target_bytes_per_sec = (self.rate_mbps * 1_000_000) / 8
        packets_per_sec = target_bytes_per_sec / packet_size
        interval = 1.0 / packets_per_sec
        
        if self.verbose:
            print(f"Congestion: Generating {self.rate_mbps} Mbps to {self.target_ip}")
        
        # Create packet payload once (reuse for efficiency)
        packet = b'C' * packet_size  # 'C' for Congestion
        
        start_time = time.time()
        next_send_time = start_time
        
        try:
            while self.running and (time.time() - start_time) < duration:
                current_time = time.time()
                
                if current_time >= next_send_time:
                    self.socket.sendto(packet, (self.target_ip, self.target_port))
                    self.bytes_sent += packet_size
                    next_send_time += interval
                
                sleep_time = next_send_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def stop(self):
        """Stop congestion generator."""
        self.running = False
        if self.socket:
            self.socket.close()


# =============================================================================
# SCENARIO 2: VIDEO STREAMING
# =============================================================================

class VideoStreamServer:
    """
    Video streaming receiver and analyzer.
    
    Simulates a video player that:
    - Receives video packets at varying rates
    - Maintains a playback buffer
    - Detects buffering events (buffer underrun)
    - Calculates quality metrics
    """
    
    def __init__(self, host='0.0.0.0', port=TestConfig.PORT_VIDEO, verbose=False):
        """
        Initialize video server.
        
        Args:
            host: IP to bind to
            port: Port to listen on
            verbose: Enable detailed logging
        """
        self.host = host
        self.port = port
        self.verbose = verbose
        self.socket = None
        self.running = False
        
        # Statistics
        self.packets_received = 0
        self.bytes_received = 0
        self.start_time = None
        self.throughputs = deque(maxlen=1000)  # Rolling window of throughput samples
        
        # Video buffer simulation
        # The buffer represents seconds of video content available for playback
        self.buffer_level = 0  # Current buffer level in seconds
        self.buffer_max = TestConfig.VIDEO_BUFFER_MAX
        self.playback_rate = 1.0  # Playback consumes 1 second of buffer per second
        self.buffering_events = 0  # Count of buffer underruns
        self.last_packet_time = None
    
    def start(self):
        """Start video server and receive packets."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, TestConfig.SOCKET_BUFFER_SIZE)
        self.socket.bind((self.host, self.port))
        self.running = True
        self.start_time = time.time()
        
        if self.verbose:
            print(f"Video Server listening on {self.host}:{self.port}")
        
        self.receive_loop()
    
    def receive_loop(self):
        """Main receive loop with throughput calculation."""
        self.socket.settimeout(1.0)
        
        last_throughput_calc = time.time()
        bytes_in_interval = 0
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65536)  # Large buffer for video packets
                arrival_time = time.time()
                
                self.process_packet(data, arrival_time)
                
                # Calculate throughput every second
                bytes_in_interval += len(data)
                if arrival_time - last_throughput_calc >= 1.0:
                    # Convert to Mbps
                    throughput_mbps = (bytes_in_interval * 8) / (1_000_000 * (arrival_time - last_throughput_calc))
                    self.throughputs.append(throughput_mbps)
                    bytes_in_interval = 0
                    last_throughput_calc = arrival_time
                    
                    if self.verbose and self.packets_received % 100 == 0:
                        print(f"Video: {self.packets_received} packets, {throughput_mbps:.2f} Mbps, buffer {self.buffer_level:.1f}s")
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Video Server error: {e}")
    
    def process_packet(self, data, arrival_time):
        """
        Process video packet and update buffer simulation.
        
        Video packet format:
        - 4 bytes: sequence number
        - 8 bytes: timestamp
        - 4 bytes: bitrate (kbps)
        - 4 bytes: frame duration (seconds)
        - remaining: video payload
        
        Args:
            data: Packet bytes
            arrival_time: Reception time
        """
        try:
            if len(data) < 20:
                return
            
            # Extract packet fields
            seq_num = struct.unpack('!I', data[0:4])[0]
            timestamp = struct.unpack('!d', data[4:12])[0]
            bitrate = struct.unpack('!I', data[12:16])[0]
            frame_duration = struct.unpack('!f', data[16:20])[0]
            
            self.packets_received += 1
            self.bytes_received += len(data)
            
            # Update buffer: add content from this packet
            self.buffer_level += frame_duration
            
            # Simulate playback consumption
            if self.last_packet_time:
                time_elapsed = arrival_time - self.last_packet_time
                self.buffer_level -= time_elapsed * self.playback_rate
                
                # Detect buffering (buffer underrun)
                if self.buffer_level <= 0:
                    self.buffering_events += 1
                    self.buffer_level = 0  # Can't go negative
            
            # Cap buffer at maximum
            self.buffer_level = min(self.buffer_level, self.buffer_max)
            
            self.last_packet_time = arrival_time
        
        except Exception as e:
            if self.verbose:
                print(f"Video packet processing error: {e}")
    
    def get_statistics(self):
        """
        Calculate video streaming statistics including quality score.
        
        Quality score (0-100) penalizes:
        - Buffering events (each -10 points, max -50)
        - Throughput variability (high stdev = quality degradation)
        
        Returns:
            dict: Comprehensive video statistics
            None: If no data collected
        """
        if not self.throughputs or self.packets_received == 0:
            return None
        
        elapsed = time.time() - self.start_time
        avg_throughput = statistics.mean(self.throughputs)
        
        # Calculate quality score (0-100)
        # Start at 100, deduct points for issues
        quality_score = 100.0
        
        # Penalize buffering events (each event = -10 points, max -50)
        if self.buffering_events > 0:
            quality_score -= min(50, self.buffering_events * 10)
        
        # Penalize throughput variability (high stdev = unstable)
        if len(self.throughputs) > 1:
            throughput_stdev = statistics.stdev(self.throughputs)
            if throughput_stdev > 1.0:
                quality_score -= min(20, throughput_stdev * 5)
        
        quality_score = max(0, quality_score)  # Ensure non-negative
        
        return {
            'packets_received': self.packets_received,
            'bytes_received': self.bytes_received,
            'duration': elapsed,
            'throughput': {
                'min': min(self.throughputs),
                'max': max(self.throughputs),
                'avg': avg_throughput,
                'median': statistics.median(self.throughputs),
                'stdev': statistics.stdev(self.throughputs) if len(self.throughputs) > 1 else 0
            },
            'buffering': {
                'events': self.buffering_events,
                'final_buffer_level': self.buffer_level
            },
            'quality_score': quality_score
        }
    
    def stop(self):
        """Stop video server."""
        self.running = False
        if self.socket:
            self.socket.close()


class VideoStreamClient:
    """
    Video streaming traffic generator.
    
    Simulates video streaming by sending packets at frame rate (30 fps)
    with payload sizes calculated to match target bitrate.
    """
    
    def __init__(self, server_ip, server_port=TestConfig.PORT_VIDEO, 
                 source_ip=None, bitrate_kbps=1000, verbose=False):
        """
        Initialize video client.
        
        Args:
            server_ip: Destination IP
            server_port: Destination port
            source_ip: Source IP to bind to
            bitrate_kbps: Target video bitrate in kbps
            verbose: Enable logging
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.source_ip = source_ip
        self.bitrate_kbps = bitrate_kbps
        self.verbose = verbose
        self.socket = None
        self.running = False
        self.packets_sent = 0
        
        # Video parameters
        self.fps = TestConfig.VIDEO_FPS
        self.frame_duration = 1.0 / self.fps
        
        # Calculate bytes per frame to achieve target bitrate
        # bitrate_kbps * 1000 bits/sec / 8 = bytes/sec
        # bytes/sec / fps = bytes per frame
        self.bytes_per_frame = (bitrate_kbps * 1000 / 8) / self.fps
        self.max_packet_size = 1400  # MTU
    
    def start(self, duration):
        """
        Generate video streaming traffic.
        
        Each frame may be split into multiple packets if it exceeds MTU.
        
        Args:
            duration: Test duration in seconds
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        if self.source_ip:
            self.socket.bind((self.source_ip, 0))
        
        self.running = True
        
        if self.verbose:
            print(f"Video Client: {self.bitrate_kbps} kbps to {self.server_ip}:{self.server_port}")
        
        start_time = time.time()
        next_frame_time = start_time
        frame_num = 0
        
        try:
            while self.running and (time.time() - start_time) < duration:
                current_time = time.time()
                
                if current_time >= next_frame_time:
                    self.send_frame(frame_num)
                    frame_num += 1
                    next_frame_time += self.frame_duration
                
                sleep_time = next_frame_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def send_frame(self, frame_num):
        """
        Send video frame, potentially fragmented into multiple packets.
        
        Args:
            frame_num: Frame number for sequencing
        """
        try:
            bytes_to_send = int(self.bytes_per_frame)
            bytes_sent = 0
            
            # Fragment frame into multiple packets if needed
            while bytes_sent < bytes_to_send:
                packet_data_size = min(self.max_packet_size - 20, bytes_to_send - bytes_sent)
                
                # Create packet header
                timestamp = time.time()
                header = struct.pack('!I', self.packets_sent)
                header += struct.pack('!d', timestamp)
                header += struct.pack('!I', self.bitrate_kbps)
                header += struct.pack('!f', self.frame_duration)
                
                # Add payload
                payload = b'V' * packet_data_size
                packet = header + payload
                
                self.socket.sendto(packet, (self.server_ip, self.server_port))
                self.packets_sent += 1
                bytes_sent += packet_data_size
        
        except Exception as e:
            if self.verbose:
                print(f"Video send error: {e}")
    
    def stop(self):
        """Stop video client."""
        self.running = False
        if self.socket:
            self.socket.close()


# =============================================================================
# SCENARIO 3: BEST-EFFORT TRAFFIC
# =============================================================================

class BestEffortServer:
    """
    Best-effort (background data) traffic receiver.
    
    Measures throughput and latency for low-priority data traffic.
    Used to establish baseline performance and compare with
    performance when competing with higher-priority traffic.
    """
    
    def __init__(self, host='0.0.0.0', port=TestConfig.PORT_DATA, verbose=False):
        """
        Initialize best-effort server.
        
        Args:
            host: IP to bind to
            port: Port to listen on
            verbose: Enable logging
        """
        self.host = host
        self.port = port
        self.verbose = verbose
        self.socket = None
        self.running = False
        
        # Statistics
        self.packets_received = 0
        self.bytes_received = 0
        self.start_time = None
        self.throughputs = deque(maxlen=1000)
        self.latencies = []
    
    def start(self):
        """Start best-effort server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, TestConfig.SOCKET_BUFFER_SIZE)
        self.socket.bind((self.host, self.port))
        self.running = True
        self.start_time = time.time()
        
        if self.verbose:
            print(f"Best-Effort Server listening on {self.host}:{self.port}")
        
        self.receive_loop()
    
    def receive_loop(self):
        """Receive packets and calculate metrics."""
        self.socket.settimeout(1.0)
        
        last_throughput_calc = time.time()
        bytes_in_interval = 0
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65536)
                arrival_time = time.time()
                
                self.process_packet(data, arrival_time)
                
                # Throughput calculation
                bytes_in_interval += len(data)
                if arrival_time - last_throughput_calc >= 1.0:
                    throughput_mbps = (bytes_in_interval * 8) / (1_000_000 * (arrival_time - last_throughput_calc))
                    self.throughputs.append(throughput_mbps)
                    bytes_in_interval = 0
                    last_throughput_calc = arrival_time
                    
                    if self.verbose and self.packets_received % 1000 == 0:
                        print(f"Data: {self.packets_received} packets, {throughput_mbps:.2f} Mbps")
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Best-Effort Server error: {e}")
    
    def process_packet(self, data, arrival_time):
        """Process data packet and calculate latency."""
        try:
            if len(data) < 12:
                return
            
            seq_num = struct.unpack('!I', data[0:4])[0]
            timestamp = struct.unpack('!d', data[4:12])[0]
            
            self.packets_received += 1
            self.bytes_received += len(data)
            
            # Calculate latency
            latency = (arrival_time - timestamp) * 1000  # ms
            self.latencies.append(latency)
        
        except Exception as e:
            if self.verbose:
                print(f"Data packet error: {e}")
    
    def get_statistics(self):
        """Get best-effort traffic statistics."""
        if not self.throughputs or not self.latencies:
            return None
        
        elapsed = time.time() - self.start_time
        
        return {
            'packets_received': self.packets_received,
            'bytes_received': self.bytes_received,
            'duration': elapsed,
            'throughput': {
                'min': min(self.throughputs),
                'max': max(self.throughputs),
                'avg': statistics.mean(self.throughputs),
                'median': statistics.median(self.throughputs),
                'stdev': statistics.stdev(self.throughputs) if len(self.throughputs) > 1 else 0
            },
            'latency': {
                'min': min(self.latencies),
                'max': max(self.latencies),
                'avg': statistics.mean(self.latencies),
                'median': statistics.median(self.latencies),
                'stdev': statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0
            }
        }
    
    def stop(self):
        """Stop best-effort server."""
        self.running = False
        if self.socket:
            self.socket.close()


class BestEffortClient:
    """
    Best-effort traffic generator.
    
    Generates bulk UDP data at specified rate to simulate
    background data transfer (web browsing, file download, etc).
    """
    
    def __init__(self, server_ip, server_port=TestConfig.PORT_DATA,
                 source_ip=None, rate_mbps=TestConfig.DATA_RATE_MBPS, verbose=False):
        """
        Initialize best-effort client.
        
        Args:
            server_ip: Destination IP
            server_port: Destination port
            source_ip: Source IP to bind to
            rate_mbps: Target rate in Mbps
            verbose: Enable logging
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.source_ip = source_ip
        self.rate_mbps = rate_mbps
        self.verbose = verbose
        self.socket = None
        self.running = False
        self.packets_sent = 0
        
        # Calculate packet rate to achieve target Mbps
        self.packet_size = TestConfig.DATA_PACKET_SIZE
        self.target_bytes_per_sec = (rate_mbps * 1_000_000) / 8
        self.packets_per_sec = self.target_bytes_per_sec / self.packet_size
        self.interval = 1.0 / self.packets_per_sec
    
    def start(self, duration):
        """Generate best-effort traffic."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, TestConfig.SOCKET_BUFFER_SIZE)
        
        if self.source_ip:
            self.socket.bind((self.source_ip, 0))
        
        self.running = True
        
        if self.verbose:
            print(f"Best-Effort Client: {self.rate_mbps} Mbps to {self.server_ip}:{self.server_port}")
        
        start_time = time.time()
        next_send_time = start_time
        
        try:
            while self.running and (time.time() - start_time) < duration:
                current_time = time.time()
                
                if current_time >= next_send_time:
                    self.send_packet()
                    next_send_time += self.interval
                
                sleep_time = next_send_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def send_packet(self):
        """Send data packet with timestamp."""
        try:
            timestamp = time.time()
            header = struct.pack('!I', self.packets_sent)
            header += struct.pack('!d', timestamp)
            
            payload_size = self.packet_size - len(header)
            payload = b'D' * payload_size  # 'D' for Data
            
            packet = header + payload
            self.socket.sendto(packet, (self.server_ip, self.server_port))
            self.packets_sent += 1
        
        except Exception as e:
            if self.verbose:
                print(f"Data send error: {e}")
    
    def stop(self):
        """Stop best-effort client."""
        self.running = False
        if self.socket:
            self.socket.close()


# =============================================================================
# SCENARIO 4: MIXED TRAFFIC
# =============================================================================

class MixedTrafficMonitor:
    """
    Traffic monitor for mixed traffic scenario.
    
    Each monitor receives one type of traffic (VoIP, Video, or Data)
    and calculates appropriate metrics for that traffic type.
    Used in Scenario 4 to measure all three services simultaneously.
    """
    
    def __init__(self, name, port, traffic_type, verbose=False):
        """
        Initialize traffic monitor.
        
        Args:
            name: Monitor name for identification
            port: Port to listen on
            traffic_type: 'voip', 'video', or 'data'
            verbose: Enable logging
        """
        self.name = name
        self.port = port
        self.traffic_type = traffic_type
        self.verbose = verbose
        self.socket = None
        self.running = False
        
        # Common statistics
        self.packets_received = 0
        self.bytes_received = 0
        self.start_time = None
        self.latencies = []
        self.throughputs = deque(maxlen=100)
        
        # VoIP-specific
        if traffic_type == 'voip':
            self.jitters = []
            self.last_latency = None
        
        # Video-specific
        if traffic_type == 'video':
            self.buffer_level = 0
            self.buffer_max = 10
            self.buffering_events = 0
            self.last_packet_time = None
    
    def start(self, host='0.0.0.0'):
        """Start the monitor."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, TestConfig.SOCKET_BUFFER_SIZE)
        self.socket.bind((host, self.port))
        self.running = True
        self.start_time = time.time()
        
        if self.verbose:
            print(f"Monitor {self.name} listening on port {self.port}")
        
        self.receive_loop()
    
    def receive_loop(self):
        """Main receive loop."""
        self.socket.settimeout(1.0)
        
        last_throughput_calc = time.time()
        bytes_in_interval = 0
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65536)
                arrival_time = time.time()
                
                self.process_packet(data, arrival_time)
                
                # Throughput calculation
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
    
    def process_packet(self, data, arrival_time):
        """Process packet based on traffic type."""
        try:
            if len(data) < 12:
                return
            
            seq_num = struct.unpack('!I', data[0:4])[0]
            timestamp = struct.unpack('!d', data[4:12])[0]
            
            self.packets_received += 1
            self.bytes_received += len(data)
            
            # Calculate latency
            latency = (arrival_time - timestamp) * 1000
            self.latencies.append(latency)
            
            # VoIP-specific: calculate jitter
            if self.traffic_type == 'voip':
                if self.last_latency is not None:
                    jitter = abs(latency - self.last_latency)
                    self.jitters.append(jitter)
                self.last_latency = latency
            
            # Video-specific: update buffer
            elif self.traffic_type == 'video' and len(data) >= 20:
                frame_duration = struct.unpack('!f', data[16:20])[0]
                self.buffer_level += frame_duration
                
                if self.last_packet_time:
                    time_elapsed = arrival_time - self.last_packet_time
                    self.buffer_level -= time_elapsed
                    
                    if self.buffer_level <= 0:
                        self.buffering_events += 1
                        self.buffer_level = 0
                
                self.buffer_level = min(self.buffer_level, self.buffer_max)
                self.last_packet_time = arrival_time
        
        except Exception as e:
            pass
    
    def get_statistics(self):
        """Get statistics for this traffic type."""
        if not self.latencies:
            return None
        
        elapsed = time.time() - self.start_time
        
        stats = {
            'name': self.name,
            'type': self.traffic_type,
            'packets_received': self.packets_received,
            'bytes_received': self.bytes_received,
            'duration': elapsed,
            'throughput': {
                'avg': statistics.mean(self.throughputs) if self.throughputs else 0,
                'min': min(self.throughputs) if self.throughputs else 0,
                'max': max(self.throughputs) if self.throughputs else 0
            },
            'latency': {
                'avg': statistics.mean(self.latencies),
                'min': min(self.latencies),
                'max': max(self.latencies),
                'stdev': statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0
            }
        }
        
        # Add VoIP-specific metrics
        if self.traffic_type == 'voip' and self.jitters:
            stats['jitter'] = {
                'avg': statistics.mean(self.jitters),
                'min': min(self.jitters),
                'max': max(self.jitters)
            }
        
        # Add Video-specific metrics
        if self.traffic_type == 'video':
            stats['buffering_events'] = self.buffering_events
        
        return stats
    
    def stop(self):
        """Stop the monitor."""
        self.running = False
        if self.socket:
            self.socket.close()


class MixedTrafficGenerator:
    """
    Traffic generator for mixed traffic scenario.
    
    Generates one type of traffic (VoIP, Video, or Data) with
    characteristics appropriate for that traffic type.
    """
    
    def __init__(self, traffic_type, dest_ip, dest_port, source_ip=None, verbose=False):
        """
        Initialize mixed traffic generator.
        
        Args:
            traffic_type: 'voip', 'video', or 'data'
            dest_ip: Destination IP
            dest_port: Destination port
            source_ip: Source IP to bind to
            verbose: Enable logging
        """
        self.traffic_type = traffic_type
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.source_ip = source_ip
        self.verbose = verbose
        self.socket = None
        self.running = False
        self.packets_sent = 0
        
        # Configure based on traffic type
        if traffic_type == 'voip':
            self.packet_size = TestConfig.VOIP_PACKET_SIZE
            self.rate = TestConfig.VOIP_PACKET_RATE  # pps
        elif traffic_type == 'video':
            self.packet_size = 1400
            self.rate = TestConfig.VIDEO_FPS  # fps
            self.bitrate_kbps = 2000  # 2 Mbps video
        elif traffic_type == 'data':
            self.packet_size = TestConfig.DATA_PACKET_SIZE
            rate_mbps = TestConfig.DATA_RATE_MBPS
            self.rate = (rate_mbps * 1_000_000 / 8) / self.packet_size  # pps
        
        self.interval = 1.0 / self.rate
    
    def start(self, duration):
        """Generate traffic for specified duration."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, TestConfig.SOCKET_BUFFER_SIZE)
        
        if self.source_ip:
            self.socket.bind((self.source_ip, 0))
        
        self.running = True
        start_time = time.time()
        next_send_time = start_time
        
        try:
            while self.running and (time.time() - start_time) < duration:
                current_time = time.time()
                
                if current_time >= next_send_time:
                    self.send_packet()
                    next_send_time += self.interval
                
                sleep_time = next_send_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def send_packet(self):
        """Send packet appropriate for traffic type."""
        try:
            timestamp = time.time()
            header = struct.pack('!I', self.packets_sent)
            header += struct.pack('!d', timestamp)
            
            # Video-specific header fields
            if self.traffic_type == 'video':
                header += struct.pack('!I', self.bitrate_kbps)
                header += struct.pack('!f', 1.0 / self.rate)  # frame duration
            
            payload_size = self.packet_size - len(header)
            payload = bytes([ord(self.traffic_type[0].upper())]) * payload_size
            
            packet = header + payload
            self.socket.sendto(packet, (self.dest_ip, self.dest_port))
            self.packets_sent += 1
        
        except Exception as e:
            pass
    
    def stop(self):
        """Stop generator."""
        self.running = False
        if self.socket:
            self.socket.close()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def print_voip_results(stats_normal, stats_congested):
    """
    Print VoIP test results comparing normal and congested conditions.
    
    Args:
        stats_normal: Statistics from normal test
        stats_congested: Statistics from congested test
    """
    print("\n" + "="*70)
    print("VOIP TEST RESULTS")
    print("="*70)
    
    if stats_normal:
        print("\nNormal Conditions:")
        print(f"  Latency:  {stats_normal['latency']['avg']:.2f}ms "
              f"(min: {stats_normal['latency']['min']:.2f}, max: {stats_normal['latency']['max']:.2f})")
        print(f"  Jitter:   {stats_normal['jitter']['avg']:.2f}ms")
        print(f"  Loss:     {stats_normal['packet_loss_percent']:.2f}%")
    
    if stats_congested:
        print("\nCongested Conditions:")
        print(f"  Latency:  {stats_congested['latency']['avg']:.2f}ms "
              f"(min: {stats_congested['latency']['min']:.2f}, max: {stats_congested['latency']['max']:.2f})")
        print(f"  Jitter:   {stats_congested['jitter']['avg']:.2f}ms")
        print(f"  Loss:     {stats_congested['packet_loss_percent']:.2f}%")
    
    if stats_normal and stats_congested:
        lat_increase = ((stats_congested['latency']['avg'] - stats_normal['latency']['avg']) / 
                       stats_normal['latency']['avg']) * 100
        print(f"\nImpact of Congestion:")
        print(f"  Latency increase: {lat_increase:+.1f}%")
        
        if abs(lat_increase) < 50 and stats_congested['packet_loss_percent'] < 1:
            print("  QoS Status: PROTECTED - VoIP traffic maintained quality under congestion")
        else:
            print("  QoS Status: DEGRADED - VoIP traffic affected by congestion")
    
    print("="*70)


def print_video_results(results_by_bitrate):
    """
    Print video streaming results for all tested bitrates.
    
    Args:
        results_by_bitrate: Dictionary mapping bitrate to statistics
    """
    print("\n" + "="*70)
    print("VIDEO STREAMING TEST RESULTS")
    print("="*70)
    
    print(f"\n{'Bitrate':<12} {'Throughput':<15} {'Buffering':<12} {'Quality':<10}")
    print("-"*70)
    
    for bitrate, stats in sorted(results_by_bitrate.items()):
        if stats:
            throughput = stats['throughput']['avg']
            buffering = stats['buffering']['events']
            quality = stats['quality_score']
            
            print(f"{bitrate:>4} kbps    {throughput:>6.2f} Mbps      "
                  f"{buffering:>2} events     {quality:>5.1f}/100")
    
    print("="*70)


def print_mixed_results(voip_stats, video_stats, data_stats):
    """
    Print mixed traffic test results showing QoS prioritization.
    
    This is the most important test result as it demonstrates that
    QoS prioritization works correctly when all services compete
    for network resources.
    
    Args:
        voip_stats: VoIP monitor statistics
        video_stats: Video monitor statistics
        data_stats: Data monitor statistics
    """
    print("\n" + "="*70)
    print("MIXED TRAFFIC TEST RESULTS - QoS Prioritization Validation")
    print("="*70)
    
    print(f"\n{'Service':<12} {'Priority':<10} {'Throughput':<15} {'Latency':<12} {'Status':<12}")
    print("-"*70)
    
    # VoIP results
    if voip_stats:
        lat = voip_stats['latency']['avg']
        thr = voip_stats['throughput']['avg']
        status = "PROTECTED" if lat < 50 else "DEGRADED"
        print(f"{'VoIP':<12} {'20 (High)':<10} {thr:>6.3f} Mbps     {lat:>6.2f}ms    {status:<12}")
    
    # Video results
    if video_stats:
        thr = video_stats['throughput']['avg']
        lat = video_stats['latency']['avg']
        buffering = video_stats.get('buffering_events', 0)
        status = "FLUIDE" if buffering < 3 else "BUFFERING"
        print(f"{'Video':<12} {'80 (Med)':<10} {thr:>6.2f} Mbps     {lat:>6.2f}ms    {status:<12}")
    
    # Data results
    if data_stats:
        thr = data_stats['throughput']['avg']
        lat = data_stats['latency']['avg']
        status = "LIMITED" if thr < 5 else "OK"
        print(f"{'Data':<12} {'90 (Low)':<10} {thr:>6.2f} Mbps     {lat:>6.2f}ms    {status:<12}")
    
    # QoS validation
    print("\nQoS Hierarchy Validation:")
    
    if voip_stats and voip_stats['latency']['avg'] < 50:
        print("  [PASS] VoIP latency < 50ms - High priority traffic protected")
    else:
        print("  [FAIL] VoIP latency >= 50ms - High priority traffic degraded")
    
    if video_stats and data_stats:
        video_thr = video_stats['throughput']['avg']
        data_thr = data_stats['throughput']['avg']
        
        if video_thr > data_thr:
            ratio = video_thr / data_thr if data_thr > 0 else float('inf')
            print(f"  [PASS] Video throughput > Data throughput (ratio {ratio:.1f}:1)")
            print("         Medium priority > Low priority as expected")
        else:
            print("  [FAIL] Data throughput >= Video throughput")
            print("         QoS prioritization not functioning correctly")
    
    print("="*70)


def save_results(data, filename):
    """
    Save test results to JSON file.
    
    Args:
        data: Dictionary of test results
        filename: Output filename
    """
    result = {
        'timestamp': datetime.now().isoformat(),
        'data': data
    }
    
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to {filename}")


# =============================================================================
# TEST EXECUTION FUNCTIONS
# =============================================================================

def run_voip_test(verbose=False):
    """
    Execute VoIP test scenario (Scenario 1).
    
    Tests VoIP traffic under two conditions:
    1. Normal - VoIP traffic alone
    2. Congested - VoIP traffic competing with 100 Mbps congestion
    
    This demonstrates QoS protection for high-priority traffic.
    
    Args:
        verbose: Enable detailed logging
    
    Returns:
        tuple: (normal_stats, congested_stats)
    """
    print("\n" + "="*70)
    print("SCENARIO 1: VoIP Traffic Test")
    print("Testing real-time traffic protection under congestion")
    print("="*70)
    
    # Test 1: Normal conditions (VoIP only)
    print("\nTest 1/2: Normal conditions (30s)")
    
    server = VoIPServer(host=TestConfig.UE_VIDEO_IP, port=TestConfig.PORT_VOIP, verbose=verbose)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)
    
    client = VoIPClient(server_ip=TestConfig.UE_VIDEO_IP, source_ip=TestConfig.UE_VOIP_IP, verbose=verbose)
    client.start(duration=TestConfig.VOIP_TEST_DURATION)
    time.sleep(2)
    
    stats_normal = server.get_statistics()
    server.stop()
    
    print("Test 1 complete")
    
    # Test 2: Congested conditions (VoIP + 100 Mbps congestion)
    print("\nTest 2/2: Congested conditions (30s)")
    
    server = VoIPServer(host=TestConfig.UE_VIDEO_IP, port=TestConfig.PORT_VOIP, verbose=verbose)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)
    
    # Start congestion generator
    congestion = CongestionGenerator(target_ip=TestConfig.UE_VIDEO_IP, target_port=5061,
                                     source_ip=TestConfig.UE_WEB_IP, verbose=verbose)
    congestion_thread = threading.Thread(target=congestion.start, 
                                        args=(TestConfig.VOIP_TEST_DURATION,))
    congestion_thread.daemon = True
    congestion_thread.start()
    time.sleep(1)
    
    # Start VoIP client
    client = VoIPClient(server_ip=TestConfig.UE_VIDEO_IP, source_ip=TestConfig.UE_VOIP_IP, verbose=verbose)
    client.start(duration=TestConfig.VOIP_TEST_DURATION)
    time.sleep(2)
    
    stats_congested = server.get_statistics()
    server.stop()
    congestion.stop()
    
    print("Test 2 complete")
    
    # Display and save results
    print_voip_results(stats_normal, stats_congested)
    
    save_results({
        'normal': stats_normal,
        'congested': stats_congested
    }, 'voip_test_results.json')
    
    return stats_normal, stats_congested


def run_video_test(verbose=False):
    """
    Execute video streaming test scenario (Scenario 2).
    
    Tests video streaming at multiple bitrates:
    - 500 kbps (low quality)
    - 1000 kbps (medium quality)
    - 2000 kbps (high quality)
    - 5000 kbps (very high quality)
    
    Measures throughput, buffering, and calculates quality scores.
    
    Args:
        verbose: Enable detailed logging
    
    Returns:
        dict: Results for each bitrate tested
    """
    print("\n" + "="*70)
    print("SCENARIO 2: Video Streaming Test")
    print("Testing adaptive streaming with multiple bitrates")
    print("="*70)
    
    results = {}
    
    for i, bitrate in enumerate(TestConfig.VIDEO_BITRATES):
        print(f"\nTest {i+1}/{len(TestConfig.VIDEO_BITRATES)}: {bitrate} kbps (30s)")
        
        # Start server
        server = VideoStreamServer(host=TestConfig.UE_VOIP_IP, port=TestConfig.PORT_VIDEO, verbose=verbose)
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(2)
        
        # Start client
        client = VideoStreamClient(server_ip=TestConfig.UE_VOIP_IP, source_ip=TestConfig.UE_VIDEO_IP,
                                   bitrate_kbps=bitrate, verbose=verbose)
        client.start(duration=TestConfig.VIDEO_TEST_DURATION)
        time.sleep(2)
        
        # Get statistics
        stats = server.get_statistics()
        server.stop()
        
        results[bitrate] = stats
        
        if stats:
            print(f"  Throughput: {stats['throughput']['avg']:.2f} Mbps")
            print(f"  Buffering: {stats['buffering']['events']} events")
            print(f"  Quality: {stats['quality_score']:.1f}/100")
    
    # Display and save results
    print_video_results(results)
    save_results(results, 'video_test_results.json')
    
    return results


def run_besteffort_test(verbose=False):
    """
    Execute best-effort traffic test scenario (Scenario 3).
    
    Tests low-priority background data traffic without competition.
    Provides baseline performance for comparison with Scenario 4.
    
    Args:
        verbose: Enable detailed logging
    
    Returns:
        dict: Best-effort traffic statistics
    """
    print("\n" + "="*70)
    print("SCENARIO 3: Best-Effort Traffic Test")
    print("Testing low-priority background data traffic")
    print("="*70)
    
    print("\nTest: 10 Mbps data traffic (30s)")
    
    # Start server
    server = BestEffortServer(host=TestConfig.UE_VOIP_IP, port=TestConfig.PORT_DATA, verbose=verbose)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)
    
    # Start client
    client = BestEffortClient(server_ip=TestConfig.UE_VOIP_IP, source_ip=TestConfig.UE_WEB_IP, verbose=verbose)
    client.start(duration=TestConfig.DATA_TEST_DURATION)
    time.sleep(2)
    
    # Get statistics
    stats = server.get_statistics()
    server.stop()
    
    if stats:
        print(f"\nResults:")
        print(f"  Throughput: {stats['throughput']['avg']:.2f} Mbps")
        print(f"  Latency: {stats['latency']['avg']:.2f}ms")
        print(f"  Packets: {stats['packets_received']}")
    
    save_results(stats, 'besteffort_test_results.json')
    
    return stats


def run_mixed_traffic_test(verbose=False):
    """
    Execute mixed traffic test scenario (Scenario 4).
    
    THIS IS THE MOST IMPORTANT TEST.
    
    Runs VoIP, Video, and Data traffic simultaneously to validate
    that QoS prioritization works correctly:
    - VoIP (Priority 20) should be protected with low latency
    - Video (Priority 80) should get medium resources
    - Data (Priority 90) should be limited when competing
    
    This demonstrates the QoS hierarchy: 20 > 80 > 90
    
    Args:
        verbose: Enable detailed logging
    
    Returns:
        tuple: (voip_stats, video_stats, data_stats)
    """
    print("\n" + "="*70)
    print("SCENARIO 4: Mixed Traffic Test")
    print("CRITICAL TEST - Validates QoS prioritization")
    print("Running VoIP + Video + Data simultaneously")
    print("="*70)
    
    # Target IP where all traffic converges (creates competition)
    target_ip = TestConfig.UE_VIDEO_IP
    
    print("\nStarting traffic monitors...")
    
    # Create monitors for each traffic type
    voip_monitor = MixedTrafficMonitor("VoIP", TestConfig.PORT_VOIP, 'voip', verbose)
    video_monitor = MixedTrafficMonitor("Video", TestConfig.PORT_VIDEO, 'video', verbose)
    data_monitor = MixedTrafficMonitor("Data", TestConfig.PORT_DATA, 'data', verbose)
    
    # Start monitors in separate threads
    monitor_threads = []
    for monitor in [voip_monitor, video_monitor, data_monitor]:
        t = threading.Thread(target=monitor.start, args=(target_ip,))
        t.daemon = True
        t.start()
        monitor_threads.append(t)
        time.sleep(0.5)
    
    time.sleep(2)
    print("Monitors ready")
    
    print("\nStarting traffic generators...")
    
    # Create traffic generators
    voip_gen = MixedTrafficGenerator('voip', target_ip, TestConfig.PORT_VOIP, 
                                     TestConfig.UE_VOIP_IP, verbose)
    video_gen = MixedTrafficGenerator('video', target_ip, TestConfig.PORT_VIDEO,
                                      TestConfig.UE_VIDEO_IP, verbose)
    data_gen = MixedTrafficGenerator('data', target_ip, TestConfig.PORT_DATA,
                                     TestConfig.UE_WEB_IP, verbose)
    
    # Start generators in separate threads
    gen_threads = []
    for gen in [voip_gen, video_gen, data_gen]:
        t = threading.Thread(target=gen.start, args=(TestConfig.MIXED_TEST_DURATION,))
        t.daemon = True
        t.start()
        gen_threads.append(t)
        time.sleep(0.5)
    
    print(f"Traffic running for {TestConfig.MIXED_TEST_DURATION}s...")
    
    # Wait for generators to complete
    for t in gen_threads:
        t.join()
    
    time.sleep(2)
    
    # Stop monitors and collect statistics
    print("\nCollecting statistics...")
    voip_monitor.stop()
    video_monitor.stop()
    data_monitor.stop()
    
    voip_stats = voip_monitor.get_statistics()
    video_stats = video_monitor.get_statistics()
    data_stats = data_monitor.get_statistics()
    
    # Display and save results
    print_mixed_results(voip_stats, video_stats, data_stats)
    
    save_results({
        'voip': voip_stats,
        'video': video_stats,
        'data': data_stats
    }, 'mixed_traffic_test_results.json')
    
    return voip_stats, video_stats, data_stats


# =============================================================================
# MAIN PROGRAM
# =============================================================================

def main():
    """
    Main program entry point.
    
    Parses command-line arguments and executes requested test scenarios.
    """
    parser = argparse.ArgumentParser(
        description='Comprehensive 5G QoS Testing Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Scenarios:
  1. voip    - VoIP traffic under normal and congested conditions
  2. video   - Video streaming at multiple bitrates
  3. data    - Best-effort background data traffic
  4. mixed   - All traffic types simultaneously (CRITICAL TEST)
  all        - Run all test scenarios in sequence

UE IP Configuration (priority order):
  1. Environment variables: UE_VOIP_IP, UE_VIDEO_IP, UE_WEB_IP
  2. Config file: qos_config.json
  3. Auto-detect from network interfaces (uesimtun0/1/2)
  4. Defaults: 10.1.0.2, 10.2.0.2, 10.3.0.2

Examples:
  python3 qos_tests.py --scenario voip
  python3 qos_tests.py --scenario mixed --verbose
  python3 qos_tests.py --scenario all
  
  # Using environment variables:
  UE_VOIP_IP=10.1.0.2 UE_VIDEO_IP=10.2.0.2 UE_WEB_IP=10.3.0.2 python3 qos_tests.py
  
  # Using config file (create qos_config.json):
  echo '{"ue_voip_ip":"10.1.0.2","ue_video_ip":"10.2.0.2","ue_web_ip":"10.3.0.2"}' > qos_config.json
        """
    )
    
    parser.add_argument('--scenario', '-s', 
                       choices=['voip', 'video', 'data', 'mixed', 'all'],
                       default='all',
                       help='Test scenario to run (default: all)')
    
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Enable verbose output with detailed logging')
    
    args = parser.parse_args()
    
    print("="*70)
    print("5G QoS Testing Suite")
    print("Comprehensive validation of QoS differentiation")
    print("="*70)
    
    # Show how IPs were configured
    import os
    if os.getenv('UE_VOIP_IP'):
        print("\nIP Configuration: Environment Variables")
    elif load_config_from_file():
        print("\nIP Configuration: Config File (qos_config.json)")
    elif get_ue_ips_from_interfaces():
        print("\nIP Configuration: Auto-detected from interfaces")
        detected = get_ue_ips_from_interfaces()
        if detected and args.verbose:
            print("  Detected interfaces:")
            for iface, ip in detected.items():
                print(f"    {iface}: {ip}")
    else:
        print("\nIP Configuration: Default values")
    
    print(f"\nConfiguration:")
    print(f"  VoIP UE:  {TestConfig.UE_VOIP_IP} (Priority 20)")
    print(f"  Video UE: {TestConfig.UE_VIDEO_IP} (Priority 80)")
    print(f"  Data UE:  {TestConfig.UE_WEB_IP} (Priority 90)")
    print(f"  Verbose:  {args.verbose}")
    
    # Execute requested scenario(s)
    if args.scenario == 'voip' or args.scenario == 'all':
        run_voip_test(verbose=args.verbose)
    
    if args.scenario == 'video' or args.scenario == 'all':
        run_video_test(verbose=args.verbose)
    
    if args.scenario == 'data' or args.scenario == 'all':
        run_besteffort_test(verbose=args.verbose)
    
    if args.scenario == 'mixed' or args.scenario == 'all':
        run_mixed_traffic_test(verbose=args.verbose)
    
    print("\n" + "="*70)
    print("All requested tests completed")
    print("Results saved to JSON files")
    print("="*70)


if __name__ == "__main__":
    main()

