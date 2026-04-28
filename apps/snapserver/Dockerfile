# hadolint ignore=DL3007
FROM ghcr.io/buvis/debian-slim:latest@sha256:0f6ff8c0482212ffd25cb6466d72bf31faf9a700b721ade9aceb46e0dffddffc

ARG VERSION
ARG TARGETARCH
ARG TARGETVARIANT

USER root

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install snapserver from the upstream Debian package
# hadolint ignore=DL3008,DL3015,SC2086
RUN \
  apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
  && case "${TARGETARCH}/${TARGETVARIANT}" in \
       amd64/) DEB_ARCH=amd64 ;; \
       arm64/) DEB_ARCH=arm64 ;; \
       arm/v7) DEB_ARCH=armhf ;; \
       *) echo "unsupported arch: ${TARGETARCH}/${TARGETVARIANT}" >&2; exit 1 ;; \
     esac \
  && curl -fsSL -o /tmp/snapserver.deb \
       "https://github.com/badaix/snapcast/releases/download/v${VERSION}/snapserver_${VERSION}-1_${DEB_ARCH}_trixie.deb" \
  && apt-get install -y --no-install-recommends /tmp/snapserver.deb \
  && rm /tmp/snapserver.deb \
  && apt-get purge -y curl \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache \
  && mkdir -p /var/lib/snapserver \
  && chown -R kah:kah /var/lib/snapserver

USER kah

EXPOSE 1704 1705 1780 4955

COPY --chown=kah:kah ./entrypoint.sh /entrypoint.sh

CMD ["/entrypoint.sh"]

LABEL \
  org.opencontainers.image.title="Snapserver" \
  org.opencontainers.image.source="https://github.com/buvis/container-images/tree/master/apps/snapserver" \
  org.opencontainers.image.version="${VERSION}"
