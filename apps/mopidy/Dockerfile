ARG VERSION

FROM debian:buster-slim

ARG BUILDPLATFORM
ARG TARGETPLATFORM
ENV TARGETPLATFORM=${TARGETPLATFORM:-linux/amd64}

ENV \
  HOME=/config \
  VERSION="${VERSION}" \
  DEBCONF_NONINTERACTIVE_SEEN=true \
  DEBIAN_FRONTEND="noninteractive" \
  APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn \
  UMASK=0002

RUN \
  adduser kah \
  --uid 568 \
  --group \
  --system \
  --disabled-password \
  --no-create-home \
  && mkdir -p /config \
  && chown -R kah:kah /config \
  && chmod -R 775 /config

# Add Mopidy to sources
RUN \
  apt-get update \
  && apt-get install -y --no-install-recommends \
       ca-certificates \
       wget \
       gnupg2 \
       sudo \
  && mkdir -p /usr/local/share/keyrings \
  && wget -q -O /usr/local/share/keyrings/mopidy-archive-keyring.gpg https://apt.mopidy.com/mopidy.gpg \
  && wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/buster.list \
  && apt-get purge -y wget \
  && apt-get update \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache

# Install codecs
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
  && mkdir -p /app/mopidy \
  && chown -R kah:audio /app \
  && chmod -R u=rwX,go=rX /app \
  && usermod -G audio,sudo kah \
  # Iris needs sudo to control the server
  && echo "kah ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/kah-is-superuser \
  && printf "umask %d" "${UMASK}" >> /etc/bash.bashrc

# Switch to app directory
WORKDIR "/app"

# Run as kah user
USER kah

# Open the ports
EXPOSE 6680 6600

# Create volumes
VOLUME ["/config", "/app/mopidy/local", "/app/mopidy/media", "/app/mopidy/playlists"]

# Copy the configuration and scripts
COPY --chown=kah:audio ./apps/mopidy/config/mopidy.conf /config/mopidy.conf
COPY --chown=kah:audio ./apps/mopidy/shim/scan-local.sh /shim/scan-local.sh
COPY --chown=kah:audio ./apps/mopidy/entrypoint.sh /entrypoint.sh

# Start Mopidy
CMD ["/entrypoint.sh"]
