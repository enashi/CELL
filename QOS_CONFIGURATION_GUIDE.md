# Guide de Configuration QoS 5G

## Vue d'Ensemble

Ce guide détaille la configuration des paramètres de Qualité de Service (QoS) dans un réseau 5G, en conformité avec les spécifications 3GPP TS 23.501 et TS 23.503.

**Objectif :** Configurer des profils QoS différenciés pour VoIP, Video Streaming et trafic Best Effort.

**Standards de référence :**
- 3GPP TS 23.501 : System Architecture for 5G
- 3GPP TS 23.503 : Policy and Charging Control Framework
- 3GPP TS 23.203 : Policy and Charging Control (4G/5G convergence)

---

## Table des Matières

1. [Concepts QoS 5G](#concepts-qos-5g)
2. [Architecture QoS 5G](#architecture-qos-5g)
3. [Paramètres QoS](#paramètres-qos)
4. [Configuration des Profils](#configuration-des-profils)
5. [Mapping 5QI vers Priorités](#mapping-5qi-vers-priorités)
6. [Configuration SMF/UPF](#configuration-smfupf)
7. [Validation de la Configuration](#validation-de-la-configuration)
8. [Optimisation QoS](#optimisation-qos)

---

## Concepts QoS 5G

### Différences 4G/5G

| Concept | 4G (EPS) | 5G (5GS) |
|---------|----------|----------|
| Identificateur QoS | QCI (1-9) | 5QI (1-127) |
| Granularité | Bearer | QoS Flow |
| Flexibilité | Limitée | Étendue |
| Nombre de profils | 9 standard | 127 possibles |

### Types de QoS Flows

```
┌─────────────────────────────────────────────────┐
│           5G QoS Flow Types                      │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. GBR (Guaranteed Bit Rate)                   │
│     - Débit garanti                             │
│     - Exemple: VoIP, Video Conference           │
│     - 5QI: 1, 2, 3, 4, 65-67, 71-76, 82-85     │
│                                                  │
│  2. Non-GBR (Non-Guaranteed Bit Rate)          │
│     - Débit non garanti                         │
│     - Exemple: Web browsing, Email              │
│     - 5QI: 5-9, 69-70, 79-80                   │
│                                                  │
│  3. Delay-Critical GBR                          │
│     - GBR + contraintes strictes de latence     │
│     - Exemple: URLLC, Gaming                    │
│     - 5QI: 82-85                                │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 5QI (5G QoS Identifier)

Le 5QI est l'identifiant principal des caractéristiques QoS :

```
5QI → Définit automatiquement:
  ├── Resource Type (GBR/Non-GBR)
  ├── Priority Level
  ├── Packet Delay Budget (PDB)
  ├── Packet Error Rate (PER)
  └── Default Averaging Window
```

---

## Architecture QoS 5G

### Vue d'Ensemble

```
┌──────────────────────────────────────────────────────────────┐
│                    Architecture QoS 5G                       │
│                                                              │
│                                                              │
│  UE ←─────→ gNB ←─────→ UPF ←─────→ DN (Internet)            │
│              │           │                                   │
│              │           │                                   │
│              ↓           ↓                                   │
│            AMF         SMF                                   │
│              │           │                                   │
│              │           ↓                                   │
│              │         PCF (Policy)                          │
│              │           │                                   │
│              └───────────┴──────────→ UDR (Subscriber Data)  │
│                                                              │
│  Flux QoS:                                                   │
│  1. UE demande session PDU                                   │
│  2. SMF récupère profil QoS depuis UDR                       │
│  3. PCF applique politiques                                  │
│  4. SMF configure QoS Flow dans UPF                          │
│  5. UPF marque et route les paquets selon QoS                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Gestion des QoS Flows

```
Session PDU (ex: internet)
    │
    ├── QoS Flow 1 (5QI 1 - VoIP)
    │   ├── Priority: 20
    │   ├── PDB: 100ms
    │   └── PER: 10^-2
    │
    ├── QoS Flow 2 (5QI 9 - Video)
    │   ├── Priority: 80
    │   ├── PDB: 300ms
    │   └── PER: 10^-6
    │
    └── QoS Flow 3 (5QI 79 - Best Effort)
        ├── Priority: 90
        ├── PDB: 300ms
        └── PER: 10^-6
```

---

## Paramètres QoS

### Table Complète des Paramètres 5QI Standard (3GPP TS 23.501)

| 5QI   | Resource Type      | Priority | PDB        | PER       | Example Services                           |
|-------|--------------------|----------|------------|-----------|--------------------------------------------|
| **1** | **GBR**            | **20**   | **100ms**  | **10^-2** | **Conversational Voice (VoIP)**            |
| 2     | GBR                | 40       | 150ms      | 10^-3     | Conversational Video (Live)                |
| 3     | GBR                | 30       | 50ms       | 10^-3     | Real Time Gaming                           |
| 4     | GBR                | 50       | 300ms      | 10^-6     | Non-Conversational Video (Buffered)        |
| 5     | Non-GBR            | 10       | 100ms      | 10^-6     | IMS Signalling                             |
| 6     | Non-GBR            | 60       | 300ms      | 10^-6     | Video (Buffered Streaming) TCP             |
| 7     | Non-GBR            | 70       | 100ms      | 10^-3     | Voice, Video (Live Streaming)              |
| 8     | Non-GBR            | 80       | 300ms      | 10^-6     | Video (Buffered Streaming)                 |
| **9** | **Non-GBR**        | **90**   | **300ms**  | **10^-6** | **Video/TCP/Default Bearer**               |
| 65    | GBR                | 7        | 75ms       | 10^-2     | Mission Critical user plane (Push-To-Talk) |
| 66    | GBR                | 20       | 100ms      | 10^-2     | Mission Critical Voice                     |
| 69    | Non-GBR            | 5        | 60ms       | 10^-6     | Mission Critical delay sensitive           |
| 70    | Non-GBR            | 55       | 200ms      | 10^-6     | Mission Critical Data                      |
| 79    | Non-GBR            | 65       | 50ms       | 10^-2     | V2X Messages                               |
| 80    | Non-GBR            | 68       | 10ms       | 10^-6     | Low Latency eMBB                           |
| 82    | Delay-Critical GBR | 19       | 10ms       | 10^-4     | Discrete Automation                        |
| 83    | Delay-Critical GBR | 22       | 10ms       | 10^-4     | Discrete Automation                        |
| 84    | Delay-Critical GBR | 24       | 30ms       | 10^-5     | Intelligent Transport Systems              |
| 85    | Delay-Critical GBR | 21       | 5ms        | 10^-5     | Electricity Distribution (URLLC)           |

### Paramètres ARP (Allocation and Retention Priority)

```yaml
ARP:
  priorityLevel: 1-15          # 1 = Highest, 15 = Lowest
  preemptionCapability:        # MAY_PREEMPT / NOT_PREEMPT
  preemptionVulnerability:     # PREEMPTABLE / NOT_PREEMPTABLE
```

**Matrice de Préemption :**

```
Service à priorité HAUTE (ARP=1) peut préempter service BASSE priorité (ARP=9)
Service à priorité BASSE (ARP=9) NE PEUT PAS préempter service HAUTE priorité
```

### Sélection des 5QI pour Notre Projet

Pour ce projet, nous utilisons :

| Service | 5QI | Justification |
|---------|-----|---------------|
| **VoIP** | **1** | Conversational Voice - Standard 3GPP pour voix temps réel |
| **Video** | **9** | Video TCP - Standard pour streaming vidéo buffered |
| **Data/Web** | **9** | Default bearer - Trafic best effort |

**Note :** Video et Data utilisent le même 5QI (9) mais avec des **priorités différentes** :
- Video : Priority 80 (Medium)
- Data : Priority 90 (Low)

---

## Configuration des Profils

### Profil VoIP (5QI 1)
#### Configuration UERANSIM

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

### Profil Video Streaming (5QI 9 - Priority 80)

#### Caractéristiques
#### Configuration UERANSIM

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

---

### Profil Best Effort / Data (5QI 9 - Priority 90)

#### Caractéristiques
#### Configuration UERANSIM

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
    apn: 'web'       # Uses web DNN -> 5QI 79, Priority 90
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

---

## Mapping 5QI vers Priorités

### Hiérarchie des Priorités

```
┌─────────────────────────────────────────┐
│      Hiérarchie QoS (Priority)          │
├─────────────────────────────────────────┤
│                                         │
│  Priority 1-15:  Emergency Services     │
│  Priority 10:    IMS Signalling         │
│  Priority 20:    VoIP (5QI 1)           │ ← HIGHEST (notre projet)
│  Priority 30-50: Video Conference       │
│  Priority 60-70: Streaming (premium)    │
│  Priority 80:    Video Streaming (5QI 9)│ ← MEDIUM (notre projet)
│  Priority 90:    Web (5QI 79)           │ ← LOWEST (notre projet)
│                                         │
└─────────────────────────────────────────┘
```

## Configuration SMF/UPF

### Configuration SMF (Session Management Function)

Le SMF gère les sessions PDU et applique les politiques QoS.

#### Fichier de Configuration SMF

```yaml
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
```

#### Table DSCP

| Service | 5QI | Priority | DSCP | Valeur DSCP | Binary |
|---------|-----|----------|------|-------------|--------|
| VoIP    | 1   | 20       | EF   | 46          | 101110 |
| Video   | 9   | 80       | AF41 | 34          | 100010 |
| Web     | 79  | 90       | BE   | 0           | 000000 |

---

## Validation de la Configuration

### Script de Validation QoS

```bash
#!/bin/bash
# validate_qos.sh

echo "========================================="
echo "Validation Configuration QoS"
echo "========================================="

# 1. Vérifier les profils UE
echo -e "\n1. Profils UE configurés:"
for config in ~/Desktop/5g-qos-testing/UERANSIM/config/ue*.yaml; do
    echo "  Fichier: $(basename $config)"
    grep -A 5 "qos:" $config | grep -E "5qi|priority"
done

# 2. Vérifier les interfaces actives
echo -e "\n2. Interfaces UE actives:"
ip addr show | grep -E "uesimtun[0-9]" | grep inet

# 3. Tester connectivité vers iperf3
echo -e "\n3. Test connectivité iperf3:"
ping -c 3 192.168.70.150

# 4. Vérifier sessions PDU dans logs SMF
echo -e "\n4. Sessions PDU établies:"
docker logs oai-smf 2>&1 | grep -i "PDU Session Establishment" | tail -5

# 5. Vérifier QoS Flows dans logs UPF
echo -e "\n5. QoS Flows actifs:"
docker logs oai-upf 2>&1 | grep -i "QoS Flow" | tail -5

echo -e "\n========================================="
echo "Validation terminée"
echo "========================================="
```

### Tests de Validation

#### Test 1 : Vérifier 5QI Assigné

```bash
# Capturer trafic NAS entre UE et AMF
sudo tcpdump -i any -w registration.pcap "sctp"

# Analyser avec Wireshark pour voir:
# - PDU Session Establishment Request
# - PDU Session Establishment Accept
# - QoS Flow descriptions avec 5QI
```

#### Test 2 : Vérifier Priorités

```bash
# Lancer test sous congestion
cd ~/Desktop/5g-qos-testing/scripts

# Test simultané VoIP + Video + Data
python3 test_voip.py 10.2.0.8 60 &
python3 test_video.py 192.168.70.150 5 60 &
python3 test_video.py 192.168.70.150 8 60 &

# Observer les throughputs:
# VoIP devrait maintenir ~64 kbps (priorité haute)
# Video devrait être stable (priorité medium)
# Web peut varier (priorité basse)
```

---

## Optimisation QoS

### Tuning des Paramètres

#### 1. Augmenter la Bande Passante Garantie (GBR)

Pour VoIP avec codec HD :

```yaml
qos:
  5qi: 1
  gbrUl: "128kbps"   # Au lieu de 64 kbps
  gbrDl: "128kbps"
```

#### 2. Ajuster les Priorités

Pour donner plus de bande passante à la vidéo :

```yaml
qos:
  5qi: 9
  priority: 70        # Au lieu de 80 (plus prioritaire)
```

#### 3. Modifier PDB (Packet Delay Budget)

Pour applications temps réel critiques :

```yaml
qos:
  5qi: 1
  pdb: 50             # 50ms au lieu de 100ms
```

### Monitoring QoS

```bash
# Script de monitoring temps réel
#!/bin/bash
watch -n 1 '
echo "=== QoS Flows Status ==="
docker exec oai-upf cat /proc/net/dev | grep -E "uesimtun|N6"
echo ""
echo "=== SMF Sessions ==="
docker logs oai-smf 2>&1 | grep "Active Sessions" | tail -1
'
```

---

## Références Standards

### Documents 3GPP

1. **TS 23.501** - System architecture for the 5G System (5GS)
   - Section 5.7 : QoS Model
   - Section 5.7.2 : 5G QoS Characteristics

2. **TS 23.503** - Policy and charging control framework
   - Section 6.1 : QoS control

3. **TS 23.203** - Policy and charging control architecture
   - Annexe A : Standardized QCI characteristics

4. **TS 38.300** - NR overall description
   - Section 10 : QoS

### Valeurs de Référence

```
Source: 3GPP TS 23.501 V17.3.0 (2021-12)
Table 5.7.4-1: Standardized 5QI to QoS characteristics mapping

5QI 1:
  Resource Type: GBR
  Priority Level: 20
  Packet Delay Budget: 100 ms
  Packet Error Rate: 10^-2
  Default Maximum Data Burst Volume: N/A
  Default Averaging Window: 2000 ms
```

---

## Résumé Configuration

### Table Récapitulative de Notre Configuration

| UE  |       IMSI      | Service | 5QI | Priority | ARP Level | Resource Type |    IP    |
|-----|-----------------|---------|-----|----------|-----------|---------------|----------|
| UE1 | 001010000000001 | VoIP    | 1   | 20       | 1         | GBR           | 10.1.0.* |
| UE2 | 001010000000002 | Video   | 9   | 80       | 8         | Non-GBR       | 10.2.0.* |
| UE3 | 001010000000003 | Web     | 79  | 90       | 9         | Non-GBR       | 10.3.0.* |

### Conformité Standards

✅ **5QI** : Conformes 3GPP TS 23.501  
✅ **Priorités** : Hiérarchie respectée (20 > 80 > 90)  
✅ **ARP** : Préemption correctement configurée  
✅ **PDB/PER** : Valeurs standard 3GPP  

---

**Version :** 1.0  
**Date :** Janvier 2026  
**Conformité :** 3GPP Release 17
