#!/bin/bash

set -o pipefail
set -o errexit
set -o nounset

# APN="internet.telekom"
# WWAN_IFACE="wwan0"

# Read configuration parameters from command line arguments or environment variables
readonly APN=${1:-$APN}
readonly WWAN_IFACE=${2:-$WWAN_IFACE}

# Exit if not all parameters are set
if [[ -z "$APN" || -z "$WWAN_IFACE" ]]; then
    echo "Usage: $0 <apn> <wwan_iface>"
    echo "Or set APN, and WWAN_IFACE environment variables."
    exit 1
fi

main() {

    echo "=== LTE Connect Script ==="

    # Check if we already have a connection
    if check_connection; then
        echo "Already connected, exiting"
        exit 0
    fi

    if ! wait_for_modem_hardware; then
        echo "Failed to detect modem, trying to restart ModemManager"
        restart_modemmanager
        if ! wait_for_modem_hardware; then
            echo "Modem detection failed after ModemManager restart, exiting"
            exit 1
        fi
    fi

    echo "Trying simple-connect"
    if connect_bearer && set_up_network_interface && check_connection; then
        echo "Connection successful, exiting"
        exit 0
    fi

    echo "Simple-connect failed, resetting modem"
    reset_modem
    if ! wait_for_modem_reset; then
        echo "Reset failed"
        mmcli -m any
        exit 1
    fi
    
    if ! wait_for_modem_hardware; then
        echo "Modem failed to register with the OS after reset"
        mmcli -m any
        exit 1
    fi

    if ! wait_for_modem_ready; then
        echo "Modem failed to get ready"
        mmcli -m any
        exit 1
    fi

    if connect_bearer && set_up_network_interface && check_connection; then
        echo "Connection successful, exiting"
        exit 0
    else
        echo "Connection finally failed, exiting"
        mmcli -m any
        exit 1
    fi
}

check_connection() {
    echo "Checking connection on $WWAN_IFACE"
    if ping -c 3 -w 1 -i 0.2 -I $WWAN_IFACE 1.1.1.1 >/dev/null; then
        echo "Connection check successful! ✅"
        return 0
    else
        echo "Connection check failed! ❌"
        return 1
    fi
}

wait_for_modem_hardware() {
    echo "Waiting for ModemManager to pick up modem (timeout 90s)"
    mmcli -S
    for i in {1..45}; do
        echo "Checking for modem (attempt $i)..."
        if mmcli -m any &>/dev/null; then
            echo "Modem detected."
            return 0
        fi
        sleep 2
    done
    echo "Modem not detected. Giving up."
    return 1
}

wait_for_modem_reset() {
    echo "Waiting for modem to reset (timeout 20s)"
    for i in {1..10}; do
        if ! mmcli -m any &>/dev/null; then
            echo "Modem reset"
            return 0
        fi
        sleep 2
    done
    echo "Modem did not react to reset command"
    return 1
}

wait_for_modem_ready() {
    # Wait for the modem to be ready
    for i in {1..10}; do
        local state=$(get_modem_state)
        echo "Current modem state: $state"
        if [[ "$state" == "registered" || "$state" == "enabled" || "$state" == "connected" ]]; then
            echo "Modem is ready."
            return 0
        fi
        sleep 2
    done
    echo "Modem is not ready. Giving up."
    return 1
}

wait_for_modem_connected() {
    # Wait for the modem to be connected
    for i in {1..30}; do
        local state=$(get_modem_state)
        echo "Current modem state: $state"
        if [ "$state" == "connected" ]; then
            echo "Modem is registered to network. ✅"
            return 0
        fi
        sleep 2
    done
    echo "Modem failed to connect. Giving up."
    return 1
}

reset_modem() {
    local at_port=$(get_modem_at_port)
    echo "Resetting modem via AT command on $at_port"
    echo -ne 'AT&F\r\n' > $at_port
    if [[ $? -ne 0 ]]; then
        echo "Failed to send reset command to modem, exiting"
        exit 1
    fi
}

