FROM debian:stable-slim
ENV DEBIAN_FRONTEND=noninteractive

ARG TARGETPLATFORM
ARG BUILDPLATFORM
ARG VERSION

# Add Mopidy to sources
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates \
        gnupg2 \
        sudo \
        wget \
 && wget -q -O mopidy.key https://apt.mopidy.com/mopidy.gpg \
 && apt-key add mopidy.key \
 && wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/buster.list \
 && apt-get purge -y wget \
 && apt-get autoremove -y \
 && apt-get clean -y \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache

# Install codecs
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        gstreamer1.0-alsa \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-libav \
 && apt-get autoremove -y \
 && apt-get clean -y \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache

# Install Mopidy and extensions
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        mopidy \
        mopidy-mpd \
        mopidy-local \
        mopidy-scrobbler \
        mopidy-soundcloud \
        mopidy-tunein \
        python3-pip \
        python3-setuptools \
 && python3 -m pip install \
        Mopidy-DefaultPlaylist==0.1.0 \
        Mopidy-Iris==3.62.0 \
        Mopidy-MPD==3.2.0 \
        Mopidy-Youtube==3.5 \
        Mopidy-YTMusic==0.3.5 \
 && apt-get autoremove -y \
 && apt-get clean -y \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache \
 && update-ca-certificates -f \
 && echo "mopidy ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/mopidy-is-superuser

# Create volumes
VOLUME ["/app/config", "/var/lib/mopidy/local", "/var/lib/mopidy/media", "/var/lib/mopidy/playlists"]

# Open the ports
EXPOSE 6680 6600

# Start Mopidy
CMD mopidy --config /app/config/mopidy.conf
