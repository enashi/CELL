# Setup Guide

## Prerequisites
* Ubuntu 20.04/22.04 or similar Linux distribution
* Minimum 8GB RAM, 4 CPU cores, 50GB disk space
* Docker and Docker Compose installed

## Quick Start

### 1. Clone the Repository
```bash
git clone https://gitlab.noc.onelab.eu/projects-2025-2026/5g-qos-testing.git
cd 5g-qos-testing
```

### 2. Deploy 5G Core Network with QoS Support
```bash
cd deployment
docker-compose up -d
```

### 3. Configure QoS Profiles
Edit the SMF configuration to add/modify QoS profiles:
```bash
vim config/smf.yaml
```

### 4. Deploy UEs with Different QoS Requirements
```bash
cd ueransim
# Start UE1 with 5QI 1 (VoIP)
docker-compose -f ue-voip.yaml up -d

# Start UE2 with 5QI 9 (Video)
docker-compose -f ue-video.yaml up -d
```

### 5. Run Test Scenarios
```bash
cd tests
python3 run_all_tests.py
```

### 6. Analyze Results
```bash
cd results
python3 analyze_results.py
```

## Detailed Setup Instructions

### OAI Core Configuration
See `docs/OAI_CONFIG.md` for detailed SMF/UPF QoS configuration.

### UERANSIM Configuration
See `docs/UERANSIM_CONFIG.md` for UE QoS profile configuration.

### Testing Guide
See `docs/TESTING_GUIDE.md` for detailed test procedures.

## Troubleshooting
Common issues and solutions:
* **PDU Session Failure**: Check SMF logs and verify QoS configuration
* **No QoS Differentiation**: Verify UPF supports QoS marking
* **Connection Issues**: Check network connectivity between components