restart_modemmanager() {
    echo "Restarting ModemManager service"
    systemctl restart ModemManager.service
    if [[ $? -ne 0 ]]; then
        echo "Failed to restart ModemManager service, exiting"
        exit 1
    fi
}

is_mbim_driver_active() {
    mmcli -m any -J | jq -e '.modem.generic.drivers[] | select(. == "cdc_mbim")' >/dev/null 2>&1
}

get_usb_id() {
    mmcli -m any -J | jq -r '.modem.generic.device' | grep -Po '[0-9\-]+$'
    if [[ $? -ne 0 ]]; then
        echo "USB ID lookup failed, exiting"
        exit 1
    fi
}

get_modem_id() {
    mmcli -m any -J | jq -r '.modem."dbus-path"' | grep -Po '\d+$'
    if [[ $? -ne 0 ]]; then
        echo "Modem ID lookup failed, exiting"
        exit 1
    fi
}

get_modem_state() {
    mmcli -m any -J | jq -r '.modem.generic.state'
    if [[ $? -ne 0 ]]; then
        echo "Modem state lookup failed, exiting"
        exit 1
    fi
}

get_modem_at_port() {
    # We need to use the secondary at port if there are multiple, because the first one is often already in use
    local device_name
    device_name=$(mmcli -m any -J | jq -r '[.modem.generic.ports[] | select(contains("at"))] | sort | .[-1]' | grep -Po '^\w+')
    if [[ $? -ne 0 ]]; then
        echo "AT serial device lookup failed, exiting"
        exit 1
    fi
    echo "/dev/$device_name"
}

connect_bearer() {
    local modem_id=$(get_modem_id)
    echo "Connecting to APN $APN on modem $modem_id..."
    if ! mmcli -m $modem_id --simple-connect="apn=$APN,ip-type=ipv4,allow-roaming=true"; then
        echo "Failed to connect modem"
        return 1
    fi

    if wait_for_modem_connected; then
        echo "Modem connected"
        return 0
    else
        echo "Modem not connected"
        return 1
    fi
}

set_up_network_interface() {
    echo "Setting up network interface"

    # Fetch modem info
    local modem_id=$(get_modem_id)

    echo "Using modem with ID $modem_id"
    mmcli -m $modem_id

    # Fetch bearer info
    local bearer_id=$( mmcli -m $modem_id -J | jq -r '.modem.generic.bearers[0]' | grep -Po '\d+$' )

    echo "Using bearer with ID $bearer_id"
    mmcli -b $bearer_id

    local bearer_ip=$( mmcli -b $bearer_id -J | jq -r '.bearer."ipv4-config".address' )
    local bearer_gw=$( mmcli -b $bearer_id -J | jq -r '.bearer."ipv4-config".gateway' )
    local bearer_ip_prefix=$( mmcli -b $bearer_id -J | jq -r '.bearer."ipv4-config".prefix' )
    local bearer_dns=$( mmcli -b $bearer_id -J | jq -r '.bearer."ipv4-config".dns | join (" ")' )

    echo "Using IP info from bearer:"
    echo "BEARER_IP: $bearer_ip"
    echo "BEARER_GW: $bearer_gw"
    echo "BEARER_IP_PREFIX: $bearer_ip_prefix"
    echo "BEARER_DNS: $bearer_dns"

    if [[ -z "$bearer_ip" || -z "$bearer_gw" || -z "$bearer_ip_prefix" || -z "$bearer_dns" ]]; then
        echo "No valid IP info — aborting. ❌"
        return 1
    fi

    echo "Setting up $WWAN_IFACE..."

    # Configure interface
    ip addr flush dev $WWAN_IFACE
    ip link set $WWAN_IFACE up
    ip addr add $bearer_ip/$bearer_ip_prefix dev $WWAN_IFACE

    echo "Setting DNS servers"
    resolvectl dns $WWAN_IFACE $bearer_dns

    echo "Setting default IP route"
    ip route add default via $bearer_gw metric 500

    echo "Network interface configuration done"

    return 0
}

main