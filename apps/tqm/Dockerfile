FROM alpine:3.21 AS download

ARG VERSION
ARG TARGETARCH

RUN apk add --no-cache curl tar \
 && curl -fsSL "https://github.com/autobrr/tqm/releases/download/v${VERSION}/tqm_${VERSION}_linux_${TARGETARCH}.tar.gz" \
    | tar xz -C /tmp

FROM gcr.io/distroless/static:nonroot

COPY --from=download /tmp/tqm /usr/local/bin/tqm

ENTRYPOINT ["tqm"]

LABEL \
  org.opencontainers.image.title="tqm" \
  org.opencontainers.image.source="https://github.com/buvis/container-images/tree/main/apps/tqm" \
  org.opencontainers.image.version="${VERSION}"
