#!/usr/bin/env python3
"""
Visualization script for QoS test results
Compatible with qos_tests.py output files
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import os

def load_json(filename):
    """Load JSON file if it exists."""
    if not os.path.exists(filename):
        return None
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return None


def plot_voip_comparison(output='voip_comparison.png'):
    """
    Generate VoIP comparison graph (normal vs congested).
    
    Reads: voip_test_results.json
    Creates: voip_comparison.png
    """
    data = load_json('voip_test_results.json')
    
    if not data or 'data' not in data:
        print("Warning: voip_test_results.json not found or invalid")
        return False
    
    stats = data['data']
    normal = stats.get('normal')
    congested = stats.get('congested')
    
    if not normal or not congested:
        print("Warning: Incomplete VoIP data")
        return False
    
    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('VoIP Test Results - Normal vs Congested Conditions', 
                 fontsize=16, fontweight='bold')
    
    conditions = ['Normal', 'Congested']
    colors = ['#2ecc71', '#e74c3c']
    
    # Subplot 1: Latency
    ax1 = axes[0]
    latencies = [normal['latency']['avg'], congested['latency']['avg']]
    bars1 = ax1.bar(conditions, latencies, color=colors, alpha=0.8, 
                    edgecolor='black', linewidth=2)
    ax1.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
    ax1.set_title('Average Latency', fontsize=13, fontweight='bold')
    ax1.axhline(y=10, color='orange', linestyle='--', linewidth=2, 
                label='Target (50ms)', alpha=0.7)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    for bar, lat in zip(bars1, latencies):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{lat:.2f}ms',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # Subplot 2: Jitter
    ax2 = axes[1]
    jitters = [normal['jitter']['avg'], congested['jitter']['avg']]
    bars2 = ax2.bar(conditions, jitters, color=colors, alpha=0.8,
                    edgecolor='black', linewidth=2)
    ax2.set_ylabel('Jitter (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('Average Jitter', fontsize=13, fontweight='bold')
    ax2.axhline(y=5, color='orange', linestyle='--', linewidth=2,
                label='Target (30ms)', alpha=0.7)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    for bar, jit in zip(bars2, jitters):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{jit:.2f}ms',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # Subplot 3: Packet Loss
    ax3 = axes[2]
    losses = [normal['packet_loss_percent'], congested['packet_loss_percent']]
    bars3 = ax3.bar(conditions, losses, color=colors, alpha=0.8,
                    edgecolor='black', linewidth=2)
    ax3.set_ylabel('Packet Loss (%)', fontsize=12, fontweight='bold')
    ax3.set_title('Packet Loss Rate', fontsize=13, fontweight='bold')
    ax3.axhline(y=0.1, color='orange', linestyle='--', linewidth=2,
                label='Target (1%)', alpha=0.7)
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    for bar, loss in zip(bars3, losses):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{loss:.2f}%',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches='tight')
    print(f"Created: {output}")
    plt.close()
    return True


def plot_video_comparison(output='video_comparison.png'):
    """
    Generate video streaming comparison graph.
    
    Reads: video_test_results.json
    Creates: video_comparison.png
    """
    data = load_json('video_test_results.json')
    
    if not data or 'data' not in data:
        print("Warning: video_test_results.json not found or invalid")
        return False
    
    results = data['data']
    
    if not results:
        print("Warning: No video test data")
        return False
    
    # Extract data for each bitrate
    bitrates = []
    throughputs = []
    buffering_events = []
    quality_scores = []
    
    for bitrate_str, stats in sorted(results.items(), key=lambda x: int(x[0])):
        if stats:
            bitrate = int(bitrate_str)
            bitrates.append(bitrate / 1000)  # Convert to Mbps
            throughputs.append(stats['throughput']['avg'])
            buffering_events.append(stats['buffering']['events'])
            quality_scores.append(stats['quality_score'])
    
    if not bitrates:
        print("Warning: No valid video data")
        return False
    
    # Create figure with 4 subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Video Streaming Test Results - Multiple Bitrates', 
                 fontsize=16, fontweight='bold')
    
    # Subplot 1: Bitrate vs Throughput
    ax1 = axes[0, 0]
    ax1.plot(bitrates, bitrates, 'r--', linewidth=2, label='Ideal', alpha=0.5)
    ax1.plot(bitrates, throughputs, 'bo-', linewidth=2, markersize=8, label='Measured')
    ax1.set_xlabel('Requested Bitrate (Mbps)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Actual Throughput (Mbps)', fontsize=12, fontweight='bold')
    ax1.set_title('Bitrate vs Throughput', fontsize=13, fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # Subplot 2: Buffering Events
    ax2 = axes[0, 1]
    colors = ['green' if b == 0 else 'orange' if b < 3 else 'red' 
              for b in buffering_events]
    bars = ax2.bar(bitrates, buffering_events, color=colors, alpha=0.7, 
                   edgecolor='black', linewidth=2)
    ax2.set_xlabel('Bitrate (Mbps)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Buffering Events', fontsize=12, fontweight='bold')
    ax2.set_title('Buffering by Bitrate', fontsize=13, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    for bar, events in zip(bars, buffering_events):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(events)}',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # Subplot 3: Quality Score
    ax3 = axes[1, 0]
    colors_quality = ['green' if q >= 90 else 'orange' if q >= 70 else 'red' 
                      for q in quality_scores]
    bars2 = ax3.bar(bitrates, quality_scores, color=colors_quality, alpha=0.7, 
                    edgecolor='black', linewidth=2)
    ax3.set_xlabel('Bitrate (Mbps)', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Quality Score', fontsize=12, fontweight='bold')
    ax3.set_title('Video Quality Score', fontsize=13, fontweight='bold')
    ax3.set_ylim(0, 110)
    ax3.axhline(y=90, color='green', linestyle='--', label='Excellent (90+)', alpha=0.5)
    ax3.axhline(y=70, color='orange', linestyle='--', label='Acceptable (70+)', alpha=0.5)
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    for bar, score in zip(bars2, quality_scores):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{score:.0f}',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # Subplot 4: Summary
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    summary = "VIDEO STREAMING SUMMARY\n\n"
    summary += f"Bitrates tested: {len(bitrates)}\n"
    summary += f"Range: {min(bitrates):.1f} - {max(bitrates):.1f} Mbps\n\n"
    
    for i, br in enumerate(bitrates):
        summary += f"{br:.1f} Mbps:\n"
        summary += f"  Throughput: {throughputs[i]:.2f} Mbps\n"
        summary += f"  Buffering: {buffering_events[i]} events\n"
        summary += f"  Quality: {quality_scores[i]:.0f}/100\n"
        
        if quality_scores[i] >= 90:
            summary += f"  Status: EXCELLENT\n\n"
        elif quality_scores[i] >= 70:
            summary += f"  Status: ACCEPTABLE\n\n"
        else:
            summary += f"  Status: DEGRADED\n\n"
    
    ax4.text(0.1, 0.9, summary, transform=ax4.transAxes,
            fontsize=10, verticalalignment='top',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches='tight')
    print(f"Created: {output}")
    plt.close()
    return True


def plot_mixed_traffic(output='mixed_traffic_comparison.png'):
    """
    Generate mixed traffic comparison graph.
    
    Reads: mixed_traffic_test_results.json
    Creates: mixed_traffic_comparison.png
    """
    data = load_json('mixed_traffic_test_results.json')
    
    if not data or 'data' not in data:
        print("Warning: mixed_traffic_test_results.json not found or invalid")
        return False
    
    stats = data['data']
    voip = stats.get('voip')
    video = stats.get('video')
    web_data = stats.get('data')
    
    if not all([voip, video, web_data]):
        print("Warning: Incomplete mixed traffic data")
        return False
    
    # Create figure with 4 subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Mixed Traffic Test - QoS Prioritization Validation', 
                 fontsize=16, fontweight='bold')
    
    services = ['VoIP\n(P:20)', 'Video\n(P:80)', 'Data\n(P:90)']
    colors = ['#2ecc71', '#3498db', '#e74c3c']
    
    # Subplot 1: Throughput
    ax1 = axes[0, 0]
    throughputs = [
        voip['throughput']['avg'],
        video['throughput']['avg'],
        web_data['throughput']['avg']
    ]
    bars1 = ax1.bar(services, throughputs, color=colors, alpha=0.8, 
                    edgecolor='black', linewidth=2)
    ax1.set_ylabel('Throughput (Mbps)', fontsize=12, fontweight='bold')
    ax1.set_title('Throughput by Service', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    for bar, tp in zip(bars1, throughputs):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{tp:.2f}',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # Subplot 2: Latency
    ax2 = axes[0, 1]
    latencies = [
        voip['latency']['avg'],
        video['latency']['avg'],
        web_data['latency']['avg']
    ]
    bars2 = ax2.bar(services, latencies, color=colors, alpha=0.8,
                    edgecolor='black', linewidth=2)
    ax2.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('Latency by Service', fontsize=13, fontweight='bold')
    ax2.axhline(y=5, color='orange', linestyle='--', linewidth=2, 
                label='VoIP Target (50ms)', alpha=0.7)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    for bar, lat in zip(bars2, latencies):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{lat:.2f}',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # Subplot 3: Packets Received
    ax3 = axes[1, 0]
    packets = [
        voip['packets_received'],
        video['packets_received'],
        web_data['packets_received']
    ]
    bars3 = ax3.bar(services, packets, color=colors, alpha=0.8,
                    edgecolor='black', linewidth=2)
    ax3.set_ylabel('Packets Received', fontsize=12, fontweight='bold')
    ax3.set_title('Packet Volume', fontsize=13, fontweight='bold')
    ax3.grid(axis='y', alpha=0.3)
    
    for bar, pkt in zip(bars3, packets):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{pkt:d}',
                ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    # Subplot 4: QoS Evaluation
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    eval_text = "QoS PRIORITIZATION VALIDATION\n\n"
    
    # VoIP evaluation
    eval_text += "VoIP (Priority 20 - High):\n"
    eval_text += f"  Latency: {voip['latency']['avg']:.2f}ms\n"
    if 'jitter' in voip:
        eval_text += f"  Jitter: {voip['jitter']['avg']:.2f}ms\n"
    if voip['latency']['avg'] < 50:
        eval_text += "  Status: PROTECTED\n"
    else:
        eval_text += "  Status: DEGRADED\n"
    
    # Video evaluation
    eval_text += "\nVideo (Priority 80 - Medium):\n"
    eval_text += f"  Throughput: {video['throughput']['avg']:.2f} Mbps\n"
    eval_text += f"  Buffering: {video.get('buffering_events', 0)} events\n"
    if video.get('buffering_events', 0) < 3:
        eval_text += "  Status: FLUIDE\n"
    else:
        eval_text += "  Status: BUFFERING\n"
    
    # Data evaluation
    eval_text += "\nData (Priority 90 - Low):\n"
    eval_text += f"  Throughput: {web_data['throughput']['avg']:.2f} Mbps\n"
    eval_text += f"  Latency: {web_data['latency']['avg']:.2f}ms\n"
    if web_data['throughput']['avg'] > 5:
        eval_text += "  Status: OK\n"
    else:
        eval_text += "  Status: LIMITED\n"
    
    # Hierarchy validation
    eval_text += "\nHIERARCHY VALIDATION:\n"
    if video['throughput']['avg'] > web_data['throughput']['avg']:
        ratio = video['throughput']['avg'] / web_data['throughput']['avg']
        eval_text += f"  Video > Data\n"
        eval_text += f"  Ratio: {ratio:.1f}:1\n"
        eval_text += "  Result: PASS\n"
    else:
        eval_text += "  Video <= Data\n"
        eval_text += "  Result: FAIL\n"
    
    if voip['latency']['avg'] < 50:
        eval_text += "  VoIP Protected: PASS\n"
    else:
        eval_text += "  VoIP Protected: FAIL\n"
    
    ax4.text(0.1, 0.9, eval_text, transform=ax4.transAxes,
            fontsize=11, verticalalignment='top',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches='tight')
    print(f"Created: {output}")
    plt.close()
    return True


def plot_all_summary(output='all_tests_summary.png'):
    """
    Generate comprehensive summary of all tests.
    
    Reads: All test result files
    Creates: all_tests_summary.png
    """
    voip_data = load_json('voip_test_results.json')
    video_data = load_json('video_test_results.json')
    mixed_data = load_json('mixed_traffic_test_results.json')
    
    has_voip = voip_data and 'data' in voip_data
    has_video = video_data and 'data' in video_data
    has_mixed = mixed_data and 'data' in mixed_data
    
    if not (has_voip or has_video or has_mixed):
        print("Warning: No test results found")
        return False
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Comprehensive QoS Test Results Summary', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: VoIP comparison (if available)
    ax1 = axes[0, 0]
    if has_voip:
        stats = voip_data['data']
        if stats.get('normal') and stats.get('congested'):
            conditions = ['Normal', 'Congested']
            latencies = [
                stats['normal']['latency']['avg'],
                stats['congested']['latency']['avg']
            ]
            colors_voip = ['#2ecc71', '#e74c3c']
            ax1.bar(conditions, latencies, color=colors_voip, alpha=0.8,
                   edgecolor='black', linewidth=2)
            ax1.set_ylabel('Latency (ms)', fontsize=11, fontweight='bold')
            ax1.set_title('VoIP: QoS Protection', fontsize=12, fontweight='bold')
            ax1.axhline(y=5, color='orange', linestyle='--', alpha=0.7)
            ax1.grid(axis='y', alpha=0.3)
            
            for i, lat in enumerate(latencies):
                ax1.text(i, lat, f'{lat:.1f}ms', ha='center', va='bottom', fontweight='bold')
    else:
        ax1.text(0.5, 0.5, 'VoIP data\nnot available', 
                ha='center', va='center', transform=ax1.transAxes, fontsize=12)
    ax1.set_title('VoIP: QoS Protection', fontsize=12, fontweight='bold')
    
    # Plot 2: Video quality (if available)
    ax2 = axes[0, 1]
    if has_video:
        results = video_data['data']
        bitrates = []
        quality_scores = []
        
        for bitrate_str, stats in sorted(results.items(), key=lambda x: int(x[0])):
            if stats:
                bitrates.append(int(bitrate_str) / 1000)
                quality_scores.append(stats['quality_score'])
        
        if bitrates:
            ax2.plot(bitrates, quality_scores, 'bo-', linewidth=2, markersize=8)
            ax2.set_xlabel('Bitrate (Mbps)', fontsize=11, fontweight='bold')
            ax2.set_ylabel('Quality Score', fontsize=11, fontweight='bold')
            ax2.set_title('Video: Quality vs Bitrate', fontsize=12, fontweight='bold')
            ax2.axhline(y=90, color='green', linestyle='--', alpha=0.5)
            ax2.axhline(y=70, color='orange', linestyle='--', alpha=0.5)
            ax2.grid(alpha=0.3)
            ax2.set_ylim(0, 110)
    else:
        ax2.text(0.5, 0.5, 'Video data\nnot available',
                ha='center', va='center', transform=ax2.transAxes, fontsize=12)
    ax2.set_title('Video: Quality vs Bitrate', fontsize=12, fontweight='bold')
    
    # Plot 3: Mixed traffic throughput (if available)
    ax3 = axes[1, 0]
    if has_mixed:
        stats = mixed_data['data']
        if all(k in stats for k in ['voip', 'video', 'data']):
            services = ['VoIP', 'Video', 'Data']
            throughputs = [
                stats['voip']['throughput']['avg'],
                stats['video']['throughput']['avg'],
                stats['data']['throughput']['avg']
            ]
            colors_mixed = ['#2ecc71', '#3498db', '#e74c3c']
            ax3.bar(services, throughputs, color=colors_mixed, alpha=0.8,
                   edgecolor='black', linewidth=2)
            ax3.set_ylabel('Throughput (Mbps)', fontsize=11, fontweight='bold')
            ax3.set_title('Mixed: Throughput by Service', fontsize=12, fontweight='bold')
            ax3.grid(axis='y', alpha=0.3)
            
            for i, tp in enumerate(throughputs):
                ax3.text(i, tp, f'{tp:.1f}', ha='center', va='bottom', fontweight='bold')
    else:
        ax3.text(0.5, 0.5, 'Mixed traffic\ndata not available',
                ha='center', va='center', transform=ax3.transAxes, fontsize=12)
    ax3.set_title('Mixed: Throughput by Service', fontsize=12, fontweight='bold')
    
    # Plot 4: Global summary
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    summary = "GLOBAL SUMMARY\n\n"
    
    if has_voip:
        stats = voip_data['data']
        if stats.get('normal') and stats.get('congested'):
            impact = ((stats['congested']['latency']['avg'] - 
                      stats['normal']['latency']['avg']) / 
                      stats['normal']['latency']['avg']) * 100
            summary += f"VoIP Test:\n"
            summary += f"  Congestion impact: {impact:+.1f}%\n"
            if abs(impact) < 50:
                summary += f"  Result: PROTECTED\n"
            else:
                summary += f"  Result: DEGRADED\n"
    
    if has_video:
        results = video_data['data']
        summary += f"\nVideo Test:\n"
        summary += f"  {len(results)} bitrates tested\n"
        summary += f"  Result: VALIDATED\n"
    
    if has_mixed:
        stats = mixed_data['data']
        if all(k in stats for k in ['voip', 'video', 'data']):
            summary += f"\nMixed Traffic:\n"
            video_thr = stats['video']['throughput']['avg']
            data_thr = stats['data']['throughput']['avg']
            if video_thr > data_thr:
                summary += f"  Hierarchy: CORRECT\n"
                summary += f"  Video > Data ({video_thr:.1f} > {data_thr:.1f})\n"
            else:
                summary += f"  Hierarchy: ANOMALY\n"
    
    summary += f"\nOVERALL CONCLUSION:\n"
    if has_voip and has_mixed:
        summary += f"  QoS VALIDATED\n"
        summary += f"  Prioritization working\n"
    else:
        summary += f"  Tests incomplete\n"
    
    ax4.text(0.1, 0.9, summary, transform=ax4.transAxes,
            fontsize=12, verticalalignment='top',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches='tight')
    print(f"Created: {output}")
    plt.close()
    return True


def main():
    """Main function to generate all visualizations."""
    print("="*70)
    print("QoS Test Results Visualization")
    print("="*70)
    print("\nGenerating graphs from test results...\n")
    
    generated = []
    
    # Generate VoIP comparison
    if plot_voip_comparison():
        generated.append("voip_comparison.png")
    
    # Generate video comparison
    if plot_video_comparison():
        generated.append("video_comparison.png")
    
    # Generate mixed traffic comparison
    if plot_mixed_traffic():
        generated.append("mixed_traffic_comparison.png")
    
    # Generate overall summary
    if plot_all_summary():
        generated.append("all_tests_summary.png")
    
    print("\n" + "="*70)
    if generated:
        print("Visualization complete!")
        print("\nGenerated files:")
        for filename in generated:
            print(f"  - {filename}")
    else:
        print("No visualizations generated.")
        print("Make sure test result JSON files exist:")
        print("  - voip_test_results.json")
        print("  - video_test_results.json")
        print("  - mixed_traffic_test_results.json")
    print("="*70)


if __name__ == "__main__":
    main()
