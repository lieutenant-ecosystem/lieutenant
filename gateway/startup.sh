#!/bin/bash

# Create user with a home directory and set a default shell
adduser --disabled-password --shell /bin/bash --gecos "" "$SSH_USERNAME"

# Set up SSH directory and authorized keys
mkdir -p "/home/$SSH_USERNAME/.ssh"
echo "$SSH_PUBLIC_KEY" > "/home/$SSH_USERNAME/.ssh/authorized_keys"
chown -R "$SSH_USERNAME:$SSH_USERNAME" "/home/$SSH_USERNAME/.ssh"
chmod 700 "/home/$SSH_USERNAME/.ssh"
chmod 600 "/home/$SSH_USERNAME/.ssh/authorized_keys"

# Install Cloudflared Service
cloudflared service uninstall || true
cloudflared service install "$CLOUDFLARE_TUNNEL_TOKEN"

mkdir -p /run/sshd
chmod 755 /run/sshd

/usr/sbin/sshd -D