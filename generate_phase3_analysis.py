#!/usr/bin/env python3
"""
Phase 3 - Générateur de graphiques et d'analyse pour le projet 5G QoS
Génère automatiquement des visualisations professionnelles pour le rapport
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime
import json

# Configuration des styles
plt.style.use('seaborn-v0_8-darkgrid')
COLORS = {
    'voip': '#2ecc71',    # Vert - Haute priorité
    'video': '#3498db',   # Bleu - Moyenne priorité  
    'web': '#e74c3c',     # Rouge - Basse priorité
}

class QoSAnalyzer:
    """Analyse et visualisation des résultats QoS"""
    
    def __init__(self):
        self.data = {
            'ues': {
                'voip': {
                    'imsi': '001010000000001',
                    'ip': '10.1.0.2',
                    'subnet': '10.1.0.0/24',
                    'interface': 'uesimtun2',
                    'dnn': 'voip',
                    'qos': {
                        '5qi': 1,
                        'type': 'GBR',
                        'priority': 20,
                        'arp': 1,
                        'mbr_ul': 150,  # Kbps
                        'mbr_dl': 150,
                        'gfbr': 150
                    }
                },
                'video': {
                    'imsi': '001010000000002',
                    'ip': '10.2.0.2',
                    'subnet': '10.2.0.0/24',
                    'interface': 'uesimtun1',
                    'dnn': 'video',
                    'qos': {
                        '5qi': 9,
                        'type': 'Non-GBR',
                        'priority': 80,
                        'arp': 8,
                        'mbr_ul': None,
                        'mbr_dl': None,
                        'gfbr': None
                    }
                },
                'web': {
                    'imsi': '001010000000003',
                    'ip': '10.3.0.2',
                    'subnet': '10.3.0.0/24',
                    'interface': 'uesimtun0',
                    'dnn': 'web',
                    'qos': {
                        '5qi': 79,
                        'type': 'Non-GBR',
                        'priority': 90,
                        'arp': 9,
                        'mbr_ul': None,
                        'mbr_dl': None,
                        'gfbr': None
                    }
                }
            },
            'tests': {
                'video_to_voip': {
                    'source': 'video',
                    'destination': 'voip',
                    'throughput': 48.7,  # Gbps
                    'transfer': 170,      # GB
                    'retrans': 54,
                    'duration': 30        # secondes
                },
                'web_to_voip': {
                    'source': 'web',
                    'destination': 'voip',
                    'throughput': 49.2,  # Gbps
                    'transfer': 172,      # GB
                    'retrans': 80,
                    'duration': 30        # secondes
                }
            }
        }
    
    def generate_qos_comparison_chart(self, output_file='qos_comparison.png'):
        """Graphique comparatif des profils QoS"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Comparaison des Profils QoS - 5G Network', 
                     fontsize=16, fontweight='bold')
        
        ues = ['VoIP', 'Video', 'Web']
        colors = [COLORS['voip'], COLORS['video'], COLORS['web']]
        
        # Graph 1: 5QI
        ax1 = axes[0, 0]
        qis = [self.data['ues']['voip']['qos']['5qi'],
               self.data['ues']['video']['qos']['5qi'],
               self.data['ues']['web']['qos']['5qi']]
        bars1 = ax1.bar(ues, qis, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
        ax1.set_ylabel('5QI Value', fontsize=12, fontweight='bold')
        ax1.set_title('5QI (5G QoS Identifier)', fontsize=13, fontweight='bold')
        ax1.set_ylim(0, 10)
        ax1.grid(axis='y', alpha=0.3)
        for bar, qi in zip(bars1, qis):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{qi}',
                    ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        # Graph 2: Priority Level
        ax2 = axes[0, 1]
        priorities = [self.data['ues']['voip']['qos']['priority'],
                     self.data['ues']['video']['qos']['priority'],
                     self.data['ues']['web']['qos']['priority']]
        bars2 = ax2.bar(ues, priorities, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
        ax2.set_ylabel('Priority Level', fontsize=12, fontweight='bold')
        ax2.set_title('Priority Level (lower = higher priority)', fontsize=13, fontweight='bold')
        ax2.set_ylim(0, 100)
        ax2.invert_yaxis()  # Inverser pour montrer que 20 > 80 > 90
        ax2.grid(axis='y', alpha=0.3)
        for bar, prio in zip(bars2, priorities):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{prio}',
                    ha='center', va='top', fontweight='bold', fontsize=11)
        
        # Graph 3: ARP Priority
        ax3 = axes[1, 0]
        arps = [self.data['ues']['voip']['qos']['arp'],
                self.data['ues']['video']['qos']['arp'],
                self.data['ues']['web']['qos']['arp']]
        bars3 = ax3.bar(ues, arps, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
        ax3.set_ylabel('ARP Priority Level', fontsize=12, fontweight='bold')
        ax3.set_title('ARP (Allocation & Retention Priority)', fontsize=13, fontweight='bold')
        ax3.set_ylim(0, 10)
        ax3.grid(axis='y', alpha=0.3)
        for bar, arp in zip(bars3, arps):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{arp}',
                    ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        # Graph 4: Type (GBR vs Non-GBR)
        ax4 = axes[1, 1]
        types = ['GBR', 'Non-GBR', 'Non-GBR']
        type_values = [1 if t == 'GBR' else 0 for t in types]
        bars4 = ax4.bar(ues, type_values, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
        ax4.set_ylabel('QoS Type', fontsize=12, fontweight='bold')
        ax4.set_title('QoS Flow Type', fontsize=13, fontweight='bold')
        ax4.set_yticks([0, 1])
        ax4.set_yticklabels(['Non-GBR', 'GBR'])
        ax4.set_ylim(-0.1, 1.2)
        for bar, t in zip(bars4, types):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    t,
                    ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Graphique QoS sauvegardé: {output_file}")
        plt.close()
    
    def generate_throughput_comparison(self, output_file='throughput_comparison.png'):
        """Graphique comparatif des throughputs"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('Résultats Tests de Performance - iperf3', 
                     fontsize=16, fontweight='bold')
        
        tests = ['Video → VoIP', 'Web → VoIP']
        throughputs = [
            self.data['tests']['video_to_voip']['throughput'],
            self.data['tests']['web_to_voip']['throughput']
        ]
        transfers = [
            self.data['tests']['video_to_voip']['transfer'],
            self.data['tests']['web_to_voip']['transfer']
        ]
        colors_tests = [COLORS['video'], COLORS['web']]
        
        # Graph 1: Throughput
        bars1 = ax1.barh(tests, throughputs, color=colors_tests, 
                        alpha=0.8, edgecolor='black', linewidth=2)
        ax1.set_xlabel('Throughput (Gbps)', fontsize=12, fontweight='bold')
        ax1.set_title('Average Throughput', fontsize=13, fontweight='bold')
        ax1.set_xlim(0, 55)
        ax1.grid(axis='x', alpha=0.3)
        for bar, tp in zip(bars1, throughputs):
            width = bar.get_width()
            ax1.text(width, bar.get_y() + bar.get_height()/2.,
                    f' {tp} Gbps',
                    ha='left', va='center', fontweight='bold', fontsize=11)
        
        # Graph 2: Transfer
        bars2 = ax2.barh(tests, transfers, color=colors_tests, 
                        alpha=0.8, edgecolor='black', linewidth=2)
        ax2.set_xlabel('Total Transfer (GB)', fontsize=12, fontweight='bold')
        ax2.set_title('Total Data Transferred (30s)', fontsize=13, fontweight='bold')
        ax2.set_xlim(0, 180)
        ax2.grid(axis='x', alpha=0.3)
        for bar, tf in zip(bars2, transfers):
            width = bar.get_width()
            ax2.text(width, bar.get_y() + bar.get_height()/2.,
                    f' {tf} GB',
                    ha='left', va='center', fontweight='bold', fontsize=11)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Graphique throughput sauvegardé: {output_file}")
        plt.close()
    
    def generate_architecture_diagram(self, output_file='architecture_simplified.png'):
        """Diagramme d'architecture simplifié"""
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        # Titre
        ax.text(5, 9.5, 'Architecture 5G QoS Testing', 
                ha='center', fontsize=18, fontweight='bold')
        
        # Couche UERANSIM (Native)
        ueransim_box = mpatches.FancyBboxPatch((0.5, 6), 4, 2.5, 
                                               boxstyle="round,pad=0.1",
                                               facecolor='lightblue', 
                                               edgecolor='black', linewidth=2)
        ax.add_patch(ueransim_box)
        ax.text(2.5, 8, 'UERANSIM (Native)', ha='center', fontsize=12, fontweight='bold')
        
        # gNB
        gnb_box = mpatches.Rectangle((1, 7.3), 1, 0.5, facecolor=COLORS['voip'], 
                                     edgecolor='black', linewidth=1.5)
        ax.add_patch(gnb_box)
        ax.text(1.5, 7.55, 'gNB', ha='center', va='center', fontsize=9, fontweight='bold')
        
        # UEs
        ue_voip = mpatches.Rectangle((0.7, 6.5), 0.8, 0.4, facecolor=COLORS['voip'],
                                     edgecolor='black', linewidth=1.5)
        ax.add_patch(ue_voip)
        ax.text(1.1, 6.7, 'UE VoIP', ha='center', va='center', fontsize=8, fontweight='bold')
        
        ue_video = mpatches.Rectangle((1.8, 6.5), 0.8, 0.4, facecolor=COLORS['video'],
                                      edgecolor='black', linewidth=1.5)
        ax.add_patch(ue_video)
        ax.text(2.2, 6.7, 'UE Video', ha='center', va='center', fontsize=8, fontweight='bold')
        
        ue_web = mpatches.Rectangle((2.9, 6.5), 0.8, 0.4, facecolor=COLORS['web'],
                                    edgecolor='black', linewidth=1.5)
        ax.add_patch(ue_web)
        ax.text(3.3, 6.7, 'UE Web', ha='center', va='center', fontsize=8, fontweight='bold')
        
        # Docker Bridge Network
        bridge_box = mpatches.FancyBboxPatch((0.5, 4.5), 9, 0.8,
                                            boxstyle="round,pad=0.05",
                                            facecolor='lightyellow',
                                            edgecolor='orange', linewidth=2)
        ax.add_patch(bridge_box)
        ax.text(5, 4.9, 'Docker Bridge Network (192.168.70.0/24)', 
                ha='center', fontsize=11, fontweight='bold')
        
        # 5G Core (Docker)
        core_box = mpatches.FancyBboxPatch((0.5, 0.5), 9, 3.5,
                                          boxstyle="round,pad=0.1",
                                          facecolor='lightgreen',
                                          edgecolor='black', linewidth=2)
        ax.add_patch(core_box)
        ax.text(5, 3.7, '5G Core Network (Docker)', ha='center', 
                fontsize=12, fontweight='bold')
        
        # Control Plane
        cp_box = mpatches.Rectangle((1, 2), 3.5, 1.3, facecolor='lightcyan',
                                    edgecolor='black', linewidth=1.5)
        ax.add_patch(cp_box)
        ax.text(2.75, 3.1, 'Control Plane', ha='center', fontsize=10, fontweight='bold')
        
        nfs = [('AMF', 1.2, 2.5), ('SMF', 2.2, 2.5), ('NRF', 3.2, 2.5),
               ('UDM', 1.2, 2.1), ('AUSF', 2.2, 2.1), ('UDR', 3.2, 2.1)]
        for nf, x, y in nfs:
            nf_box = mpatches.Rectangle((x, y), 0.6, 0.25, facecolor='white',
                                       edgecolor='black', linewidth=1)
            ax.add_patch(nf_box)
            ax.text(x+0.3, y+0.125, nf, ha='center', va='center', 
                   fontsize=7, fontweight='bold')
        
        # User Plane
        up_box = mpatches.Rectangle((5, 2), 1.5, 1.3, facecolor='lightcoral',
                                    edgecolor='black', linewidth=1.5)
        ax.add_patch(up_box)
        ax.text(5.75, 3.1, 'User Plane', ha='center', fontsize=10, fontweight='bold')
        
        upf_box = mpatches.Rectangle((5.2, 2.4), 1.1, 0.5, facecolor='white',
                                    edgecolor='black', linewidth=1)
        ax.add_patch(upf_box)
        ax.text(5.75, 2.65, 'UPF', ha='center', va='center', 
               fontsize=9, fontweight='bold')
        
        # Database
        db_box = mpatches.Rectangle((7, 2.5), 1.5, 0.6, facecolor='lightgray',
                                    edgecolor='black', linewidth=1.5)
        ax.add_patch(db_box)
        ax.text(7.75, 2.8, 'MySQL', ha='center', va='center', 
               fontsize=9, fontweight='bold')
        
        # Flèches de connexion
        # UERANSIM -> Docker
        ax.annotate('', xy=(2.5, 4.5), xytext=(2.5, 6),
                   arrowprops=dict(arrowstyle='<->', lw=2, color='blue'))
        ax.text(2.8, 5.2, 'N2/N3', fontsize=9, color='blue', fontweight='bold')
        
        # SMF highlight (QoS)
        ax.text(2.5, 1.7, '⭐ QoS Engine', ha='center', fontsize=8, 
               color='red', fontweight='bold')
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Diagramme architecture sauvegardé: {output_file}")
        plt.close()
    
    def generate_qos_behavior_chart(self, output_file='qos_behavior_expected.png'):
        """Graphique du comportement QoS attendu sous congestion"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('Comportement QoS Attendu en Situation de Congestion', 
                     fontsize=16, fontweight='bold')
        
        # Scenario 1: Sans congestion (observé)
        ax1.set_title('Sans Congestion (Testé)', fontsize=13, fontweight='bold')
        ues = ['VoIP', 'Video', 'Web']
        throughput_normal = [48.7, 48.7, 49.2]  # Tous obtiennent le max
        colors = [COLORS['voip'], COLORS['video'], COLORS['web']]
        
        bars1 = ax1.bar(ues, throughput_normal, color=colors, 
                       alpha=0.8, edgecolor='black', linewidth=2)
        ax1.set_ylabel('Throughput (Gbps)', fontsize=12, fontweight='bold')
        ax1.set_ylim(0, 55)
        ax1.grid(axis='y', alpha=0.3)
        for bar, tp in zip(bars1, throughput_normal):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{tp:.1f}',
                    ha='center', va='bottom', fontweight='bold', fontsize=11)
        ax1.text(1.5, 52, 'Capacité suffisante\n→ Tous les UEs obtiennent le débit max',
                ha='center', fontsize=9, style='italic')
        
        # Scenario 2: Avec congestion (théorique)
        ax2.set_title('Avec Congestion (Attendu)', fontsize=13, fontweight='bold')
        # Simulation: bande totale limitée à 10 Gbps
        # VoIP: garanti 150 Kbps = 0.00015 Gbps (négligeable) -> obtient son GBR
        # Video (priority 80): 70% de 10 Gbps = 7 Gbps
        # Web (priority 90): 30% de 10 Gbps = 3 Gbps
        throughput_congestion = [0.15/1000, 7, 3]  # GBR VoIP en Gbps, puis video, web
        
        bars2 = ax2.bar(ues, throughput_congestion, color=colors,
                       alpha=0.8, edgecolor='black', linewidth=2)
        ax2.set_ylabel('Throughput (Gbps)', fontsize=12, fontweight='bold')
        ax2.set_ylim(0, 10)
        ax2.grid(axis='y', alpha=0.3)
        
        # Annotations spéciales
        ax2.text(0, 0.3, 'GBR\n150 Kbps\ngaranti',
                ha='center', fontsize=8, fontweight='bold')
        ax2.text(1, 7.5, '7 Gbps\n(70%)',
                ha='center', fontsize=10, fontweight='bold')
        ax2.text(2, 3.5, '3 Gbps\n(30%)',
                ha='center', fontsize=10, fontweight='bold')
        
        ax2.text(1.5, 9.2, 'Bande limitée à 10 Gbps\n→ Différenciation selon Priority Level',
                ha='center', fontsize=9, style='italic')
        
        # Ratio Video/Web
        ax2.text(1.5, 8.5, f'Ratio Video/Web = {7/3:.1f}:1',
                ha='center', fontsize=9, color='purple', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Graphique comportement QoS sauvegardé: {output_file}")
        plt.close()
    
    def generate_subnet_mapping(self, output_file='subnet_mapping.png'):
        """Visualisation du mapping DNN → Subnet"""
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        ax.text(5, 9.5, 'Mapping DNN → Subnet IP', 
                ha='center', fontsize=18, fontweight='bold')
        
        # DNN boxes
        dnns = [
            ('voip', COLORS['voip'], 2, 7),
            ('video', COLORS['video'], 5, 7),
            ('web', COLORS['web'], 8, 7)
        ]
        
        subnets = [
            ('10.1.0.0/24', COLORS['voip'], 2, 3, '10.1.0.2'),
            ('10.2.0.0/24', COLORS['video'], 5, 3, '10.2.0.2'),
            ('10.3.0.0/24', COLORS['web'], 8, 3, '10.3.0.2')
        ]
        
        for dnn, color, x, y in dnns:
            # DNN box
            dnn_box = mpatches.FancyBboxPatch((x-0.8, y), 1.6, 0.8,
                                             boxstyle="round,pad=0.1",
                                             facecolor=color, alpha=0.7,
                                             edgecolor='black', linewidth=2)
            ax.add_patch(dnn_box)
            ax.text(x, y+0.4, f'DNN: {dnn}', ha='center', va='center',
                   fontsize=12, fontweight='bold')
        
        for subnet, color, x, y, ip in subnets:
            # Subnet box
            subnet_box = mpatches.FancyBboxPatch((x-0.8, y), 1.6, 1.2,
                                                boxstyle="round,pad=0.1",
                                                facecolor=color, alpha=0.3,
                                                edgecolor='black', linewidth=2)
            ax.add_patch(subnet_box)
            ax.text(x, y+0.9, f'Subnet', ha='center', fontsize=10, fontweight='bold')
            ax.text(x, y+0.6, subnet, ha='center', fontsize=11, fontweight='bold')
            ax.text(x, y+0.3, f'UE IP: {ip}', ha='center', fontsize=9)
            
            # Flèche DNN -> Subnet
            ax.annotate('', xy=(x, y+1.2), xytext=(x, 7),
                       arrowprops=dict(arrowstyle='->', lw=2, color='black'))
        
        # Légende
        ax.text(5, 1.5, '✅ Séparation par DNN validée', ha='center',
               fontsize=12, fontweight='bold', color='green',
               bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Graphique mapping subnet sauvegardé: {output_file}")
        plt.close()
    
    def generate_all_graphs(self):
        """Génère tous les graphiques"""
        print("\n🎨 Génération de tous les graphiques...\n")
        
        self.generate_qos_comparison_chart()
        self.generate_throughput_comparison()
        self.generate_architecture_diagram()
        self.generate_qos_behavior_chart()
        self.generate_subnet_mapping()
        
        print("\n✅ Tous les graphiques générés avec succès!")
        print("\n📁 Fichiers créés:")
        print("   • qos_comparison.png")
        print("   • throughput_comparison.png")
        print("   • architecture_simplified.png")
        print("   • qos_behavior_expected.png")
        print("   • subnet_mapping.png")
        print("\n💡 Utilisez ces graphiques dans votre rapport!")

    def export_data_json(self, output_file='qos_data.json'):
        """Exporte les données en JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        print(f"✅ Données exportées: {output_file}")
    
    def generate_summary_table(self):
        """Génère un résumé textuel des données"""
        print("\n" + "="*80)
        print("📊 RÉSUMÉ DES DONNÉES COLLECTÉES")
        print("="*80)
        
        print("\n🎯 PROFILS QoS:")
        print("-" * 80)
        for ue_name, ue_data in self.data['ues'].items():
            qos = ue_data['qos']
            print(f"\n{ue_name.upper():>10} | DNN: {ue_data['dnn']:>6} | "
                  f"5QI: {qos['5qi']:>2} | Type: {qos['type']:>8} | "
                  f"Priority: {qos['priority']:>3} | ARP: {qos['arp']:>2}")
            print(f"           | IP: {ue_data['ip']:>12} | "
                  f"Subnet: {ue_data['subnet']:>15} | "
                  f"Interface: {ue_data['interface']}")
        
        print("\n\n📈 RÉSULTATS TESTS:")
        print("-" * 80)
        for test_name, test_data in self.data['tests'].items():
            print(f"\n{test_name.upper().replace('_', ' ')}")
            print(f"  Source: {test_data['source'].capitalize():>10} → "
                  f"Destination: {test_data['destination'].capitalize()}")
            print(f"  Throughput: {test_data['throughput']:>6.1f} Gbps")
            print(f"  Transfer:   {test_data['transfer']:>6} GB in {test_data['duration']}s")
            print(f"  Retrans:    {test_data['retrans']:>6} packets")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 PHASE 3 - GÉNÉRATEUR D'ANALYSE ET GRAPHIQUES")
    print("="*80)
    
    analyzer = QoSAnalyzer()
    
    # Génération des graphiques
    analyzer.generate_all_graphs()
    
    # Export JSON
    analyzer.export_data_json()
    
    # Résumé textuel
    analyzer.generate_summary_table()
    
    print("\n✅ Phase 3 - Analyse terminée avec succès!")
    print("📄 Intégrez ces graphiques dans votre rapport\n")
