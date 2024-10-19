#!/bin/sh

# Update package list and install SSH server and necessary packages
apt update
apt install -y openssh-server adduser curl

# Configure SSH (generate host keys and modify sshd_config)
ssh-keygen -A
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config

# Enable and start the SSH service
systemctl enable ssh
systemctl start ssh

# Create user with a home directory and set a default shell
adduser --disabled-password --shell /bin/bash --gecos "" "$SSH_USERNAME"

# Set up SSH directory and authorized keys
mkdir -p "/home/$SSH_USERNAME/.ssh"
echo "$SSH_PUBLIC_KEY" > "/home/$SSH_USERNAME/.ssh/authorized_keys"
chown -R "$SSH_USERNAME:$SSH_USERNAME" "/home/$SSH_USERNAME/.ssh"
chmod 700 "/home/$SSH_USERNAME/.ssh"
chmod 600 "/home/$SSH_USERNAME/.ssh/authorized_keys"

# Create the privilege separation directory
mkdir -p /run/sshd
chmod 755 /run/sshd

# Download and install the cloudflared Debian package
curl -L --output cloudflared.deb "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb"
dpkg -i cloudflared.deb
rm -f cloudflared.deb
cloudflared service install "$CLOUDFLARE_TUNNEL_TOKEN"
systemctl enable cloudflared
systemctl start cloudflared

# Clean up and ensure any dependencies are installed
apt install -f