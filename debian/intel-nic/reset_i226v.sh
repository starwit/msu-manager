#!/bin/bash
echo "Resetting Intel I226-V NIC"
intel_id=$(lspci | grep I226-V | awk '{print $1}')
device_path=$(ls -d /sys/bus/pci/devices/* | grep ${intel_id})
echo 1 > ${device_path}/remove
sleep 5
echo 1 > /sys/bus/pci/rescan