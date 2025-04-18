#!/bin/sh

# Update package list and install SSH server and necessary packages
apt update
apt install -y openssh-server adduser curl

# Create the privilege separation directory
mkdir -p /run/sshd
chmod 755 /run/sshd

# Configure SSH (generate host keys and modify sshd_config)
ssh-keygen -A
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config

# Download and install the cloudflared Debian package
# TODO: This should ideally be a different tag
ARCHITECTURE=$(if [ "$(arch)" = "aarch64" ]; then echo "arm64"; else echo "amd64"; fi)
curl -L --output cloudflared.deb "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$ARCHITECTURE.deb"
dpkg -i cloudflared.deb
rm -f cloudflared.deb

# Clean up and ensure any dependencies are installed
apt install -f