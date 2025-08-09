#!/bin/bash
set -e

if command -v golemsp &> /dev/null; then
  echo "[INFO] Golem is already installed. Skipping installation."
else
  echo "[INFO] Installing Golem provider..."
  expect << 'EXPECT_SCRIPT'
#!/usr/bin/expect -f

set timeout -1

spawn bash -c "curl -sSf https://join.golem.network/as-provider | bash -"

expect {
  -re ".*Do you accept the terms and conditions.*" {
    send "yes\r"
    exp_continue
  }
  -re ".*Do you agree to augment stats.golem.network.*" {
    send "allow\r"
    exp_continue
  }
  -re ".*Node name.*" {
    send "idle-finance-node\r"
    exp_continue
  }
  -re ".*Ethereum mainnet wallet address.*" {
    send "0x44dE4219e25BeEfF3561c2858c5dde8771D5BC97\r"
    exp_continue
  }
  -re ".*Price GLM per hour.*" {
    send "0.025\r"
    exp_continue
  }
  eof
}
EXPECT_SCRIPT
fi

echo "[INFO] Golem installation complete."
