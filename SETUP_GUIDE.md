# Guide d'Installation et Configuration - Tests QoS 5G

## Vue d'Ensemble

Ce guide décrit l'installation complète de l'environnement de test QoS pour réseaux 5G, incluant :
- Déploiement du 5G Core Network (OpenAirInterface)
- Configuration du simulateur UE/gNB (UERANSIM)
- Installation des outils de test
- Configuration du serveur iperf3

**Durée d'installation :** 2-3 heures  
**Niveau :** Intermédiaire à Avancé  
**Système requis :** Ubuntu 20.04/22.04/24.04 LTS

---

## Table des Matières

1. [Prérequis Système](#prérequis-système)
2. [Architecture du Système](#architecture-du-système)
3. [Installation du 5G Core Network](#installation-du-5g-core-network)
4. [Installation de UERANSIM](#installation-de-ueransim)
5. [Configuration des Profils QoS](#configuration-des-profils-qos)
6. [Installation des Scripts de Test](#installation-des-scripts-de-test)
7. [Déploiement du Serveur iperf3](#déploiement-du-serveur-iperf3)
8. [Vérification de l'Installation](#vérification-de-linstallation)
9. [Troubleshooting](#troubleshooting)

---

## Prérequis Système

### Configuration Matérielle Minimale

```
CPU      : 4 cores (8 cores recommandé)
RAM      : 8 GB (16 GB recommandé)
Stockage : 50 GB disponible
Réseau   : Interface Ethernet
```

### Logiciels Requis

```bash
# Mise à jour système
sudo apt-get update
sudo apt-get upgrade -y

# Docker et Docker Compose
sudo apt-get install -y docker.io docker-compose

# Outils de développement
sudo apt-get install -y \
    git \
    build-essential \
    cmake \
    libsctp-dev \
    lksctp-tools \
    iproute2 \
    net-tools \
    iperf3

# Python 3 et pip
sudo apt-get install -y python3 python3-pip

# Permissions Docker
sudo usermod -aG docker $USER
newgrp docker
```

### Vérification des Prérequis

```bash
# Versions requises
docker --version          # >= 20.10
docker-compose --version  # >= 1.29
python3 --version        # >= 3.8
git --version            # >= 2.25

# Test Docker
docker run hello-world

# Test permissions
docker ps
```

---

## Architecture du Système

### Diagramme d'Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    Machine Hôte Ubuntu                        │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              5G Core Network (Docker)                  │   │
│  │                                                        │   │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐      │   │
│  │  │ AMF  │  │ SMF  │  │ UPF  │  │ NRF  │  │ UDM  │      │   │
│  │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘      │   │
│  │                                                        │   │
│  │  Réseau: 192.168.70.0/24                               │   │
│  └────────────────────────────────────────────────────────┘   │
│                            ↕                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              UERANSIM (Natif)                          │   │
│  │                                                        │   │
│  │  ┌──────┐                                              │   │
│  │  │ gNB  │  ← Simule la station de base                 │   │
│  │  └──────┘                                              │   │
│  │     ↕                                                  │   │
│  │  ┌──────┐  ┌──────┐  ┌──────┐                          │   │
│  │  │ UE1  │  │ UE2  │  │ UE3  │  ← Simule terminaux      │   │
│  │  │ VoIP │  │Video │  │ Data │                          │   │
│  │  └──────┘  └──────┘  └──────┘                          │   │
│  │                                                        │   │
│  │  Interfaces: uesimtun0, uesimtun1, uesimtun2           │   │
│  └────────────────────────────────────────────────────────┘   │
│                            ↕                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              Scripts de Test                           │   │
│  │                                                        │   │
│  │  ~/Desktop/5g-qos-testing/scripts/                     │   │
│  │    ├── test_voip_complete.py                           │   │
│  │    ├── test_video_complete.py                          │   │
│  │    └── analyze_results_simple.py                       │   │
│  └────────────────────────────────────────────────────────┘   │
│                            ↕                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │           Serveur iperf3 (Docker)                      │   │
│  │                                                        │   │
│  │           IP: 192.168.70.150                           │   │
│  │           Port: 5201 (TCP/UDP)                         │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

### Flux de Données

```
UE (10.x.0.6) → gNB → AMF → SMF → UPF → iperf3 Server
                                     ↓
                              Mesure QoS
```

---

## Installation du 5G Core Network

### 1. Cloner le Dépôt OAI

```bash
# Créer répertoire de travail
mkdir -p ~/Desktop/5g-qos-testing
cd ~/Desktop/5g-qos-testing

# Cloner OpenAirInterface CN5G
git clone https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed.git oai-cn5g
cd oai-cn5g
git checkout master
```

### 2. Configurer Docker Compose

Créer/modifier `docker-compose.yml` :

```yaml
# Docker Compose for 5G QoS Testing - Adapted for your structure
# Structure: 5g-qos-testing/oai-cn5g/ (ce fichier) et 5g-qos-testing/UERANSIM/build/

networks:
  oai-network:
    driver: bridge
    ipam:
      config:
        - subnet: 192.168.70.0/24

services:

  mysql:
    image: mysql:8.0
    container_name: mysql
    environment:
      MYSQL_ROOT_PASSWORD: linux
      MYSQL_DATABASE: oai_db
    networks:
      oai-network:
        ipv4_address: 192.168.70.131
    volumes:
      - ./database/oai_db.sql:/docker-entrypoint-initdb.d/oai_db.sql
      - ./healthscripts/mysql-healthcheck.sh:/tmp/mysql-healthcheck.sh
    healthcheck:
      test: /bin/bash -c "/tmp/mysql-healthcheck.sh"
      interval: 10s
      timeout: 5s
      retries: 5

  oai-nrf:
    image: oaisoftwarealliance/oai-nrf:develop
    container_name: oai-nrf
    networks:
      oai-network:
        ipv4_address: 192.168.70.130
    environment:
      - TZ=Europe/Paris
    volumes:
      - ./conf/config.yaml:/openair-nrf/etc/config.yaml

  oai-udr:
    image: oaisoftwarealliance/oai-udr:develop
    container_name: oai-udr
    depends_on: 
      mysql:
        condition: service_healthy
      oai-nrf:
        condition: service_started
    networks:
      oai-network:
        ipv4_address: 192.168.70.136
    environment:
      - REGISTER_NRF=yes
      - TZ=Europe/Paris
    volumes:
      - ./conf/config.yaml:/openair-udr/etc/config.yaml

  oai-udm:
    image: oaisoftwarealliance/oai-udm:develop
    container_name: oai-udm
    depends_on: 
      - oai-udr
      - oai-nrf
    networks:
      oai-network:
        ipv4_address: 192.168.70.137
    environment:
      - REGISTER_NRF=yes
      - TZ=Europe/Paris
    volumes:
      - ./conf/config.yaml:/openair-udm/etc/config.yaml

  oai-ausf:
    image: oaisoftwarealliance/oai-ausf:develop
    container_name: oai-ausf
    depends_on: 
      - oai-udm
      - oai-nrf
    networks:
      oai-network:
        ipv4_address: 192.168.70.138
    environment:
      - REGISTER_NRF=yes
      - TZ=Europe/Paris
    volumes:
      - ./conf/config.yaml:/openair-ausf/etc/config.yaml

  oai-amf:
    image: oaisoftwarealliance/oai-amf:develop
    container_name: oai-amf
    depends_on: 
      - oai-nrf
      - oai-ausf
    networks:
      oai-network:
        ipv4_address: 192.168.70.132
    environment:
      - REGISTER_NRF=yes
      - TZ=Europe/Paris
    volumes:
      - ./conf/config.yaml:/openair-amf/etc/config.yaml

  oai-smf:
    image: oaisoftwarealliance/oai-smf:develop
    container_name: oai-smf
    depends_on: 
      - oai-nrf
      - oai-amf
    networks:
      oai-network:
        ipv4_address: 192.168.70.133
    environment:
      - REGISTER_NRF=yes
      - TZ=Europe/Paris
    volumes:
      - ./conf/config.yaml:/openair-smf/etc/config.yaml

  oai-upf:
    image: oaisoftwarealliance/oai-upf:develop
    container_name: oai-upf
    depends_on: 
      - oai-smf
    cap_add: 
      - NET_ADMIN
    devices:
      - "/dev/net/tun:/dev/net/tun"
    networks:
      oai-network:
        ipv4_address: 192.168.70.134
    environment:
      - REGISTER_NRF=yes
      - TZ=Europe/Paris
      - NETWORK_UE_NAT_OPTION=yes
    volumes:
      - ./conf/config.yaml:/openair-upf/etc/config.yaml

  # iperf3 server for throughput testing
  iperf-server:
    image: networkstatic/iperf3
    container_name: iperf-server
    command: -s
    networks:
      oai-network:
        ipv4_address: 192.168.70.150
    ports:
      - "5201:5201/tcp"
      - "5201:5201/udp" 

volumes:
  mysql-data:
```

### 3. Configurer Fichier de configuration

cd conf
Créer/modifier `config.yaml` :

```yaml
################################################################################
# Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The OpenAirInterface Software Alliance licenses this file to You under
# the OAI Public License, Version 1.1  (the "License"); you may not use this file
# except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.openairinterface.org/?page_id=698
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#-------------------------------------------------------------------------------
# For more information about the OpenAirInterface (OAI) Software Alliance:
#      contact@openairinterface.org
################################################################################

# OAI CN Configuration File
### This file can be used by all OAI NFs
### Some fields are specific to an NF and will be ignored by other NFs
### The {{ env['ENV_NAME'] }} syntax lets you define these values in a docker-compose file
### If you intend to mount this file or use a bare-metal deployment, please refer to README.md
### The README.md also defines default values and allowed values for each configuration parameter

############# Common configuration

################################################################################
# OAI CN Configuration File with QoS Profiles
################################################################################

# Log level for all the NFs
log_level:
  general: debug

# If you enable registration, the other NFs will use the NRF discovery mechanism
register_nf:
  general: yes
  
http_version: 2

############## SBI Interfaces
nfs:
  amf:
    host: 192.168.70.132
    sbi:
      port: 8080
      api_version: v1
      interface_name: eth0
    n2:
      interface_name: eth0
      port: 38412
  smf:
    host: 192.168.70.133
    sbi:
      port: 8080
      api_version: v1
      interface_name: eth0
    n4:
      interface_name: eth0
      port: 8805
  upf:
    host: 192.168.70.134
    sbi:
      port: 8080
      api_version: v1
      interface_name: eth0
    n3:
      interface_name: eth0
      port: 2152
    n4:
      interface_name: eth0
      port: 8805
    n6:
      interface_name: eth0
    n9:
      interface_name: eth0
      port: 2152
  udm:
    host: 192.168.70.137
    sbi:
      port: 8080
      api_version: v1
      interface_name: eth0
  udr:
    host: 192.168.70.136
    sbi:
      port: 8080
      api_version: v1
      interface_name: eth0
  ausf:
    host: 192.168.70.138
    sbi:
      port: 8080
      api_version: v1
      interface_name: eth0
  nrf:
    host: 192.168.70.130
    sbi:
      port: 8080
      api_version: v1
      interface_name: eth0

#### Common for UDR and AMF
database:
  host: mysql
  user: root
  type: mysql
  password: linux
  database_name: oai_db
  generate_random: true
  connection_timeout: 300

## general single_nssai configuration
snssais:
  - &embb_slice
    sst: 1

############## NF-specific configuration
amf:
  pid_directory: "/var/run"
  amf_name: "OAI-AMF"
  support_features_options:
    enable_simple_scenario: no
    enable_nssf: no
    enable_smf_selection: yes
    use_external_udm: no
  relative_capacity: 30
  statistics_timer_interval: 20
  emergency_support: false
  served_guami_list:
    - mcc: 001
      mnc: 01
      amf_region_id: 01
      amf_set_id: 001
      amf_pointer: 01
  plmn_support_list:
    - mcc: 001
      mnc: 01
      tac: 0x0001
      nssai:
        - *embb_slice
  supported_integrity_algorithms:
    - "NIA1"
    - "NIA2"
  supported_encryption_algorithms:
    - "NEA0"
    - "NEA1"
    - "NEA2"

smf:
  ue_mtu: 1500
  support_features:
    use_local_subscription_info: yes
    use_local_pcc_rules: yes
  upfs:
    - host: 192.168.70.134
      config:
        enable_usage_reporting: no
  ue_dns:
    primary_ipv4: "1.1.1.1"
    primary_ipv6: "2001:4860:4860::8888"
    secondary_ipv4: "8.8.8.8"
    secondary_ipv6: "2001:4860:4860::8888"
  ims:
    pcscf_ipv4: "192.168.70.139"
    pcscf_ipv6: "fe80::7915:f408:1787:db8b"
  
  smf_info:
    sNssaiSmfInfoList:
      - sNssai: *embb_slice
        dnnSmfInfoList:
          - dnn: "voip"       # For VoIP traffic (GBR)
          - dnn: "video"      # For video streaming
          - dnn: "web"        # For web browsing
          - dnn: "default"    # Default/best effort
  
  # QoS Profiles adapted from qos_profiles.yaml
  local_subscription_infos:
    # VoIP Profile - 5QI 1 (GBR, High Priority)
    - single_nssai: *embb_slice
      dnn: "voip"
      qos_profile:
        5qi: 1                      # Conversational Voice
        session_ambr_ul: "200Kbps"  # Slightly higher than GBR for overhead
        session_ambr_dl: "200Kbps"
      # Note: GBR values should be configured per flow in policy rules
      
    # Video Streaming Profile - 5QI 9 (Non-GBR, Medium Priority)
    - single_nssai: *embb_slice
      dnn: "video"
      qos_profile:
        5qi: 9                      # Video streaming
        session_ambr_ul: "5Mbps"    # Upload for interactive video
        session_ambr_dl: "20Mbps"   # Download for HD video
        
    # Web Browsing Profile - 5QI 9 (Non-GBR, Lower Priority)
    - single_nssai: *embb_slice
      dnn: "web"
      qos_profile:
        5qi: 79                      # Best effort
        session_ambr_ul: "10Mbps"
        session_ambr_dl: "50Mbps"
        
    # Default/Best Effort - 5QI 9
    - single_nssai: *embb_slice
      dnn: "default"
      qos_profile:
        5qi: 9
        session_ambr_ul: "10Mbps"
        session_ambr_dl: "10Mbps"
  
  # Local PCC Rules for QoS enforcement
  local_pcc_rules:
    # VoIP QoS Rules
    - rule_id: 1
      precedence: 1
      flow_description: "permit out ip from any to assigned"
      qos:
        5qi: 1
        priority_level: 20
        arp:
          priority_level: 1
          preemption_capability: "NOT_PREEMPT"
          preemption_vulnerability: "NOT_PREEMPTABLE"
        # GBR parameters for VoIP
        gfbr_uplink: "150Kbps"
        gfbr_downlink: "150Kbps"
        mfbr_uplink: "150Kbps"
        mfbr_downlink: "150Kbps"
        
    # Video QoS Rules
    - rule_id: 2
      precedence: 10
      flow_description: "permit out ip from any to assigned"
      qos:
        5qi: 9
        priority_level: 80
        arp:
          priority_level: 8
          preemption_capability: "MAY_PREEMPT"
          preemption_vulnerability: "PREEMPTABLE"
          
    # Web/Best Effort QoS Rules  
    - rule_id: 3
      precedence: 20
      flow_description: "permit out ip from any to assigned"
      qos:
        5qi: 79
        priority_level: 90
        arp:
          priority_level: 9
          preemption_capability: "MAY_PREEMPT"
          preemption_vulnerability: "PREEMPTABLE"

upf:
  support_features:
    enable_bpf_datapath: no
    enable_snat: yes
  remote_n6_gw: 192.168.70.1
  smfs:
    - host: 192.168.70.133
  upf_info:
    sNssaiUpfInfoList:
      - sNssai: *embb_slice
        dnnUpfInfoList:
          - dnn: "voip"
          - dnn: "video"
          - dnn: "web"
          - dnn: "default"

## DNN configuration - Define subnets for each service type
dnns:
  - dnn: "voip"
    pdu_session_type: "IPV4"
    ipv4_subnet: "10.1.0.0/24"     # VoIP UEs get IPs from this range
    
  - dnn: "video"
    pdu_session_type: "IPV4"
    ipv4_subnet: "10.2.0.0/24"     # Video UEs get IPs from this range
    
  - dnn: "web"
    pdu_session_type: "IPV4"
    ipv4_subnet: "10.3.0.0/24"     # Web UEs get IPs from this range
    
  - dnn: "default"
    pdu_session_type: "IPV4"
    ipv4_subnet: "10.0.255.0/24"   # Default/best effort
```

### 3. Démarrer le 5G Core Network

```bash
cd ~/Desktop/5g-qos-testing/oai-cn5g

# Démarrer tous les services
docker-compose up -d

# Vérifier les conteneurs
docker-compose ps

# Tous les conteneurs doivent être "Up" et "healthy"
```

### 4. Vérifier les Logs

```bash
# Logs NRF (doit être le premier à démarrer)
docker logs oai-nrf

# Logs AMF
docker logs oai-amf

# Logs SMF
docker logs oai-smf

# Logs UPF
docker logs oai-upf

# Logs iperf3
docker logs iperf-server
# Devrait afficher: "Server listening on 5201"
```

---

## Installation de UERANSIM

### 1. Cloner et Compiler UERANSIM

```bash
cd ~/Desktop/5g-qos-testing

# Cloner le dépôt
git clone https://github.com/aligungr/UERANSIM.git
mv UERANSIM UERANSIM
cd UERANSIM

# Installer dépendances
sudo apt-get install -y \
    make \
    g++ \
    libsctp-dev \
    lksctp-tools \
    iproute2

# Compiler
make
```

### 2. Configurer le gNB

cd build
Créer `open5gs-gnb.yaml` :

```yaml
mcc: '001'          # Mobile Country Code value
mnc: '01'           # Mobile Network Code value (2 or 3 digits)

nci: '0x000000010'  # NR Cell Identity (36-bit)
idLength: 32        # NR gNB ID length in bits [22...32]
tac: 1              # Tracking Area Code

linkIp: 192.168.70.1   # gNB's local IP address for Radio Link Simulation
ngapIp: 192.168.70.1   # gNB's local IP address for N2 Interface (Usually same with local IP)
gtpIp: 192.168.70.1    # gNB's local IP address for N3 Interface (Usually same with local IP)

# List of AMF address information
amfConfigs:
  - address: 192.168.70.132  # AMF IP from docker-compose oai-network
    port: 38412

# List of supported S-NSSAIs by this gNB
slices:
  - sst: 1                   # Service/Slice Type (matches AMF configuration)

# Indicates whether or not SCTP stream number errors should be ignored
ignoreStreamIds: true
```

### 3. Configurer les UEs avec Profils QoS

#### UE1 - Profil VoIP (5QI 1)

Créer `build/open5gs-ue_voip.yaml` :

```yaml
# UE Configuration for VoIP Testing
# IMSI: 001010000000001 (VoIP User)
# This UE will use the "voip" DNN with 5QI 1 (GBR)

supi: 'imsi-001010000000001'
mcc: '001'
mnc: '01'
protectionScheme: 0
homeNetworkPublicKey: '5a8d38864820197c3394b92613b20b91633cbd897119273bf8e4a6f4eec0a650'
homeNetworkPublicKeyId: 1
routingIndicator: '0000'

key: 'fec86ba6eb707ed08905757b1bb44b8f'
op: 'C42449363BBAD02B66D16BC975D77CC1'
opType: 'OPC'
amf: '8000'
imei: '356938035643801'
imeiSv: '4370816125816151'

tunNetmask: '255.255.255.0'

gnbSearchList:
  - 192.168.70.1

uacAic:
  mps: false
  mcs: false

uacAcc:
  normalClass: 0
  class11: false
  class12: false
  class13: false
  class14: false
  class15: false

# Configure to use VoIP DNN for high priority voice traffic
sessions:
  - type: 'IPv4'
    apn: 'voip'      # Uses voip DNN -> 5QI 1, Priority 20
    slice:
      sst: 1

configured-nssai:
  - sst: 1

default-nssai:
  - sst: 1

integrity:
  IA1: true
  IA2: true
  IA3: true

ciphering:
  EA1: true
  EA2: true
  EA3: true

integrityMaxRate:
  uplink: 'full'
  downlink: 'full'
```

#### UE2 - Profil Video (5QI 9)

Créer `build/open5gs-ue_video.yaml` :

```yaml
# UE Configuration for Video Streaming Testing
# IMSI: 001010000000002 (Video User)
# This UE will use the "video" DNN with 5QI 9 (Non-GBR, medium priority)

supi: 'imsi-001010000000002'
mcc: '001'
mnc: '01'
protectionScheme: 0
homeNetworkPublicKey: '5a8d38864820197c3394b92613b20b91633cbd897119273bf8e4a6f4eec0a650'
homeNetworkPublicKeyId: 1
routingIndicator: '0000'

key: 'fec86ba6eb707ed08905757b1bb44b8f'
op: 'C42449363BBAD02B66D16BC975D77CC1'
opType: 'OPC'
amf: '8000'
imei: '356938035643802'
imeiSv: '4370816125816152'

tunNetmask: '255.255.255.0'

gnbSearchList:
  - 192.168.70.1

uacAic:
  mps: false
  mcs: false

uacAcc:
  normalClass: 0
  class11: false
  class12: false
  class13: false
  class14: false
  class15: false

# Configure to use Video DNN for video streaming
sessions:
  - type: 'IPv4'
    apn: 'video'     # Uses video DNN -> 5QI 9, Priority 80
    slice:
      sst: 1

configured-nssai:
  - sst: 1

default-nssai:
  - sst: 1

integrity:
  IA1: true
  IA2: true
  IA3: true

ciphering:
  EA1: true
  EA2: true
  EA3: true

integrityMaxRate:
  uplink: 'full'
  downlink: 'full'
```

#### UE3 - Profil Data (5QI 9)

Créer `build/open5gs-ue_web.yaml` :

```yaml
# UE Configuration for Web Browsing Testing
# IMSI: 001010000000003 (Web User)
# This UE will use the "web" DNN with 5QI 9 (Non-GBR, lower priority)

supi: 'imsi-001010000000003'
mcc: '001'
mnc: '01'
protectionScheme: 0
homeNetworkPublicKey: '5a8d38864820197c3394b92613b20b91633cbd897119273bf8e4a6f4eec0a650'
homeNetworkPublicKeyId: 1
routingIndicator: '0000'

key: 'fec86ba6eb707ed08905757b1bb44b8f'
op: 'C42449363BBAD02B66D16BC975D77CC1'
opType: 'OPC'
amf: '8000'
imei: '356938035643803'
imeiSv: '4370816125816153'

tunNetmask: '255.255.255.0'

gnbSearchList:
  - 192.168.70.1

uacAic:
  mps: false
  mcs: false

uacAcc:
  normalClass: 0
  class11: false
  class12: false
  class13: false
  class14: false
  class15: false

# Configure to use Web DNN for best-effort browsing
sessions:
  - type: 'IPv4'
    apn: 'web'       # Uses web DNN -> 5QI 9, Priority 90
    slice:
      sst: 1

configured-nssai:
  - sst: 1

default-nssai:
  - sst: 1

integrity:
  IA1: true
  IA2: true
  IA3: true

ciphering:
  EA1: true
  EA2: true
  EA3: true

integrityMaxRate:
  uplink: 'full'
  downlink: 'full'
```

### 4. Démarrer UERANSIM

```bash
cd ~/Desktop/5g-qos-testing/UERANSIM/build

# Terminal 1: Démarrer gNB
./nr-gnb -c open5gs-gnb.yaml

# Terminal 2: Démarrer UE1 (VoIP)
./nr-ue -c open5gs-ue_voip.yaml

# Terminal 3: Démarrer UE2 (Video)
./nr-ue -c open5gs-ue_video.yaml

# Terminal 4: Démarrer UE3 (Data)
./nr-ue -c open5gs-ue_web_.yaml
```

### 5. Vérifier les Interfaces

```bash
# Lister les interfaces créées
ip addr show | grep uesimtun

# Devrait afficher:
# uesimtun0: UE1 (VoIP)
# uesimtun1: UE2 (Video)
# uesimtun2: UE3 (Data)

# Obtenir les IPs
ip addr show uesimtun0 | grep inet
ip addr show uesimtun1 | grep inet
ip addr show uesimtun2 | grep inet
```

---

## Configuration des Profils QoS

### Table des Profils QoS 3GPP TS 23.501

| Service | 5QI | Type    | Priority  | PDB   | PER   | Débit    |
|---------|-----|---------|-----------|-------|-------|----------|
| VoIP    | 1   | GBR     | 20        | 100ms | 10^-2 | 64 kbps  |
| Video   | 9   | Non-GBR | 80        | 300ms | 10^-6 | Variable |
| Web     | 79  | Non-GBR | 90        | 300ms | 10^-6 | Variable |

**Légende :**
- **5QI** : 5G QoS Identifier
- **GBR** : Guaranteed Bit Rate
- **PDB** : Packet Delay Budget
- **PER** : Packet Error Rate

### Configuration dans UDR Database

```sql
-- Insérer les profils QoS dans la base de données MySQL

-- UE1: VoIP Profile
INSERT INTO SessionManagementSubscriptionData 
  (ueid, servingPlmnId, singleNssai, dnnConfigurations)
VALUES 
  ('imsi-001010000000001', '00101', 
   '{"sst":1,"sd":"010203"}',
   '{"internet":{"5gQosProfile":{"5qi":1,"arp":{"priorityLevel":1}}}}');

-- UE2: Video Profile
INSERT INTO SessionManagementSubscriptionData 
  (ueid, servingPlmnId, singleNssai, dnnConfigurations)
VALUES 
  ('imsi-001010000000002', '00101',
   '{"sst":1,"sd":"010203"}',
   '{"internet":{"5gQosProfile":{"5qi":9,"arp":{"priorityLevel":8}}}}');

-- UE3: Web Profile
INSERT INTO SessionManagementSubscriptionData 
  (ueid, servingPlmnId, singleNssai, dnnConfigurations)
VALUES 
  ('imsi-001010000000003', '00101',
   '{"sst":1,"sd":"010203"}',
   '{"internet":{"5gQosProfile":{"5qi":79,"arp":{"priorityLevel":9}}}}');
```

---

## Installation des Scripts de Test

### 1. Vérifier les Dépendances Python

```bash
# Test d'import
python3 -c "import socket, threading, subprocess, json, struct"
echo "✓ Toutes les dépendances sont installées"
```

---

## Déploiement du Serveur iperf3

Le serveur iperf3 est déjà inclus dans le docker-compose.yml du 5G Core Network.

### Vérification

```bash
# Vérifier que le conteneur tourne
docker ps | grep iperf

# Tester depuis l'hôte
iperf3 -c localhost -p 5201 -t 5

# Tester en UDP (pour video)
iperf3 -c localhost -p 5201 -u -b 10M -t 5
```

---

## Vérification de l'Installation

### Script de Vérification Complète

```bash
#!/bin/bash
echo "========================================="
echo "Vérification Installation 5G QoS Testing"
echo "========================================="

# 1. Docker
echo -e "\n1. Vérification Docker:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "oai-|mysql|iperf"

# 2. UERANSIM
echo -e "\n2. Vérification UERANSIM:"
if [ -d ~/Desktop/5g-qos-testing/UERANSIM ]; then
    echo "✓ UERANSIM installé"
    ls -lh ~/Desktop/5g-qos-testing/UERANSIM/build/nr-*
else
    echo "✗ UERANSIM non trouvé"
fi

# 3. Interfaces UE
echo -e "\n3. Vérification Interfaces:"
ip addr show | grep uesimtun

# 4. Scripts de test
echo -e "\n4. Vérification Scripts:"
ls -lh ~/Desktop/5g-qos-testing/scripts/*.py

# 5. Connectivité iperf3
echo -e "\n5. Test iperf3:"
iperf3 -c localhost -p 5201 -t 2

echo -e "\n========================================="
echo "Vérification terminée"
echo "========================================="
```

Enregistrez comme `verify_installation.sh` et exécutez :

```bash
chmod +x verify_installation.sh
./verify_installation.sh
```

---

## Troubleshooting

### Problème : Conteneurs Docker ne démarrent pas

**Symptôme :**
```
ERROR: Container not starting
```

**Solution :**
```bash
# Vérifier les logs
docker-compose logs

# Redémarrer proprement
docker-compose down
docker-compose up -d

# Vérifier le réseau
docker network inspect oai-cn5g_oai-network
```

### Problème : UEs ne se connectent pas

**Symptôme :**
```
[ERROR] Registration failed
```

**Solution :**
```bash
# Vérifier que AMF est accessible
ping 192.168.70.132

# Vérifier les logs AMF
docker logs oai-amf | grep -i registration

# Vérifier configuration gNB
cat ~/Desktop/5g-qos-testing/UERANSIM/build/open5gs-gnb.yaml | grep amfConfigs
```

### Problème : Pas d'interfaces uesimtun

**Symptôme :**
```
No such device: uesimtun0
```

**Solution :**
```bash
# Vérifier que UE est démarré
ps aux | grep nr-ue

# Vérifier modules kernel
sudo modprobe tun

# Redémarrer UE
killall nr-ue
./nr-ue -c open5gs-ue_voip.yaml
```

### Problème : iperf3 non accessible

**Symptôme :**
```
iperf3: connect failed
```

**Solution :**
```bash
# Vérifier conteneur
docker ps | grep iperf
docker logs iperf-server

# Vérifier port UDP
docker port iperf-server
# Doit afficher: 5201/tcp ET 5201/udp

# Si manquant, redéployer avec UDP
docker stop iperf-server
docker rm iperf-server
# Modifier docker-compose.yml pour ajouter UDP
docker-compose up -d iperf-server
```

---

## Résumé de l'Installation

### Structure Finale

```
~/Desktop/5g-qos-testing/
├── oai-cn5g/                    # 5G Core Network
│   ├── docker-compose.yml
│   ├── conf
│   │   ├── config.yaml
│   │   ├── sip.conf
│   │   └── users.conf
│   │
│   └── database/
│
├── UERANSIM/                    # Simulateur UE/gNB
│   └── build/
│       ├── nr-gnb
│       ├── nr-ue
│       ├── nr-gnb
│       ├── open5gs-gnb.yaml
│       ├── open5gs-ue_voip.yaml
│       ├── open5gs-ue_video.yaml
│       └── open5gs-ue_web.yaml
│
└── scripts/                     # Scripts de test
    ├── test_voip_complete.py
    ├── test_video_complete.py
    └── analyze_results_simple.py
```

### Services Actifs

```
Docker Containers (192.168.70.0/24):
  ├── mysql          (192.168.70.131)
  ├── oai-nrf        (192.168.70.130)
  ├── oai-ausf       (192.168.70.132)
  ├── oai-udm        (192.168.70.133)
  ├── oai-udr        (192.168.70.134)
  ├── oai-amf        (192.168.70.132)
  ├── oai-smf        (192.168.70.133)
  ├── oai-upf        (192.168.70.134)
  └── iperf-server   (192.168.70.150)

UERANSIM (Natif):
  ├── nr-gnb         (127.0.0.1)
  ├── nr-ue (UE1)    (uesimtun0: 10.1.0.*)
  ├── nr-ue (UE2)    (uesimtun1: 10.2.0.*)
  └── nr-ue (UE3)    (uesimtun2: 10.3.0.*)
```

### Commandes de Démarrage Rapide

```bash
# 1. Démarrer 5G Core
cd ~/Desktop/5g-qos-testing/oai-cn5g
docker-compose up -d

# 2. Démarrer gNB (Terminal 1)
cd ~/Desktop/5g-qos-testing/UERANSIM/build
./nr-ue -c open5gs-gnb.yaml

# 3. Démarrer UEs (Terminaux 2, 3, 4)
./nr-ue -c open5gs-ue_voip.yaml
./nr-ue -c open5gs-ue_video.yaml
./nr-ue -c open5gs-ue_web.yaml

# 4. Vérifier
ip addr show | grep uesimtun
docker ps
```

---

## Références

- **OpenAirInterface CN5G** : https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed
- **UERANSIM** : https://github.com/aligungr/UERANSIM
- **3GPP TS 23.501** : System architecture for 5G
- **3GPP TS 23.203** : Policy and charging control architecture
- **Docker Documentation** : https://docs.docker.com/

---

**Version :** 1.0  
**Date :** Janvier 2026  
**Auteur :** AZIZA - BOUBRIK - LEZOUL - YAHI

