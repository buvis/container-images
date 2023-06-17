# hadolint ignore=DL3007
FROM ghcr.io/buvis/debian-slim:vstable-20230612-slim

ARG VERSION

USER root

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV HOME=/app

# Add Mopidy to sources
# hadolint ignore=DL3008,DL3015,SC2086
RUN \
  apt-get update \
  && apt-get install -y --no-install-recommends \
       ca-certificates \
       wget \
       gnupg2 \
  && mkdir -p /usr/local/share/keyrings \
  && wget -q -O /usr/local/share/keyrings/mopidy-archive-keyring.gpg https://apt.mopidy.com/mopidy.gpg \
  && wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/buster.list \
  && apt-get purge -y wget \
  && apt-get update \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache

# Install codecs
# hadolint ignore=DL3008,DL3015,SC2086
RUN \
  apt-get update \
  && apt-get install -y --no-install-recommends \
       gstreamer1.0-alsa \
       gstreamer1.0-pulseaudio \
       gstreamer1.0-plugins-base \
       gstreamer1.0-plugins-bad \
       gstreamer1.0-plugins-good \
       gstreamer1.0-plugins-ugly \
       gstreamer1.0-libav \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache

# Install Mopidy and extensions
# hadolint ignore=DL3008,DL3015,SC2086
RUN \
  apt-get update \
  && apt-get install -y --no-install-recommends \
       mopidy \
       python3-pip \
       python3-setuptools \
  && python3 -m pip install \
       Mopidy-DefaultPlaylist \
       Mopidy-Iris \
       Mopidy-Local \
       Mopidy-MPD \
       Mopidy-Muse \
       Mopidy-Scrobbler \
       Mopidy-Tidal \
       Mopidy-TuneIn \
       Mopidy-Youtube \
       youtube-dl \
       ytmusicapi \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache \
  && update-ca-certificates -f \
  && chown -R kah:audio /app \
  && chmod -R u=rwX,go=rX /app \
  && chown -R kah:audio /media \
  && chmod -R u=rwX,go=rX /media \
  && usermod -G audio kah \
  && printf "umask %d" "${UMASK}" >> /etc/bash.bashrc

# Switch to app directory
WORKDIR "/app"

# Run as kah user
USER kah

# Open the ports
EXPOSE 6680 6600

# Create volumes
VOLUME ["/app", "/config", "/media"]

# Copy the configuration and scripts
COPY --chown=kah:audio ./apps/mopidy/config/mopidy.conf /config/mopidy.conf
COPY --chown=kah:audio ./apps/mopidy/shim/scan-local.sh /shim/scan-local.sh
COPY --chown=kah:audio ./apps/mopidy/entrypoint.sh /entrypoint.sh

# Start Mopidy
CMD ["/entrypoint.sh"]

LABEL \
  org.opencontainers.image.title="Mopidy" \
  org.opencontainers.image.source="https://github.com/buvis/container-images/tree/main/apps/mopidy" \
  org.opencontainers.image.version="${VERSION}"
