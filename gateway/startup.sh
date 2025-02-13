#!/bin/sh

# Create user with a home directory and set a default shell
if ! id "$SSH_USERNAME" &>/dev/null; then
  echo "$SSH_USERNAME does not exist. Creating user."
  adduser --disabled-password --shell /bin/bash --gecos "" "$SSH_USERNAME"

  # Set up SSH directory and authorized keys
  mkdir -p "/home/$SSH_USERNAME/.ssh"
  echo "$SSH_PUBLIC_KEY" > "/home/$SSH_USERNAME/.ssh/authorized_keys"
  chown -R "$SSH_USERNAME:$SSH_USERNAME" "/home/$SSH_USERNAME/.ssh"
  chmod 700 "/home/$SSH_USERNAME/.ssh"
  chmod 600 "/home/$SSH_USERNAME/.ssh/authorized_keys"
else
  echo "User $SSH_USERNAME already exists. Skipping user creation."
fi

echo "Starting the SSH service"
service ssh start

echo "Stopping the Cloudflare Tunnel"
cloudflared service uninstall > /dev/null 2>&1 || true

echo "Setting Cloudflared's log level to DEBUG"
export CF_TUNNEL_LOGLEVEL=debug

echo "Starting the Cloudflare Tunnel"
cloudflared service install "$CLOUDFLARE_TUNNEL_TOKEN"
echo "Cloudflare Tunnel started successfully"

tail -f /var/log/cloudflared.log