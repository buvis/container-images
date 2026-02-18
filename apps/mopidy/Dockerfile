# hadolint ignore=DL3007
FROM ghcr.io/buvis/debian-slim:latest@sha256:a21a850d9fe58ae40cb14d1fcf214259753e9e4acba4310cde1b166a9aeaf570

ARG VERSION

USER root

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV HOME=/app

# Add Mopidy to sources
# hadolint ignore=DL3008,DL3015,SC2086
RUN \
  apt-get update \
  && apt-get install -y apt-transport-https \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
  ca-certificates \
  wget \
  gnupg2 \
  && mkdir -p /etc/apt/keyrings \
  && wget -q -O /etc/apt/keyrings/mopidy-archive-keyring.gpg https://apt.mopidy.com/mopidy.gpg \
  && wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/trixie.list \
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

# Install Mopidy
# hadolint ignore=DL3008,DL3015,SC2086
RUN \
  apt-get update \
  && apt-get install -y --no-install-recommends \
  mopidy \
  python3-full \
  python3-pip \
  python3-setuptools \
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

# Patch scan.py for GStreamer 1.25-1.26.2 StructureWrapper compat (remove when GStreamer >= 1.26.3 or Mopidy >= 4.0)
COPY ./patches/fix-gstreamer-structurewrapper.py /tmp/fix-gstreamer-structurewrapper.py
RUN python3 /tmp/fix-gstreamer-structurewrapper.py && rm /tmp/fix-gstreamer-structurewrapper.py

# Install Mopidy extensions
# hadolint ignore=DL3008,DL3015,SC2086
RUN \
  python3 -m pip install --break-system-packages \
  Mopidy-DefaultPlaylist \
  Mopidy-Iris \
  Mopidy-Local \
  Mopidy-MPD \
  Mopidy-Muse \
  Mopidy-Scrobbler \
  Mopidy-Tidal \
  Mopidy-TuneIn \
  Mopidy-Youtube \
  Mopidy-YTMusic \
  youtube-dl \
  ytmusicapi

# Switch to app directory
WORKDIR "/app"

# Switch to kah user
USER kah

# Open the ports
EXPOSE 6680 6600

# Create volumes
VOLUME ["/app", "/config", "/media"]

# Copy the configuration and scripts
COPY --chown=kah:audio ./config/mopidy.conf /config/mopidy.conf
COPY --chown=kah:audio ./shim/scan-local.sh /shim/scan-local.sh
COPY --chown=kah:audio ./entrypoint.sh /entrypoint.sh

# Start Mopidy
CMD ["/entrypoint.sh"]

LABEL \
  org.opencontainers.image.title="Mopidy" \
  org.opencontainers.image.source="https://github.com/buvis/container-images/tree/main/apps/mopidy" \
  org.opencontainers.image.version="${VERSION}"
