#!/bin/bash
set -e

echo "[INFO] Checking for KVM..."
if ! command -v kvm-ok &> /dev/null; then
  echo "[INFO] Installing KVM..."
  sudo apt update
  sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils
  sudo usermod -aG kvm $USER
  newgrp kvm  
  ls -l /dev/kvm
  echo "KVM installed."
else
  echo "KVM already installed."
fi 