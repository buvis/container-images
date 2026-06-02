FROM alpine:3.23@sha256:5b10f432ef3da1b8d4c7eb6c487f2f5a8f096bc91145e68878dd4a5019afde11 AS download

ARG VERSION
ARG TARGETARCH

RUN apk add --no-cache curl tar \
 && curl -fsSL "https://github.com/autobrr/tqm/releases/download/v${VERSION}/tqm_${VERSION}_linux_${TARGETARCH}.tar.gz" \
    | tar xz -C /tmp

FROM gcr.io/distroless/static:nonroot@sha256:963fa6c544fe5ce420f1f54fb88b6fb01479f054c8056d0f74cc2c6000df5240

ARG VERSION

COPY --from=download /tmp/tqm /usr/local/bin/tqm

ENTRYPOINT ["tqm"]

LABEL \
  org.opencontainers.image.title="tqm" \
  org.opencontainers.image.source="https://github.com/buvis/container-images/tree/main/apps/tqm" \
  org.opencontainers.image.version="${VERSION}"
