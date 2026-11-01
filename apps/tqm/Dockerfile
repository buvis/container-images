FROM alpine:3.24@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a AS download

ARG VERSION
ARG TARGETARCH

RUN apk add --no-cache curl tar \
 && curl -fsSL "https://github.com/autobrr/tqm/releases/download/v${VERSION}/tqm_${VERSION}_linux_${TARGETARCH}.tar.gz" \
    | tar xz -C /tmp

FROM gcr.io/distroless/static:nonroot@sha256:25ac8f0c3b2334a9eb05452266bd4697864a8c8ef0ef71e5e6480d7f92868329

ARG VERSION

COPY --from=download /tmp/tqm /usr/local/bin/tqm

ENTRYPOINT ["tqm"]

LABEL \
  org.opencontainers.image.title="tqm" \
  org.opencontainers.image.source="https://github.com/buvis/container-images/tree/main/apps/tqm" \
  org.opencontainers.image.version="${VERSION}"
