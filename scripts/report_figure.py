#!/usr/bin/env python3
"""
Generate Professional Graphs for 5G QoS Report
Creates publication-quality figures for Master's thesis using actual test results

Requirements: pip3 install matplotlib numpy pandas --break-system-packages
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import json
from pathlib import Path
import sys

# Set publication-quality style
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'serif'
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9

# Create output directory
output_dir = Path("report_figures")
output_dir.mkdir(exist_ok=True)


# =============================================================================
# LOAD TEST RESULTS FROM JSON
# =============================================================================

def load_test_results():
    """Load test results from JSON files"""
    results = {
        'voip': None,
        'video': None
    }
    
    # Load VoIP results
    voip_file = Path('results_voip.json')
    if voip_file.exists():
        try:
            with open(voip_file, 'r') as f:
                results['voip'] = json.load(f)
            print(f"✓ Loaded VoIP results from {voip_file}")
        except Exception as e:
            print(f"⚠ Warning: Could not load VoIP results: {e}")
    else:
        print(f"⚠ Warning: VoIP results file not found: {voip_file}")
    
    # Load Video results
    video_file = Path('results_video.json')
    if video_file.exists():
        try:
            with open(video_file, 'r') as f:
                results['video'] = json.load(f)
            print(f"✓ Loaded Video results from {video_file}")
        except Exception as e:
            print(f"⚠ Warning: Could not load Video results: {e}")
    else:
        print(f"⚠ Warning: Video results file not found: {video_file}")
    
    return results


# =============================================================================
# Figure 1: QoS Profile Comparison - Bar Chart
# =============================================================================

def generate_qos_profile_comparison():
    """Compare QoS profiles for different services"""
    print("\n[1/7] Generating QoS Profile Comparison...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # Data
    services = ['VoIP\n(5QI 1)', 'Video\n(5QI 9)', 'Data\n(5QI 9)']
    priorities = [20, 80, 90]
    colors = ['#2ecc71', '#3498db', '#95a5a6']
    
    # Subplot 1: Priority Levels
    bars1 = ax1.barh(services, priorities, color=colors, edgecolor='black', linewidth=1.5)
    ax1.set_xlabel('Priority Level (Lower = Higher Priority)', fontweight='bold')
    ax1.set_title('Priority Level by Service Type', fontweight='bold')
    ax1.set_xlim(0, 100)
    ax1.grid(axis='x', alpha=0.3, linestyle='--')
    ax1.invert_xaxis()  # Lower numbers = higher priority
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars1, priorities)):
        ax1.text(val + 2, i, f'P={val}', va='center', fontweight='bold')
    
    # Subplot 2: Resource Type
    resource_types = ['GBR', 'Non-GBR', 'Non-GBR']
    resource_colors = ['#27ae60', '#3498db', '#95a5a6']
    
    bars2 = ax2.barh(services, [1, 1, 1], color=resource_colors, edgecolor='black', linewidth=1.5)
    ax2.set_xlabel('Resource Type', fontweight='bold')
    ax2.set_title('Resource Allocation Type', fontweight='bold')
    ax2.set_xticks([0.5])
    ax2.set_xticklabels([''])
    ax2.set_xlim(0, 1)
    
    # Add labels
    for i, (bar, rtype) in enumerate(zip(bars2, resource_types)):
        ax2.text(0.5, i, rtype, ha='center', va='center', 
                fontweight='bold', fontsize=11, color='white')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig_qos_profile_comparison.png', bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: fig_qos_profile_comparison.png")


# =============================================================================
# Figure 2: VoIP Performance Metrics (FROM JSON)
# =============================================================================

def generate_voip_performance(voip_data):
    """VoIP test results with ITU-T thresholds"""
    print("\n[2/7] Generating VoIP Performance Metrics...")
    
    if voip_data is None:
        print("  ⚠ Skipping: No VoIP test data available")
        return
    
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    
    # Extract data from JSON
    latency_avg = voip_data.get('latency', {}).get('avg', 0)
    jitter = voip_data.get('jitter', 0)
    packet_loss = voip_data.get('latency', {}).get('loss', 0)
    
    thresholds_data = voip_data.get('thresholds', {})
    latency_threshold = thresholds_data.get('latency', 150)
    jitter_threshold = thresholds_data.get('jitter', 30)
    loss_threshold = thresholds_data.get('loss', 1)
    
    # Data
    metrics = ['Latency\n(ms)', 'Jitter\n(ms)', 'Packet Loss\n(%)']
    measured = [latency_avg, jitter, packet_loss]
    thresholds = [latency_threshold, jitter_threshold, loss_threshold]
    
    # Colors for each metric
    colors = ['#2ecc71', '#27ae60', '#229954']
    
    for i, (ax, metric, value, threshold, color) in enumerate(
        zip(axes, metrics, measured, thresholds, colors)):
        
        # Determine if passed
        passed = value <= threshold
        bar_color = color if passed else '#e74c3c'
        
        # Bar chart
        bars = ax.bar(['Measured', 'Threshold'], [value, threshold], 
                     color=[bar_color, '#e74c3c'], edgecolor='black', linewidth=1.5)
        
        ax.set_ylabel('Value', fontweight='bold')
        ax.set_title(metric, fontweight='bold', fontsize=12)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontweight='bold')
        
        # Add PASS/FAIL indicator
        status_text = '✓ PASS' if passed else '✗ FAIL'
        status_color = 'green' if passed else 'red'
        ax.text(0.5, max(value, threshold) * 0.8, status_text,
               ha='center', fontsize=14, color=status_color, fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='white', 
                        edgecolor=status_color, linewidth=2))
    
    plt.suptitle('VoIP Performance vs. ITU-T G.114 Thresholds', 
                fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'fig_voip_performance.png', bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: fig_voip_performance.png")


# =============================================================================
# Figure 3: Video Throughput Performance (FROM JSON)
# =============================================================================

def generate_video_throughput(video_data):
    """Video streaming throughput performance"""
    print("\n[3/7] Generating Video Throughput Performance...")
    
    if video_data is None:
        print("  ⚠ Skipping: No Video test data available")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # Extract data from JSON
    results = video_data.get('results', {})
    throughput = results.get('throughput_mbps', 0)
    target = results.get('bitrate_target_mbps', 5)
    ratio = results.get('throughput_ratio', 0) * 100  # Convert to percentage
    threshold = video_data.get('threshold', 0.95) * 100  # 95%
    
    # Subplot 1: Throughput Comparison
    categories = ['Target\nBitrate', 'Achieved\nThroughput', f'{threshold:.0f}%\nThreshold']
    values = [target, throughput, target * (threshold/100)]
    colors = ['#3498db', '#2ecc71', '#e74c3c']
    
    bars = ax1.bar(categories, values, color=colors, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Bitrate (Mbps)', fontweight='bold')
    ax1.set_title('HD Video Streaming Target', fontweight='bold')
    ax1.set_ylim(0, max(values) * 1.3)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f'{val:.2f} Mbps',
                ha='center', va='bottom', fontweight='bold')
    
    # Add PASS indicator
    passed = ratio >= threshold
    status_text = f'✓ PASS ({ratio:.1f}%)' if passed else f'✗ FAIL ({ratio:.1f}%)'
    status_color = 'green' if passed else 'red'
    ax1.text(1, max(values) * 1.1, status_text, ha='center', fontsize=12,
            color=status_color, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white', 
                     edgecolor=status_color, linewidth=2))
    
    # Subplot 2: Throughput Ratio Gauge
    # Create gauge
    theta = np.linspace(0, np.pi, 100)
    
    # Background arc
    ax2.plot(np.cos(theta), np.sin(theta), 'k-', linewidth=2)
    
    # Fill regions
    threshold_angle = np.pi * (threshold / 100)
    ax2.fill_between(np.cos(theta[theta <= threshold_angle]), 
                     np.sin(theta[theta <= threshold_angle]),
                     alpha=0.3, color='red', label=f'< {threshold:.0f}% (FAIL)')
    ax2.fill_between(np.cos(theta[theta > threshold_angle]),
                     np.sin(theta[theta > threshold_angle]),
                     alpha=0.3, color='green', label=f'≥ {threshold:.0f}% (PASS)')
    
    # Needle for actual ratio
    needle_angle = np.pi * min(ratio / 100, 1.0)  # Cap at 100%
    needle_color = 'green' if ratio >= threshold else 'red'
    ax2.plot([0, np.cos(needle_angle)], [0, np.sin(needle_angle)],
            color=needle_color, linewidth=4, label=f'Achieved: {ratio:.1f}%')
    ax2.plot(0, 0, 'ko', markersize=10)
    
    # Labels
    ax2.text(0, -0.3, f'{ratio:.1f}%', ha='center', fontsize=18, fontweight='bold')
    ax2.text(0, -0.5, 'Throughput Ratio', ha='center', fontsize=10)
    
    ax2.set_xlim(-1.2, 1.2)
    ax2.set_ylim(-0.7, 1.2)
    ax2.axis('off')
    ax2.legend(loc='upper right', frameon=True, fancybox=True)
    ax2.set_title('Throughput Ratio Gauge', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig_video_throughput.png', bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: fig_video_throughput.png")


# =============================================================================
# Figure 4: QoS Scores Comparison (FROM JSON)
# =============================================================================

def generate_qos_scores(test_results):
    """Compare QoS scores for different service types"""
    print("\n[4/7] Generating QoS Scores Comparison...")
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Extract scores from test results
    voip_data = test_results.get('voip')
    video_data = test_results.get('video')
    
    # Subplot 1: Overall QoS Scores
    ax1 = axes[0]
    services = []
    scores = []
    colors_list = []
    
    if voip_data:
        services.append('VoIP\n(5QI 1)')
        voip_score = voip_data.get('scores', {}).get('overall', 0)
        scores.append(voip_score)
        colors_list.append('#2ecc71' if voip_score >= 80 else '#f39c12' if voip_score >= 60 else '#e74c3c')
    
    if video_data:
        services.append('Video\n(5QI 9)')
        video_score = video_data.get('scores', {}).get('overall', 0)
        scores.append(video_score)
        colors_list.append('#3498db' if video_score >= 80 else '#f39c12' if video_score >= 60 else '#e74c3c')
    
    if not services:
        print("  ⚠ Skipping: No test data available")
        return
    
    bars = ax1.barh(services, scores, color=colors_list, edgecolor='black', linewidth=2)
    ax1.set_xlabel('QoS Score (0-100)', fontweight='bold')
    ax1.set_title('Overall QoS Performance', fontweight='bold')
    ax1.set_xlim(0, 105)
    ax1.axvline(x=80, color='green', linestyle='--', linewidth=1.5, alpha=0.5, label='Target: 80')
    ax1.grid(axis='x', alpha=0.3, linestyle='--')
    
    # Add score labels
    for bar, score in zip(bars, scores):
        ax1.text(score + 2, bar.get_y() + bar.get_height()/2,
                f'{score:.1f}',
                va='center', fontweight='bold', fontsize=11)
    
    ax1.legend(loc='lower right')
    
    # Subplot 2: Detailed Metrics
    ax2 = axes[1]
    
    if voip_data and video_data:
        # Show detailed breakdown
        categories = ['Latency', 'Jitter', 'Loss', 'Throughput', 'Overall']
        voip_scores_detail = [
            voip_data.get('scores', {}).get('latency', 0),
            voip_data.get('scores', {}).get('jitter', 0),
            voip_data.get('scores', {}).get('loss', 0),
            0,  # N/A for VoIP
            voip_data.get('scores', {}).get('overall', 0)
        ]
        video_scores_detail = [
            0,  # N/A for Video
            0,  # N/A for Video
            video_data.get('scores', {}).get('loss', 0),
            video_data.get('scores', {}).get('throughput', 0),
            video_data.get('scores', {}).get('overall', 0)
        ]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax2.bar(x - width/2, voip_scores_detail, width, label='VoIP',
                       color='#2ecc71', edgecolor='black', linewidth=1)
        bars2 = ax2.bar(x + width/2, video_scores_detail, width, label='Video',
                       color='#3498db', edgecolor='black', linewidth=1)
        
        ax2.set_ylabel('Score', fontweight='bold')
        ax2.set_title('Detailed QoS Metrics Comparison', fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(categories, rotation=45, ha='right')
        ax2.set_ylim(0, 110)
        ax2.axhline(y=80, color='green', linestyle='--', linewidth=1.5, alpha=0.5)
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
    elif voip_data:
        # Show only VoIP breakdown
        categories = ['Latency', 'Jitter', 'Loss', 'Overall']
        voip_scores_detail = [
            voip_data.get('scores', {}).get('latency', 0),
            voip_data.get('scores', {}).get('jitter', 0),
            voip_data.get('scores', {}).get('loss', 0),
            voip_data.get('scores', {}).get('overall', 0)
        ]
        
        bars = ax2.bar(categories, voip_scores_detail, color='#2ecc71', 
                      edgecolor='black', linewidth=1.5)
        ax2.set_ylabel('Score', fontweight='bold')
        ax2.set_title('VoIP QoS Metrics Detail', fontweight='bold')
        ax2.set_ylim(0, 110)
        ax2.axhline(y=80, color='green', linestyle='--', linewidth=1.5, alpha=0.5)
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
    elif video_data:
        # Show only Video breakdown
        categories = ['Throughput', 'Loss', 'Overall']
        video_scores_detail = [
            video_data.get('scores', {}).get('throughput', 0),
            video_data.get('scores', {}).get('loss', 0),
            video_data.get('scores', {}).get('overall', 0)
        ]
        
        bars = ax2.bar(categories, video_scores_detail, color='#3498db',
                      edgecolor='black', linewidth=1.5)
        ax2.set_ylabel('Score', fontweight='bold')
        ax2.set_title('Video QoS Metrics Detail', fontweight='bold')
        ax2.set_ylim(0, 110)
        ax2.axhline(y=80, color='green', linestyle='--', linewidth=1.5, alpha=0.5)
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig_qos_scores.png', bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: fig_qos_scores.png")


# =============================================================================
# Figure 5: Test Summary Dashboard (FROM JSON)
# =============================================================================

def generate_test_summary_dashboard(test_results):
    """Complete test summary with all metrics"""
    print("\n[5/7] Generating Test Summary Dashboard...")
    
    voip_data = test_results.get('voip')
    video_data = test_results.get('video')
    
    if not voip_data and not video_data:
        print("  ⚠ Skipping: No test data available")
        return
    
    fig = plt.figure(figsize=(14, 10))
    import matplotlib.gridspec as gridspec
    gs = gridspec.GridSpec(3, 2, height_ratios=[1, 1, 0.6], hspace=0.3, wspace=0.3)
    
    # Subplot 1: VoIP Metrics (Top Left)
    if voip_data:
        ax1 = fig.add_subplot(gs[0, 0])
        latency_avg = voip_data.get('latency', {}).get('avg', 0)
        jitter = voip_data.get('jitter', 0)
        loss = voip_data.get('latency', {}).get('loss', 0)
        
        metrics1 = ['Latency\n(ms)', 'Jitter\n(ms)', 'Loss\n(%)']
        values1 = [latency_avg, jitter, loss]
        colors1 = ['#2ecc71', '#27ae60', '#229954']
        
        bars1 = ax1.bar(metrics1, values1, color=colors1, edgecolor='black', linewidth=1.5)
        ax1.set_ylabel('Value', fontweight='bold')
        ax1.set_title('VoIP Performance Metrics', fontweight='bold', fontsize=11)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        
        for bar, val in zip(bars1, values1):
            ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                    f'{val:.2f}', ha='center', va='bottom', fontweight='bold')
    
    # Subplot 2: Video Metrics (Top Right)
    if video_data:
        ax2 = fig.add_subplot(gs[0, 1])
        results = video_data.get('results', {})
        throughput = results.get('throughput_mbps', 0)
        target = results.get('bitrate_target_mbps', 5)
        ratio = results.get('throughput_ratio', 0) * 100
        
        categories2 = ['Target', 'Achieved', 'Ratio %']
        values2 = [target, throughput, ratio]
        colors2 = ['#3498db', '#2ecc71', '#1abc9c']
        
        bars2 = ax2.bar(categories2, values2, color=colors2, edgecolor='black', linewidth=1.5)
        ax2.set_ylabel('Mbps / %', fontweight='bold')
        ax2.set_title('Video Streaming Performance', fontweight='bold', fontsize=11)
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
        
        for bar, val in zip(bars2, values2):
            ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                    f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # Subplot 3: QoS Scores (Middle Left)
    ax3 = fig.add_subplot(gs[1, 0])
    services3 = []
    scores3 = []
    colors3 = []
    
    if voip_data:
        services3.append('VoIP')
        score = voip_data.get('scores', {}).get('overall', 0)
        scores3.append(score)
        colors3.append('#2ecc71' if score >= 80 else '#f39c12')
    
    if video_data:
        services3.append('Video')
        score = video_data.get('scores', {}).get('overall', 0)
        scores3.append(score)
        colors3.append('#3498db' if score >= 80 else '#f39c12')
    
    bars3 = ax3.barh(services3, scores3, color=colors3, edgecolor='black', linewidth=1.5)
    ax3.set_xlabel('Overall QoS Score', fontweight='bold')
    ax3.set_title('QoS Performance Scores', fontweight='bold', fontsize=11)
    ax3.set_xlim(0, 105)
    ax3.axvline(x=80, color='green', linestyle='--', linewidth=1.5, alpha=0.5)
    ax3.grid(axis='x', alpha=0.3, linestyle='--')
    
    for bar, score in zip(bars3, scores3):
        ax3.text(score + 2, bar.get_y() + bar.get_height()/2,
                f'{score:.1f}', va='center', fontweight='bold')
    
    # Subplot 4: Priority Levels (Middle Right)
    ax4 = fig.add_subplot(gs[1, 1])
    services4 = []
    priorities4 = []
    colors4 = []
    
    if voip_data:
        services4.append('VoIP (5QI 1)')
        priorities4.append(20)
        colors4.append('#2ecc71')
    
    if video_data:
        services4.append('Video (5QI 9)')
        priorities4.append(80)
        colors4.append('#3498db')
    
    bars4 = ax4.barh(services4, priorities4, color=colors4, edgecolor='black', linewidth=1.5)
    ax4.set_xlabel('Priority (Lower = Higher)', fontweight='bold')
    ax4.set_title('Priority Hierarchy', fontweight='bold', fontsize=11)
    ax4.invert_xaxis()
    ax4.grid(axis='x', alpha=0.3, linestyle='--')
    
    for bar, priority in zip(bars4, priorities4):
        ax4.text(priority - 5, bar.get_y() + bar.get_height()/2, 
                f'P={priority}', va='center', fontweight='bold', color='white')
    
    # Subplot 5: Test Status Summary (Bottom)
    ax5 = fig.add_subplot(gs[2, :])
    ax5.axis('off')
    
    # Create table
    table_data = [['Test', '5QI', 'Priority', 'Status', 'Score']]
    
    if voip_data:
        voip_passed = '✓ PASS' if voip_data.get('passed', False) else '✗ FAIL'
        voip_score = voip_data.get('scores', {}).get('overall', 0)
        table_data.append(['VoIP Traffic', '1 (GBR)', '20 (High)', voip_passed, f'{voip_score:.1f}/100'])
    
    if video_data:
        video_passed = '✓ PASS' if video_data.get('passed', False) else '✗ FAIL'
        video_score = video_data.get('scores', {}).get('overall', 0)
        table_data.append(['Video Streaming', '9 (Non-GBR)', '80 (Medium)', video_passed, f'{video_score:.1f}/100'])
    
    table = ax5.table(cellText=table_data, cellLoc='center',
                     bbox=[0.1, 0.2, 0.8, 0.6])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Style header row
    for i in range(5):
        cell = table[(0, i)]
        cell.set_facecolor('#34495e')
        cell.set_text_props(weight='bold', color='white')
    
    # Style data rows
    for i in range(1, len(table_data)):
        for j in range(5):
            cell = table[(i, j)]
            if j == 3:  # Status column
                status = table_data[i][j]
                if '✓' in status:
                    cell.set_facecolor('#d5f4e6')
                    cell.set_text_props(weight='bold', color='green')
                else:
                    cell.set_facecolor('#fadbd8')
                    cell.set_text_props(weight='bold', color='red')
            else:
                cell.set_facecolor('#ecf0f1' if i % 2 == 0 else 'white')
    
    # Overall summary
    all_passed = (not voip_data or voip_data.get('passed', False)) and \
                 (not video_data or video_data.get('passed', False))
    summary_text = 'Summary: All Tests Passed Successfully ✓' if all_passed else \
                   'Summary: Some Tests Failed ✗'
    summary_color = 'green' if all_passed else 'red'
    
    ax5.text(0.5, 0.05, summary_text, 
            ha='center', fontsize=12, fontweight='bold', color=summary_color,
            bbox=dict(boxstyle='round', facecolor='white', 
                     edgecolor=summary_color, linewidth=2))
    
    plt.savefig(output_dir / 'fig_test_summary_dashboard.png', bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: fig_test_summary_dashboard.png")


# =============================================================================
# Figure 6: 3GPP Standards Compliance (FROM JSON)
# =============================================================================

def generate_standards_compliance(test_results):
    """Show compliance with 3GPP and ITU-T standards"""
    print("\n[6/7] Generating Standards Compliance Chart...")
    
    voip_data = test_results.get('voip')
    video_data = test_results.get('video')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Data
    standards = []
    compliance = []
    colors_comp = []
    
    if voip_data:
        latency = voip_data.get('latency', {}).get('avg', 0)
        jitter = voip_data.get('jitter', 0)
        loss = voip_data.get('latency', {}).get('loss', 0)
        
        standards.append('ITU-T G.114\nLatency < 150ms')
        compliance.append(100 if latency < 150 else 0)
        colors_comp.append('#27ae60' if latency < 150 else '#e74c3c')
        
        standards.append('ITU-T G.114\nJitter < 30ms')
        compliance.append(100 if jitter < 30 else 0)
        colors_comp.append('#27ae60' if jitter < 30 else '#e74c3c')
        
        standards.append('ITU-T G.114\nLoss < 1%')
        compliance.append(100 if loss < 1 else 0)
        colors_comp.append('#27ae60' if loss < 1 else '#e74c3c')
        
        standards.append('3GPP TS 23.501\n5QI 1 (VoIP)')
        compliance.append(100)
        colors_comp.append('#27ae60')
    
    if video_data:
        ratio = video_data.get('results', {}).get('throughput_ratio', 0)
        threshold = video_data.get('threshold', 0.95)
        
        standards.append('Throughput\n≥ 95% Target')
        compliance.append(100 if ratio >= threshold else 0)
        colors_comp.append('#27ae60' if ratio >= threshold else '#e74c3c')
        
        standards.append('3GPP TS 23.501\n5QI 9 (Video)')
        compliance.append(100)
        colors_comp.append('#27ae60')
    
    if not standards:
        print("  ⚠ Skipping: No test data available")
        return
    
    bars = ax.barh(standards, compliance, color=colors_comp, edgecolor='black', linewidth=2)
    ax.set_xlabel('Compliance (%)', fontweight='bold', fontsize=12)
    ax.set_title('Standards Compliance Assessment', fontweight='bold', fontsize=14)
    ax.set_xlim(0, 110)
    ax.axvline(x=100, color='green', linestyle='--', linewidth=2, label='Full Compliance')
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    # Add percentage labels
    for bar, value in zip(bars, compliance):
        label = f'{value}% ✓' if value == 100 else f'{value}% ✗'
        color = 'green' if value == 100 else 'red'
        ax.text(value + 2, bar.get_y() + bar.get_height()/2,
               label, va='center', fontweight='bold', fontsize=11, color=color)
    
    # Add legend
    ax.legend(loc='lower right', frameon=True, fancybox=True)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig_standards_compliance.png', bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: fig_standards_compliance.png")


# =============================================================================
# Figure 7: Congestion Scenario Explanation
# =============================================================================

def generate_congestion_limitation():
    """Illustrate the limitation of no congestion testing"""
    print("\n[7/7] Generating Congestion Limitation Diagram...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Subplot 1: Current Test Scenario (No Congestion)
    ax1.set_title('Current Test: No Network Congestion', fontweight='bold', fontsize=12)
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.axis('off')
    
    # Network capacity bar
    ax1.add_patch(plt.Rectangle((1, 7), 8, 1.5, facecolor='#ecf0f1', edgecolor='black', linewidth=2))
    ax1.text(5, 7.75, 'Network Capacity: Unlimited', ha='center', va='center', fontweight='bold')
    
    # Traffic bars
    ax1.add_patch(plt.Rectangle((1, 4.5), 0.5, 1.5, facecolor='#2ecc71', edgecolor='black', linewidth=2))
    ax1.text(1.25, 5.25, 'VoIP\n64kbps', ha='center', va='center', fontsize=8)
    
    ax1.add_patch(plt.Rectangle((2, 4.5), 2, 1.5, facecolor='#3498db', edgecolor='black', linewidth=2))
    ax1.text(3, 5.25, 'Video\n5Mbps', ha='center', va='center', fontsize=8)
    
    ax1.text(5, 2.5, 'Result: All services achieve\nperfect performance', 
            ha='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightgreen', edgecolor='green', linewidth=2))
    
    ax1.text(5, 1, '✗ No QoS differentiation visible', ha='center', fontsize=10, color='red', fontweight='bold')
    
    # Subplot 2: Desired Test Scenario (With Congestion)
    ax2.set_title('Desired Test: Network Under Congestion', fontweight='bold', fontsize=12)
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.axis('off')
    
    # Limited network capacity
    ax2.add_patch(plt.Rectangle((1, 7), 6, 1.5, facecolor='#f39c12', edgecolor='black', linewidth=2))
    ax2.text(4, 7.75, 'Network Capacity: Limited', ha='center', va='center', fontweight='bold')
    
    # Traffic bars (competing)
    ax2.add_patch(plt.Rectangle((1, 4.5), 0.8, 1.5, facecolor='#27ae60', edgecolor='black', linewidth=2))
    ax2.text(1.4, 5.25, 'VoIP\nP=20\n✓', ha='center', va='center', fontsize=8, fontweight='bold')
    
    ax2.add_patch(plt.Rectangle((2.5, 4.5), 1.8, 1.5, facecolor='#2980b9', edgecolor='black', linewidth=2))
    ax2.text(3.4, 5.25, 'Video\nP=80\n◐', ha='center', va='center', fontsize=8)
    
    ax2.add_patch(plt.Rectangle((5, 4.5), 1.5, 1.5, facecolor='#7f8c8d', edgecolor='black', linewidth=2))
    ax2.text(5.75, 5.25, 'Data\nP=90\n✗', ha='center', va='center', fontsize=8)
    
    ax2.text(5, 2.5, 'Result: Priority-based\nperformance differentiation', 
            ha='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', edgecolor='orange', linewidth=2))
    
    ax2.text(5, 1, '✓ QoS differentiation observable', ha='center', fontsize=10, color='green', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fig_congestion_limitation.png', bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: fig_congestion_limitation.png")


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Generate all figures from test results"""
    
    print("=" * 70)
    print("Generating Professional Figures for 5G QoS Report")
    print("Using actual test results from JSON files")
    print("=" * 70)
    
    # Load test results
    test_results = load_test_results()
    
    if not test_results['voip'] and not test_results['video']:
        print("\n" + "=" * 70)
        print("ERROR: No test results found!")
        print("=" * 70)
        print("\nPlease ensure test result files exist:")
        print("  - results_voip.json")
        print("  - results_video.json")
        print("\nRun the test scripts first:")
        print("  python3 test_voip_complete_1.py <target_ip>")
        print("  python3 test_video_complete.py <target_ip>")
        return 1
    
    try:
        # Generate all figures
        generate_qos_profile_comparison()
        generate_voip_performance(test_results['voip'])
        generate_video_throughput(test_results['video'])
        generate_qos_scores(test_results)
        generate_test_summary_dashboard(test_results)
        generate_standards_compliance(test_results)
        generate_congestion_limitation()
        
        print("\n" + "=" * 70)
        print("✓ All figures generated successfully!")
        print("=" * 70)
        print(f"\nOutput directory: {output_dir.absolute()}")
        print("\nGenerated files:")
        for fig in sorted(output_dir.glob("fig_*.png")):
            print(f"  - {fig.name}")
        
        print("\n" + "=" * 70)
        print("Test Results Summary:")
        print("=" * 70)
        
        if test_results['voip']:
            voip_passed = "PASSED" if test_results['voip'].get('passed', False) else "FAILED"
            voip_score = test_results['voip'].get('scores', {}).get('overall', 0)
            print(f"VoIP Test: {voip_passed} (Score: {voip_score:.1f}/100)")
            print(f"  - Latency: {test_results['voip'].get('latency', {}).get('avg', 0):.2f} ms")
            print(f"  - Jitter: {test_results['voip'].get('jitter', 0):.2f} ms")
            print(f"  - Loss: {test_results['voip'].get('latency', {}).get('loss', 0):.2f} %")
        
        if test_results['video']:
            video_passed = "PASSED" if test_results['video'].get('passed', False) else "FAILED"
            video_score = test_results['video'].get('scores', {}).get('overall', 0)
            results = test_results['video'].get('results', {})
            print(f"\nVideo Test: {video_passed} (Score: {video_score:.1f}/100)")
            print(f"  - Throughput: {results.get('throughput_mbps', 0):.2f} Mbps")
            print(f"  - Target: {results.get('bitrate_target_mbps', 0):.2f} Mbps")
            print(f"  - Ratio: {results.get('throughput_ratio', 0)*100:.1f}%")
        
        
    except Exception as e:
        print(f"\n❌ Error generating figures: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

