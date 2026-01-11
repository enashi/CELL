#!/usr/bin/env python3
"""
Results Analysis Script - Simplified Version (No Version Conflicts)

Analyzes test results from VoIP and Video tests.
Generates statistics and simple visualizations without complex dependencies.
"""

import json
import glob
import sys
from pathlib import Path
from datetime import datetime

# Simple statistics without numpy/scipy
def mean(values):
    """Calculate mean"""
    return sum(values) / len(values) if values else 0

def median(values):
    """Calculate median"""
    if not values:
        return 0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
    return sorted_values[n//2]

def stdev(values):
    """Calculate standard deviation"""
    if len(values) < 2:
        return 0
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5


# =============================================================================
# RESULT LOADING
# =============================================================================

def load_results(results_dir='./'):
    """Load all test results from JSON files"""
    print(f"Loading results from {results_dir}")
    
    results = {
        'voip': [],
        'video': [],
        'all': []
    }
    
    # Load VoIP results
    voip_files = list(Path(results_dir).glob('*voip*.json'))
    for result_file in voip_files:
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
                data['filename'] = result_file.name
                results['voip'].append(data)
                results['all'].append(data)
                print(f"  ✓ Loaded {result_file.name}")
        except Exception as e:
            print(f"  ✗ Error loading {result_file.name}: {e}")
    
    # Load Video results
    video_files = list(Path(results_dir).glob('*video*.json'))
    for result_file in video_files:
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
                data['filename'] = result_file.name
                results['video'].append(data)
                results['all'].append(data)
                print(f"  ✓ Loaded {result_file.name}")
        except Exception as e:
            print(f"  ✗ Error loading {result_file.name}: {e}")
    
    print(f"\nFound:")
    print(f"  VoIP tests: {len(results['voip'])}")
    print(f"  Video tests: {len(results['video'])}")
    print(f"  Total: {len(results['all'])}")
    
    return results


# =============================================================================
# VOIP ANALYSIS
# =============================================================================

def analyze_voip_results(voip_data):
    """Analyze VoIP test results"""
    if not voip_data:
        print("No VoIP results to analyze")
        return None
    
    print("\n" + "=" * 70)
    print("VoIP Performance Analysis")
    print("=" * 70)
    
    # Extract metrics
    latencies = []
    jitters = []
    losses = []
    passed_tests = 0
    
    for test in voip_data:
        latency = test.get('latency', {})
        latencies.append(latency.get('avg', 0))
        jitters.append(test.get('jitter', 0))
        losses.append(latency.get('loss', 0))
        if test.get('passed', False):
            passed_tests += 1
    
    # Calculate statistics
    print(f"\nLatency Statistics:")
    print(f"  Mean: {mean(latencies):.2f}ms")
    print(f"  Median: {median(latencies):.2f}ms")
    print(f"  Min: {min(latencies):.2f}ms")
    print(f"  Max: {max(latencies):.2f}ms")
    print(f"  Std Dev: {stdev(latencies):.2f}ms")
    
    print(f"\nJitter Statistics:")
    print(f"  Mean: {mean(jitters):.2f}ms")
    print(f"  Median: {median(jitters):.2f}ms")
    print(f"  Min: {min(jitters):.2f}ms")
    print(f"  Max: {max(jitters):.2f}ms")
    
    print(f"\nPacket Loss Statistics:")
    print(f"  Mean: {mean(losses):.2f}%")
    print(f"  Max: {max(losses):.2f}%")
    
    print(f"\nTest Results:")
    print(f"  Passed: {passed_tests}/{len(voip_data)}")
    print(f"  Success Rate: {passed_tests/len(voip_data)*100:.1f}%")
    
    # ITU-T G.114 thresholds
    print(f"\nITU-T G.114 Compliance:")
    latency_compliant = sum(1 for l in latencies if l <= 150)
    print(f"  Latency < 150ms: {latency_compliant}/{len(latencies)} "
          f"({latency_compliant/len(latencies)*100:.1f}%)")
    
    jitter_compliant = sum(1 for j in jitters if j <= 30)
    print(f"  Jitter < 30ms: {jitter_compliant}/{len(jitters)} "
          f"({jitter_compliant/len(jitters)*100:.1f}%)")
    
    return {
        'latencies': latencies,
        'jitters': jitters,
        'losses': losses,
        'passed': passed_tests,
        'total': len(voip_data),
        'stats': {
            'latency_mean': mean(latencies),
            'latency_median': median(latencies),
            'jitter_mean': mean(jitters),
            'loss_mean': mean(losses)
        }
    }


# =============================================================================
# VIDEO ANALYSIS
# =============================================================================

def analyze_video_results(video_data):
    """Analyze video streaming test results"""
    if not video_data:
        print("No video results to analyze")
        return None
    
    print("\n" + "=" * 70)
    print("Video Streaming Performance Analysis")
    print("=" * 70)
    
    # Extract metrics
    throughputs = []
    targets = []
    ratios = []
    losses = []
    passed_tests = 0
    
    for test in video_data:
        results = test.get('results', {})
        throughputs.append(results.get('throughput_mbps', 0))
        targets.append(results.get('bitrate_target_mbps', 0))
        ratios.append(results.get('throughput_ratio', 0))
        losses.append(results.get('loss_percent', 0))
        if test.get('passed', False):
            passed_tests += 1
    
    # Calculate statistics
    print(f"\nThroughput Statistics:")
    print(f"  Mean: {mean(throughputs):.2f} Mbps")
    print(f"  Median: {median(throughputs):.2f} Mbps")
    print(f"  Min: {min(throughputs):.2f} Mbps")
    print(f"  Max: {max(throughputs):.2f} Mbps")
    
    print(f"\nTarget vs Achieved:")
    print(f"  Mean Target: {mean(targets):.2f} Mbps")
    print(f"  Mean Achieved: {mean(throughputs):.2f} Mbps")
    print(f"  Mean Ratio: {mean(ratios)*100:.1f}%")
    
    if losses and any(l > 0 for l in losses):
        print(f"\nPacket Loss:")
        print(f"  Mean: {mean(losses):.2f}%")
        print(f"  Max: {max(losses):.2f}%")
    
    print(f"\nTest Results:")
    print(f"  Passed: {passed_tests}/{len(video_data)}")
    print(f"  Success Rate: {passed_tests/len(video_data)*100:.1f}%")
    
    # Quality assessment
    print(f"\nQuality Assessment:")
    excellent = sum(1 for r in ratios if r >= 0.98)
    good = sum(1 for r in ratios if 0.95 <= r < 0.98)
    acceptable = sum(1 for r in ratios if 0.90 <= r < 0.95)
    poor = sum(1 for r in ratios if r < 0.90)
    
    print(f"  Excellent (≥98%): {excellent}/{len(ratios)}")
    print(f"  Good (95-98%): {good}/{len(ratios)}")
    print(f"  Acceptable (90-95%): {acceptable}/{len(ratios)}")
    print(f"  Poor (<90%): {poor}/{len(ratios)}")
    
    return {
        'throughputs': throughputs,
        'targets': targets,
        'ratios': ratios,
        'losses': losses,
        'passed': passed_tests,
        'total': len(video_data),
        'stats': {
            'throughput_mean': mean(throughputs),
            'ratio_mean': mean(ratios),
            'loss_mean': mean(losses)
        }
    }


# =============================================================================
# QOS COMPARISON
# =============================================================================

def compare_qos_classes(results):
    """Compare performance across different QoS classes"""
    print("\n" + "=" * 70)
    print("QoS Class Comparison")
    print("=" * 70)
    
    voip_data = results.get('voip', [])
    video_data = results.get('video', [])
    
    if not voip_data and not video_data:
        print("Not enough data for comparison")
        return
    
    print(f"\nTest Distribution:")
    print(f"  VoIP tests: {len(voip_data)}")
    print(f"  Video tests: {len(video_data)}")
    
    # Compare pass rates
    if voip_data:
        voip_passed = sum(1 for t in voip_data if t.get('passed', False))
        voip_rate = voip_passed / len(voip_data) * 100
        print(f"\nVoIP Success Rate: {voip_rate:.1f}%")
    
    if video_data:
        video_passed = sum(1 for t in video_data if t.get('passed', False))
        video_rate = video_passed / len(video_data) * 100
        print(f"Video Success Rate: {video_rate:.1f}%")
    
    # Compare QoS scores
    if voip_data and any('scores' in t for t in voip_data):
        voip_scores = [t.get('scores', {}).get('overall', 0) for t in voip_data]
        print(f"\nVoIP Mean QoS Score: {mean(voip_scores):.1f}/100")
    
    if video_data and any('scores' in t for t in video_data):
        video_scores = [t.get('scores', {}).get('overall', 0) for t in video_data]
        print(f"Video Mean QoS Score: {mean(video_scores):.1f}/100")


# =============================================================================
# TEXT REPORT
# =============================================================================

def generate_text_report(results, voip_analysis, video_analysis, output_file='report.txt'):
    """Generate text-based report"""
    print(f"\n" + "=" * 70)
    print(f"Generating Text Report")
    print("=" * 70)
    
    with open(output_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("5G QoS Test Results Report\n")
        f.write("=" * 70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Executive Summary
        f.write("EXECUTIVE SUMMARY\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total Tests: {len(results['all'])}\n")
        f.write(f"VoIP Tests: {len(results['voip'])}\n")
        f.write(f"Video Tests: {len(results['video'])}\n\n")
        
        # VoIP Results
        if voip_analysis:
            f.write("\nVOIP TEST RESULTS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Tests Run: {voip_analysis['total']}\n")
            f.write(f"Tests Passed: {voip_analysis['passed']}\n")
            f.write(f"Success Rate: {voip_analysis['passed']/voip_analysis['total']*100:.1f}%\n\n")
            
            stats = voip_analysis['stats']
            f.write("Performance Metrics:\n")
            f.write(f"  Latency (avg): {stats['latency_mean']:.2f}ms\n")
            f.write(f"  Jitter (avg): {stats['jitter_mean']:.2f}ms\n")
            f.write(f"  Loss (avg): {stats['loss_mean']:.2f}%\n\n")
        
        # Video Results
        if video_analysis:
            f.write("\nVIDEO TEST RESULTS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Tests Run: {video_analysis['total']}\n")
            f.write(f"Tests Passed: {video_analysis['passed']}\n")
            f.write(f"Success Rate: {video_analysis['passed']/video_analysis['total']*100:.1f}%\n\n")
            
            stats = video_analysis['stats']
            f.write("Performance Metrics:\n")
            f.write(f"  Throughput (avg): {stats['throughput_mean']:.2f} Mbps\n")
            f.write(f"  Ratio (avg): {stats['ratio_mean']*100:.1f}%\n")
            f.write(f"  Loss (avg): {stats['loss_mean']:.2f}%\n\n")
        
        # Detailed Results
        f.write("\nDETAILED RESULTS\n")
        f.write("-" * 70 + "\n\n")
        
        # VoIP Details
        if results['voip']:
            f.write("VoIP Tests:\n")
            for i, test in enumerate(results['voip'], 1):
                f.write(f"\n  Test {i}:\n")
                f.write(f"    File: {test.get('filename', 'unknown')}\n")
                f.write(f"    Timestamp: {test.get('timestamp_readable', 'N/A')}\n")
                latency = test.get('latency', {})
                f.write(f"    Latency: {latency.get('avg', 0):.2f}ms\n")
                f.write(f"    Jitter: {test.get('jitter', 0):.2f}ms\n")
                f.write(f"    Loss: {latency.get('loss', 0):.2f}%\n")
                f.write(f"    Result: {'PASS' if test.get('passed', False) else 'FAIL'}\n")
        
        # Video Details
        if results['video']:
            f.write("\nVideo Tests:\n")
            for i, test in enumerate(results['video'], 1):
                f.write(f"\n  Test {i}:\n")
                f.write(f"    File: {test.get('filename', 'unknown')}\n")
                f.write(f"    Timestamp: {test.get('timestamp_readable', 'N/A')}\n")
                res = test.get('results', {})
                f.write(f"    Target: {res.get('bitrate_target_mbps', 0):.2f} Mbps\n")
                f.write(f"    Achieved: {res.get('throughput_mbps', 0):.2f} Mbps\n")
                f.write(f"    Ratio: {res.get('throughput_ratio', 0)*100:.1f}%\n")
                f.write(f"    Result: {'PASS' if test.get('passed', False) else 'FAIL'}\n")
    
    print(f"  ✓ Report saved to {output_file}")
    print(f"\nView with: cat {output_file}")


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Main analysis function"""
    print("=" * 70)
    print("5G QoS Test Results Analysis (Simplified)")
    print("=" * 70)
    
    # Load results
    results = load_results()
    
    if not results['all']:
        print("\n❌ No results found. Please run tests first:")
        print("  python3 test_voip_complete.py <target_ip>")
        print("  python3 test_video_complete.py <target_ip>")
        return 1
    
    # Analyze by type
    voip_analysis = analyze_voip_results(results['voip'])
    video_analysis = analyze_video_results(results['video'])
    
    # Compare QoS classes
    if len(results['all']) > 1:
        compare_qos_classes(results)
    
    # Generate text report
    generate_text_report(results, voip_analysis, video_analysis)
    
    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)
    print("\nGenerated files:")
    print("  - report.txt (text report)")
    print("\nNext steps:")
    print("  1. View report: cat report.txt")
    print("  2. Use statistics in your thesis")
    print("  3. Create graphs manually if needed")
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

