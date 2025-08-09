#!/bin/bash

set -e

VM_NAME=${1:-idle-finance}

echo "[INFO] Step 1: Check for multipass"
# Step 1: Check for multipass
if ! command -v multipass &> /dev/null; then
  echo "[INFO] Multipass not found. Installing..."
  sudo snap install multipass --classic
else
  echo "[INFO] Multipass is already installed."
fi

echo "[INFO] Step 2: Launch VM if not exists"
# Step 2: Launch VM if not exists
if multipass list | grep -q "$VM_NAME"; then
  echo "[INFO] VM '$VM_NAME' already exists."
else
  echo "[INFO] Launching VM '$VM_NAME'..."
  multipass launch 22.04 \
    --name "$VM_NAME" \
    --cpus 2 \
    --memory 2G \
    --disk 10G \
    --cloud-init - <<EOF
#cloud-config
users:
  - name: depin
    groups: sudo
    home: /home/depin
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    lock_passwd: false
    password: $VM_NAME

packages:
  - curl
  - expect

runcmd:
  - echo "[INFO] Creating /home/depin directory"
  - mkdir -p /home/depin
  - chown -R depin:depin /home/depin
  - chmod -R 755 /home/depin
  - echo "[INFO] Setting up auto-switch to depin user on login"
  - echo "exec sudo -u depin -i" >> /home/ubuntu/.bashrc
EOF
fi

echo "[INFO] VM '$VM_NAME' provisioned successfully."
echo "[INFO] Use the API endpoint /copy-install-scripts/{vm_name} to copy install scripts."