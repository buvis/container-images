FROM alpine:3.24@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf AS download

ARG VERSION
ARG TARGETARCH

RUN apk add --no-cache curl tar \
 && curl -fsSL "https://github.com/autobrr/tqm/releases/download/v${VERSION}/tqm_${VERSION}_linux_${TARGETARCH}.tar.gz" \
    | tar xz -C /tmp

FROM gcr.io/distroless/static:nonroot@sha256:8ce6dd87e9823c5b48dcfb2c8604714ccb351ce59607327bcc4957448da279b5

ARG VERSION

COPY --from=download /tmp/tqm /usr/local/bin/tqm

ENTRYPOINT ["tqm"]

LABEL \
  org.opencontainers.image.title="tqm" \
  org.opencontainers.image.source="https://github.com/buvis/container-images/tree/main/apps/tqm" \
  org.opencontainers.image.version="${VERSION}"
