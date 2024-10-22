# hadolint ignore=DL3007
FROM ghcr.io/buvis/debian-slim:latest

ARG VERSION

USER root

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV HOME=/app \
    TERM=xterm-256color

# Install vifm
# hadolint ignore=DL3008,DL3015,SC2086
RUN \
  apt-get update \
  && apt-get install -y --no-install-recommends \
       ca-certificates \
       mediainfo \
       nvim \
       vifm \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache \
  && update-ca-certificates -f \
  chown -R kah /app \
  && chmod -R u=rwX,go=rX /app \
  && printf "umask %d" "${UMASK}" >> /etc/bash.bashrc

# Switch to app directory
WORKDIR "/app"

# Switch to kah user
USER kah

# Create volumes
VOLUME ["/data"]

# Copy the configuration and the entrypoint
COPY --chown=kah ./apps/vifm/config/vifmrc /app/.vifm/vifmrc
COPY --chown=kah ./apps/vifm/entrypoint.sh /entrypoint.sh

# Start Mopidy
CMD ["/entrypoint.sh"]

LABEL \
  org.opencontainers.image.title="vifm" \
  org.opencontainers.image.source="https://github.com/buvis/container-images/tree/main/apps/vifm" \
  org.opencontainers.image.version="${VERSION}"
