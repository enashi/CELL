#!/bin/bash
#
# Bandwidth Limiting Helper Script
# Easy management of tc (traffic control) rules for congestion testing
#

set -e

# Auto-detect interface function
detect_interface() {
    # Priority 1: ogstun (Open5GS)
    if ip link show ogstun &>/dev/null; then
        echo "ogstun"
        return
    fi
    
    # Priority 2: Docker bridges with 5GC traffic (br-*)
    for iface in $(ip link show | grep -oP 'br-[a-f0-9]+' | head -1); do
        if [ -n "$iface" ]; then
            # Check if it has 192.168.70.x (common 5GC subnet)
            if ip addr show "$iface" | grep -q '192.168.70'; then
                echo "$iface"
                return
            fi
        fi
    done
    
    # Priority 3: First Docker bridge
    local first_bridge=$(ip link show | grep -oP 'br-[a-f0-9]+' | head -1)
    if [ -n "$first_bridge" ]; then
        echo "$first_bridge"
        return
    fi
    
    # Priority 4: uesimtun0 (UERANSIM)
    if ip link show uesimtun0 &>/dev/null; then
        echo "uesimtun0"
        return
    fi
    
    # Priority 5: First physical interface (eth*, enp*, ens*)
    for prefix in eth enp ens wlan; do
        local iface=$(ip link show | grep -oP "${prefix}[0-9a-z]+" | head -1)
        if [ -n "$iface" ]; then
            echo "$iface"
            return
        fi
    done
    
    # Fallback
    echo ""
}

# Configuration
if [ -z "$INTERFACE" ]; then
    DEFAULT_INTERFACE=$(detect_interface)
    if [ -z "$DEFAULT_INTERFACE" ]; then
        DEFAULT_INTERFACE="ogstun"
        echo "Warning: Could not auto-detect interface, using default: $DEFAULT_INTERFACE"
    else
        echo "Auto-detected interface: $DEFAULT_INTERFACE"
    fi
else
    DEFAULT_INTERFACE="$INTERFACE"
fi

INTERFACE="${INTERFACE:-$DEFAULT_INTERFACE}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Error: This script must be run as root${NC}"
        echo "Use: sudo $0 $@"
        exit 1
    fi
}

# Show usage
show_usage() {
    cat << EOF
Bandwidth Limiting Helper Script

Usage: $0 <command> [options]

Commands:
    set <rate>      Apply bandwidth limit (rate in Mbps)
    remove          Remove all bandwidth limits
    show            Show current configuration
    test            Test with multiple limits
    stats           Show statistics
    
Options:
    --interface <if>    Network interface (default: $DEFAULT_INTERFACE)
    
Examples:
    $0 set 10                    # Limit to 10 Mbps
    $0 set 50 --interface eth0   # Limit eth0 to 50 Mbps
    $0 remove                    # Remove all limits
    $0 show                      # Show current config
    $0 test                      # Test multiple limits
    
Notes:
    - Requires root permissions
    - Uses tc (traffic control) with TBF qdisc
    - Limits apply to egress (outgoing) traffic only

EOF
}

# Apply bandwidth limit
set_limit() {
    local rate_mbps=$1
    
    if [ -z "$rate_mbps" ]; then
        echo -e "${RED}Error: Rate not specified${NC}"
        echo "Usage: $0 set <rate_mbps>"
        exit 1
    fi
    
    # Validate rate is a number
    if ! [[ "$rate_mbps" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}Error: Rate must be a number${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Applying bandwidth limit...${NC}"
    echo "  Interface: $INTERFACE"
    echo "  Rate: ${rate_mbps} Mbps"
    
    # Remove existing qdisc if any
    tc qdisc del dev "$INTERFACE" root 2>/dev/null || true
    
    # Calculate burst (10ms worth of traffic, minimum 10KB)
    burst_kb=$(( rate_mbps * 1000 / 8 / 100 ))
    if [ $burst_kb -lt 10 ]; then
        burst_kb=10
    fi
    
    # Apply TBF (Token Bucket Filter)
    if tc qdisc add dev "$INTERFACE" root tbf rate "${rate_mbps}mbit" burst "${burst_kb}kb" latency 50ms; then
        echo -e "${GREEN}✓ Bandwidth limit applied successfully${NC}"
        echo ""
        show_config
    else
        echo -e "${RED}✗ Failed to apply bandwidth limit${NC}"
        exit 1
    fi
}

# Remove bandwidth limit
remove_limit() {
    echo -e "${YELLOW}Removing bandwidth limit...${NC}"
    echo "  Interface: $INTERFACE"
    
    if tc qdisc del dev "$INTERFACE" root 2>/dev/null; then
        echo -e "${GREEN}✓ Bandwidth limit removed${NC}"
    else
        echo -e "${YELLOW}No bandwidth limit was configured${NC}"
    fi
}

# Show current configuration
show_config() {
    echo -e "${YELLOW}Current configuration for $INTERFACE:${NC}"
    tc qdisc show dev "$INTERFACE"
}

# Show statistics
show_stats() {
    echo -e "${YELLOW}Statistics for $INTERFACE:${NC}"
    tc -s qdisc show dev "$INTERFACE"
}

# Test multiple bandwidth limits
test_limits() {
    local test_rates=(100 50 20 10 5)
    
    echo -e "${YELLOW}Testing multiple bandwidth limits${NC}"
    echo "Interface: $INTERFACE"
    echo "Test rates: ${test_rates[@]} Mbps"
    echo ""
    
    for rate in "${test_rates[@]}"; do
        echo "Testing $rate Mbps..."
        set_limit "$rate"
        
        echo "Limit active. Press ENTER to continue to next rate..."
        read -r
    done
    
    echo -e "${YELLOW}Tests complete. Removing limit...${NC}"
    remove_limit
}

# Check if interface exists
check_interface() {
    if ! ip link show "$INTERFACE" &>/dev/null; then
        echo -e "${RED}Error: Interface $INTERFACE not found${NC}"
        echo ""
        echo "Available interfaces:"
        ip link show | grep '^[0-9]' | awk -F': ' '{print "  - " $2}'
        exit 1
    fi
}

# Main script
main() {
    # Parse interface option
    while [[ $# -gt 0 ]]; do
        case $1 in
            --interface)
                INTERFACE="$2"
                shift 2
                ;;
            *)
                break
                ;;
        esac
    done
    
    # Get command
    command=${1:-help}
    shift || true
    
    case "$command" in
        set)
            check_root
            check_interface
            set_limit "$@"
            ;;
        
        remove)
            check_root
            check_interface
            remove_limit
            ;;
        
        show)
            check_interface
            show_config
            ;;
        
        stats)
            check_interface
            show_stats
            ;;
        
        test)
            check_root
            check_interface
            test_limits
            ;;
        
        help|--help|-h)
            show_usage
            ;;
        
        *)
            echo -e "${RED}Error: Unknown command '$command'${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
