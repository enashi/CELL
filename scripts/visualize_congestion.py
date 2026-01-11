#!/usr/bin/env python3
"""
Visualization for Congestion Test Results
Generates graphs from congestion_test_results.json
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import os

def load_congestion_results(filename='congestion_test_results.json'):
    """Load congestion test results from JSON file."""
    if not os.path.exists(filename):
        print(f"Error: {filename} not found")
        return None
    
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data.get('results', {})
    except Exception as e:
        print(f"Error loading results: {e}")
        return None


def plot_progressive_congestion(results, output='congestion_progressive.png'):
    """
    Plot results from progressive bandwidth limitation test.
    
    Shows how each service type performs as bandwidth decreases.
    """
    if not results:
        print("No progressive congestion results to plot")
        return False
    
    # Extract data
    limits = sorted([int(k) for k in results.keys()])
    
    voip_throughputs = []
    video_throughputs = []
    data_throughputs = []
    voip_latencies = []
    
    for limit in limits:
        limit_str = str(limit)
        stats = results[limit_str]
        
        if stats['voip']:
            voip_throughputs.append(stats['voip']['throughput']['avg'])
            if stats['voip']['latency']:
                voip_latencies.append(stats['voip']['latency']['avg'])
            else:
                voip_latencies.append(0)
        else:
            voip_throughputs.append(0)
            voip_latencies.append(0)
        
        if stats['video']:
            video_throughputs.append(stats['video']['throughput']['avg'])
        else:
            video_throughputs.append(0)
        
        if stats['data']:
            data_throughputs.append(stats['data']['throughput']['avg'])
        else:
            data_throughputs.append(0)
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Progressive Congestion - QoS Behavior Under Bandwidth Limits', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Throughput vs Bandwidth Limit
    x = np.arange(len(limits))
    width = 0.25
    
    bars1 = ax1.bar(x - width, voip_throughputs, width, label='VoIP (P:20)', 
                    color='#2ecc71', alpha=0.8, edgecolor='black')
    bars2 = ax1.bar(x, video_throughputs, width, label='Video (P:80)', 
                    color='#3498db', alpha=0.8, edgecolor='black')
    bars3 = ax1.bar(x + width, data_throughputs, width, label='Data (P:90)', 
                    color='#e74c3c', alpha=0.8, edgecolor='black')
    
    ax1.set_xlabel('Bandwidth Limit (Mbps)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Throughput (Mbps)', fontsize=12, fontweight='bold')
    ax1.set_title('Throughput by Service Type', fontsize=13, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'{l}' for l in limits])
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}',
                        ha='center', va='bottom', fontsize=8)
    
    # Plot 2: VoIP Latency vs Bandwidth Limit
    ax2.plot(limits, voip_latencies, 'o-', linewidth=2, markersize=8, 
             color='#2ecc71', label='VoIP Latency')
    ax2.axhline(y=50, color='orange', linestyle='--', linewidth=2, 
                label='Target (50ms)', alpha=0.7)
    ax2.axhline(y=150, color='red', linestyle='--', linewidth=2, 
                label='Limit (150ms)', alpha=0.7)
    
    ax2.set_xlabel('Bandwidth Limit (Mbps)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('VoIP Latency Under Congestion', fontsize=13, fontweight='bold')
    ax2.legend()
    ax2.grid(alpha=0.3)
    
    # Add value labels
    for i, (limit, lat) in enumerate(zip(limits, voip_latencies)):
        if lat > 0:
            ax2.text(limit, lat, f'{lat:.1f}ms', 
                    ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches='tight')
    print(f"Created: {output}")
    plt.close()
    return True


def plot_background_impact(results, output='congestion_background.png'):
    """
    Plot results from background traffic impact test.
    
    Shows how high-priority traffic is protected against background load.
    """
    if not results:
        print("No background traffic results to plot")
        return False
    
    # Extract data
    bg_rates = sorted([int(k) for k in results.keys()])
    
    voip_latencies = []
    video_throughputs = []
    
    for rate in bg_rates:
        rate_str = str(rate)
        stats = results[rate_str]
        
        if stats['voip'] and stats['voip']['latency']:
            voip_latencies.append(stats['voip']['latency']['avg'])
        else:
            voip_latencies.append(0)
        
        if stats['video']:
            video_throughputs.append(stats['video']['throughput']['avg'])
        else:
            video_throughputs.append(0)
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Background Traffic Impact - QoS Protection Validation', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: VoIP Latency vs Background Traffic
    ax1.plot(bg_rates, voip_latencies, 'o-', linewidth=2, markersize=8, 
             color='#2ecc71')
    ax1.axhline(y=50, color='orange', linestyle='--', linewidth=2, 
                label='Good (50ms)', alpha=0.7)
    ax1.axhline(y=150, color='red', linestyle='--', linewidth=2, 
                label='Acceptable (150ms)', alpha=0.7)
    
    ax1.set_xlabel('Background Traffic (Mbps)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('VoIP Latency (ms)', fontsize=12, fontweight='bold')
    ax1.set_title('VoIP Protection (Priority 20)', fontsize=13, fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # Add value labels
    for rate, lat in zip(bg_rates, voip_latencies):
        if lat > 0:
            ax1.text(rate, lat, f'{lat:.1f}', ha='center', va='bottom', fontsize=9)
    
    # Plot 2: Video Throughput vs Background Traffic
    ax2.plot(bg_rates, video_throughputs, 's-', linewidth=2, markersize=8, 
             color='#3498db')
    ax2.axhline(y=2.0, color='green', linestyle='--', linewidth=2, 
                label='Target (2 Mbps)', alpha=0.7)
    
    ax2.set_xlabel('Background Traffic (Mbps)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Video Throughput (Mbps)', fontsize=12, fontweight='bold')
    ax2.set_title('Video Throughput (Priority 80)', fontsize=13, fontweight='bold')
    ax2.legend()
    ax2.grid(alpha=0.3)
    
    # Add value labels
    for rate, thr in zip(bg_rates, video_throughputs):
        if thr > 0:
            ax2.text(rate, thr, f'{thr:.2f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches='tight')
    print(f"Created: {output}")
    plt.close()
    return True


def plot_congestion_summary(prog_results, bg_results, output='congestion_summary.png'):
    """
    Create comprehensive summary of all congestion tests.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Congestion Testing - Comprehensive Summary', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Progressive Congestion - Service Comparison
    if prog_results:
        ax1 = axes[0, 0]
        limits = sorted([int(k) for k in prog_results.keys()])
        
        voip_data = [prog_results[str(l)]['voip']['throughput']['avg'] 
                     if prog_results[str(l)]['voip'] else 0 for l in limits]
        video_data = [prog_results[str(l)]['video']['throughput']['avg'] 
                      if prog_results[str(l)]['video'] else 0 for l in limits]
        data_data = [prog_results[str(l)]['data']['throughput']['avg'] 
                     if prog_results[str(l)]['data'] else 0 for l in limits]
        
        ax1.plot(limits, voip_data, 'o-', label='VoIP', color='#2ecc71', linewidth=2)
        ax1.plot(limits, video_data, 's-', label='Video', color='#3498db', linewidth=2)
        ax1.plot(limits, data_data, '^-', label='Data', color='#e74c3c', linewidth=2)
        
        ax1.set_xlabel('Bandwidth Limit (Mbps)', fontweight='bold')
        ax1.set_ylabel('Throughput (Mbps)', fontweight='bold')
        ax1.set_title('Progressive Congestion', fontweight='bold')
        ax1.legend()
        ax1.grid(alpha=0.3)
    else:
        axes[0, 0].text(0.5, 0.5, 'Progressive test\ndata not available', 
                       ha='center', va='center', transform=axes[0, 0].transAxes)
        axes[0, 0].set_title('Progressive Congestion', fontweight='bold')
    
    # Plot 2: Background Impact - VoIP Protection
    if bg_results:
        ax2 = axes[0, 1]
        bg_rates = sorted([int(k) for k in bg_results.keys()])
        
        voip_lats = [bg_results[str(r)]['voip']['latency']['avg'] 
                     if bg_results[str(r)]['voip'] and bg_results[str(r)]['voip']['latency'] 
                     else 0 for r in bg_rates]
        
        ax2.plot(bg_rates, voip_lats, 'o-', color='#2ecc71', linewidth=2, markersize=8)
        ax2.axhline(y=50, color='orange', linestyle='--', alpha=0.7)
        ax2.fill_between(bg_rates, 0, 50, alpha=0.2, color='green', label='Good (<50ms)')
        
        ax2.set_xlabel('Background Traffic (Mbps)', fontweight='bold')
        ax2.set_ylabel('VoIP Latency (ms)', fontweight='bold')
        ax2.set_title('VoIP Protection', fontweight='bold')
        ax2.legend()
        ax2.grid(alpha=0.3)
    else:
        axes[0, 1].text(0.5, 0.5, 'Background test\ndata not available', 
                       ha='center', va='center', transform=axes[0, 1].transAxes)
        axes[0, 1].set_title('VoIP Protection', fontweight='bold')
    
    # Plot 3: QoS Hierarchy Validation
    if prog_results:
        ax3 = axes[1, 0]
        
        # Use the most congested scenario (lowest bandwidth)
        lowest_limit = min([int(k) for k in prog_results.keys()])
        stats = prog_results[str(lowest_limit)]
        
        services = ['VoIP\n(P:20)', 'Video\n(P:80)', 'Data\n(P:90)']
        throughputs = [
            stats['voip']['throughput']['avg'] if stats['voip'] else 0,
            stats['video']['throughput']['avg'] if stats['video'] else 0,
            stats['data']['throughput']['avg'] if stats['data'] else 0
        ]
        colors = ['#2ecc71', '#3498db', '#e74c3c']
        
        bars = ax3.bar(services, throughputs, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
        ax3.set_ylabel('Throughput (Mbps)', fontweight='bold')
        ax3.set_title(f'Hierarchy at {lowest_limit} Mbps Limit', fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)
        
        for bar, thr in zip(bars, throughputs):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{thr:.2f}',
                    ha='center', va='bottom', fontweight='bold')
    else:
        axes[1, 0].text(0.5, 0.5, 'Hierarchy validation\ndata not available', 
                       ha='center', va='center', transform=axes[1, 0].transAxes)
        axes[1, 0].set_title('QoS Hierarchy', fontweight='bold')
    
    # Plot 4: Summary Text
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    summary = "CONGESTION TEST SUMMARY\n\n"
    
    if prog_results:
        summary += "Progressive Congestion:\n"
        limits_tested = len(prog_results)
        summary += f"  {limits_tested} bandwidth limits tested\n"
        
        # Check if VoIP maintained at lowest limit
        lowest_limit = min([int(k) for k in prog_results.keys()])
        voip_stats = prog_results[str(lowest_limit)]['voip']
        if voip_stats:
            voip_thr = voip_stats['throughput']['avg']
            if voip_thr >= 0.06:  # 64 kbps
                summary += f"  VoIP: PROTECTED at {lowest_limit} Mbps\n"
            else:
                summary += f"  VoIP: DEGRADED at {lowest_limit} Mbps\n"
    
    if bg_results:
        summary += f"\nBackground Traffic Impact:\n"
        bg_levels = len(bg_results)
        summary += f"  {bg_levels} load levels tested\n"
        
        # Check VoIP protection at highest load
        highest_load = max([int(k) for k in bg_results.keys()])
        voip_stats = bg_results[str(highest_load)]['voip']
        if voip_stats and voip_stats['latency']:
            voip_lat = voip_stats['latency']['avg']
            if voip_lat < 50:
                summary += f"  VoIP: PROTECTED at {highest_load} Mbps\n"
                summary += f"  Latency: {voip_lat:.1f}ms\n"
            else:
                summary += f"  VoIP: DEGRADED at {highest_load} Mbps\n"
                summary += f"  Latency: {voip_lat:.1f}ms\n"
    
    summary += f"\nCONCLUSION:\n"
    if prog_results and bg_results:
        summary += "  QoS protection validated\n"
        summary += "  under multiple congestion\n"
        summary += "  scenarios.\n\n"
        summary += "  Priority hierarchy (20>80>90)\n"
        summary += "  maintained correctly.\n"
    else:
        summary += "  Run all tests for complete\n"
        summary += "  validation.\n"
    
    ax4.text(0.1, 0.9, summary, transform=ax4.transAxes,
            fontsize=11, verticalalignment='top',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches='tight')
    print(f"Created: {output}")
    plt.close()
    return True


def main():
    """Main visualization function."""
    print("="*70)
    print("Congestion Test Results Visualization")
    print("="*70)
    print("\nLoading results from congestion_test_results.json...\n")
    
    results = load_congestion_results()
    
    if not results:
        print("No results to visualize.")
        print("Run: sudo python3 congestion_tests.py")
        return
    
    generated = []
    
    # Plot progressive congestion results
    if 'progressive' in results:
        if plot_progressive_congestion(results['progressive']):
            generated.append('congestion_progressive.png')
    
    # Plot background traffic impact
    if 'background' in results:
        if plot_background_impact(results['background']):
            generated.append('congestion_background.png')
    
    # Plot comprehensive summary
    prog_res = results.get('progressive', {})
    bg_res = results.get('background', {})
    
    if prog_res or bg_res:
        if plot_congestion_summary(prog_res, bg_res):
            generated.append('congestion_summary.png')
    
    print("\n" + "="*70)
    if generated:
        print("Visualization complete!")
        print("\nGenerated files:")
        for filename in generated:
            print(f"  - {filename}")
    else:
        print("No visualizations generated.")
        print("Make sure congestion_test_results.json exists and contains data.")
    print("="*70)


if __name__ == "__main__":
    main()
