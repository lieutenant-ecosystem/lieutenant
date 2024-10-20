FROM ubuntu:latest

ARG SSH_USERNAME
ARG SSH_PUBLIC_KEY
ARG CLOUDFLARE_TUNNEL_TOKEN
ENV SSH_USERNAME=${SSH_USERNAME} \
    SSH_PUBLIC_KEY=${SSH_PUBLIC_KEY} \
    CLOUDFLARE_TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}

COPY setup.sh /setup.sh
RUN chmod +x /setup.sh
RUN /setup.sh
RUN rm /setup.sh

COPY startup.sh /startup.sh
RUN chmod +x /startup.sh
CMD ["/bin/bash", "/startup.sh"]