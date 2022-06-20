ARG VERSION

FROM debian:buster-slim

ARG BUILDPLATFORM
ARG TARGETPLATFORM
ENV TARGETPLATFORM=${TARGETPLATFORM:-linux/amd64}

ENV \
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
       Mopidy-DefaultPlaylist==0.1.0 \
       Mopidy-Iris==3.63.0 \
       Mopidy-Local==3.2.1 \
       Mopidy-MPD==3.3.0 \
       Mopidy-Scrobbler==2.0.1 \
       Mopidy-Tidal==0.2.7 \
       Mopidy-TuneIn==1.1.0 \
       Mopidy-Youtube==3.5 \
       youtube-dl==2021.12.17 \
       ytmusicapi==0.22.0 \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache \
  && update-ca-certificates -f \
  && echo "kah ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/mopidy-is-superuser \
  && usermod -G audio,sudo kah

# Switch to app directory
WORKDIR "/app"

RUN \
  chown -R mopidy:audio /app \
  && chmod -R u=rwX,go=rX /app

# Create volumes
VOLUME ["/config", "/var/lib/mopidy/local", "/var/lib/mopidy/media", "/var/lib/mopidy/playlists"]

# Open the ports
EXPOSE 6680 6600

# Run as kah user
USER kah

# Copy the scripts
COPY ./apps/mopidy/shim/scan-local.sh /shim/scan-local.sh
COPY ./apps/mopidy/entrypoint.sh /entrypoint.sh

# Start Mopidy
CMD ["/entrypoint.sh"]
