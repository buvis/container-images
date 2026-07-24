FROM alpine:3.24@sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b AS download

ARG VERSION
ARG TARGETARCH

RUN apk add --no-cache curl tar \
 && curl -fsSL "https://github.com/autobrr/tqm/releases/download/v${VERSION}/tqm_${VERSION}_linux_${TARGETARCH}.tar.gz" \
    | tar xz -C /tmp

FROM gcr.io/distroless/static:nonroot@sha256:f7f8f729987ad0fdf6b05eeeae94b26e6a0f613bdf46feea7fc40f7bd72953e6

ARG VERSION

COPY --from=download /tmp/tqm /usr/local/bin/tqm

ENTRYPOINT ["tqm"]

LABEL \
  org.opencontainers.image.title="tqm" \
  org.opencontainers.image.source="https://github.com/buvis/container-images/tree/main/apps/tqm" \
  org.opencontainers.image.version="${VERSION}"
