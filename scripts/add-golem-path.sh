#!/bin/bash
set -e

echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

echo "Golem path added to ~/.bashrc"




# curl -sSL https://github.com/skillDeCoder/idle-finance-v2/blob/main/automation/golem/scripts/install-golem.sh  | bash


# curl -sSL https://raw.githubusercontent.com/skillDeCoder/idle-finance-v2/main/automation/golem/scripts/install-golem.sh | bash


# https://raw.githubusercontent.com/skillDeCoder/idle-finance-v2/main/automation/golem/scripts/hello-world.sh

# https://github.com/skillDeCoder/idle-finance-v2/blob/main/automation/golem/scripts/hello-world.sh





curl -sSL https://raw.githubusercontent.com/skillDeCoder/idle-finance-v2/main/automation/golem/scripts/hello-world.sh  | bash