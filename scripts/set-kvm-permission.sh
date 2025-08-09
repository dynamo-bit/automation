#!/bin/bash
set -e

sudo usermod -aG kvm $USER
newgrp kvm  
ls -l /dev/kvm
echo "Permissions set."

