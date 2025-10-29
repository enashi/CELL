# 5G QoS Configuration and Service Differentiation Testing

## Project Overview
This project explores Quality of Service (QoS) mechanisms in 5G networks by configuring different QoS profiles and testing service differentiation for various application types. Students will learn how 5G networks prioritize traffic and ensure quality for different services.

## Objective
Configure and test QoS policies in a 5G network to demonstrate service differentiation:
* **Deploy 5G Network**: Set up OpenAirInterface 5G Core and UERANSIM for testing
* **Configure QoS Profiles**: Implement multiple 5QI (5G QoS Identifier) profiles for different service types:
  - 5QI 1: Conversational Voice (GBR - Guaranteed Bit Rate)
  - 5QI 5: IMS Signaling (Non-GBR)
  - 5QI 9: Video Streaming (Non-GBR)
  - 5QI 79: Low latency eMBB (Non-GBR)
  - Custom profiles as needed
* **Test Different Applications**: Simulate various application types and measure QoS parameters:
  - VoIP calls (latency, jitter, packet loss)
  - Video streaming (throughput, buffering)
  - Web browsing (page load times)
  - File downloads (throughput)
* **Network Congestion Testing**: Create congestion scenarios and verify QoS prioritization
* **Performance Analysis**: Compare performance metrics across different QoS classes

## Learning Outcomes
* Understand 5G QoS architecture (5QI, QFI, QoS Flows)
* Learn to configure QoS policies in 5G Core Network
* Gain experience with traffic generation and network testing tools
* Analyze the impact of QoS on different application types
* Document trade-offs between guaranteed and non-guaranteed bit rate services

## Tools & Software
* **Docker-Compose** or **Kubernetes**: Container orchestration
* **OpenAirInterface 5G Core Network**: AMF, SMF, UPF with QoS support
* **UERANSIM**: Multiple UE instances with different QoS requirements
* **iperf3**: Bandwidth testing
* **VoIP tools**: SIPp or similar for voice call simulation
* **Video streaming**: ffmpeg for video traffic generation
* **Wireshark/tcpdump**: Packet capture and analysis
* **Python**: For test automation and result analysis

## Project Tasks

### Phase 1: Infrastructure Setup (Week 1-2)
- [ ] Deploy OAI 5G Core Network with QoS support enabled
- [ ] Configure SMF with multiple QoS profiles
- [ ] Deploy UERANSIM with multiple UEs
- [ ] Verify basic connectivity and PDU session establishment
- [ ] Document network configuration

### Phase 2: QoS Profile Configuration (Week 2-3)
- [ ] Study 3GPP QoS specifications (TS 23.501)
- [ ] Configure QoS profiles in OAI SMF:
  - Define 5QI values
  - Set priority levels
  - Configure ARP (Allocation and Retention Priority)
  - Set bit rate parameters (GFBR, MFBR for GBR flows)
- [ ] Create multiple PDU sessions with different QoS
- [ ] Verify QoS flow establishment using logs/Wireshark

### Phase 3: Application Testing (Week 3-4)
- [ ] Test Scenario 1: VoIP Traffic
  - Generate VoIP-like traffic (small packets, constant rate)
  - Measure latency, jitter, packet loss
  - Test under normal and congested conditions
- [ ] Test Scenario 2: Video Streaming
  - Stream video traffic with varying bitrates
  - Measure throughput, buffering, quality degradation
  - Compare different 5QI profiles
- [ ] Test Scenario 3: Best-Effort Traffic
  - Generate background data traffic
  - Measure throughput and latency
  - Observe behavior when competing with prioritized traffic
- [ ] Test Scenario 4: Mixed Traffic
  - Run multiple applications simultaneously
  - Verify QoS prioritization works correctly
  - Measure impact on each service type

### Phase 4: Congestion Testing (Week 4-5)
- [ ] Create network congestion scenarios:
  - Limit UPF bandwidth
  - Generate high-volume background traffic
  - Oversubscribe network resources
- [ ] Verify QoS behavior under congestion:
  - High-priority traffic maintains QoS
  - Low-priority traffic degrades gracefully
  - GBR flows receive guaranteed resources
- [ ] Test admission control (reject new flows when resources exhausted)
- [ ] Document and analyze results

### Phase 5: Analysis and Documentation (Week 5-6)
- [ ] Analyze collected data:
  - Create graphs comparing QoS profiles
  - Calculate statistical metrics (mean, percentiles)
  - Identify QoS violations and root causes
- [ ] Write comprehensive report:
  - QoS configuration details
  - Test methodology
  - Results and analysis
  - Recommendations for QoS tuning
- [ ] Create presentation with demo
- [ ] Submit source code and configurations

## Expected Deliverables
1. **Deployed 5G Network**: OAI 5G Core with QoS-enabled configuration
2. **QoS Configuration Files**: Documented SMF and UPF configurations
3. **Test Scripts**: Automated scripts for running test scenarios
4. **Performance Data**: Raw data from all test scenarios
5. **Analysis Report**: 
   - QoS behavior analysis
   - Performance comparisons
   - Graphs and visualizations
6. **Technical Documentation**:
   - Setup guide
   - QoS configuration guide
   - Test procedure documentation
7. **Source Code**: All scripts and configuration files
8. **Final Presentation**: Demo and findings

## Test Scenarios Summary

| Scenario | Service Type | 5QI | Traffic Pattern | Key Metrics |
|----------|-------------|-----|-----------------|-------------|
| 1 | VoIP | 1 | Small packets, 50pps | Latency, jitter, loss |
| 2 | Video HD | 9 | Variable rate, 5Mbps avg | Throughput, buffering |
| 3 | Web Browsing | 79 | Bursty, HTTP requests | Page load time, latency |
| 4 | File Download | 9 | Bulk transfer, 10Mbps+ | Throughput, completion time |
| 5 | Background | 9 | High volume | Throughput when deprioritized |

## Prerequisites
* Basic understanding of computer networks
* Familiarity with Linux command line
* Basic knowledge of Docker/Docker-Compose
* Understanding of QoS concepts (helpful but not required)

## Difficulty Level
⭐⭐☆☆☆ (Beginner to Intermediate)

This project is suitable for students who want to understand 5G QoS mechanisms without requiring deep protocol modifications or machine learning expertise. Focus is on configuration, testing, and analysis.

## References
* [3GPP TS 23.501 - 5G System Architecture](https://www.3gpp.org/DynaReport/23501.htm)
* [3GPP TS 23.503 - Policy and Charging Control](https://www.3gpp.org/DynaReport/23503.htm)
* [OpenAirInterface Documentation](https://gitlab.eurecom.fr/oai/cn5g)
* [UERANSIM Configuration Guide](https://github.com/aligungr/UERANSIM/wiki)
* [5G QoS Explained](https://www.3gpp.org/technologies/keywords-acronyms/5g-qos-flow)

## Bonus Challenges (Optional)
* Implement custom 5QI profiles for emerging applications (AR/VR, IoT)
* Test QoS with network slicing (separate slices for different service types)
* Implement dynamic QoS modification based on network conditions
* Create a visualization dashboard for real-time QoS monitoring

## Support
For questions and issues, please open an issue in this repository or contact the lab instructors.

