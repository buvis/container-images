## Purpose

Run [Snapcast server](https://github.com/badaix/snapcast) in a container. Multi-arch image (amd64, arm64, armhf) built from the upstream Debian package on top of Debian trixie.

## Run

```bash
docker run \
  --detach \
  --restart=always \
  --name snapserver \
  --publish 1704:1704 \
  --publish 1705:1705 \
  --publish 1780:1780 \
  --mount type=bind,source=/var/local/docker/snapserver/snapserver.conf,target=/etc/snapserver.conf,readonly \
  ghcr.io/buvis/snapserver
```

Edit `/etc/snapserver.conf` to define stream sources (TCP, pipe, etc.) and the HTTP control endpoint. See the [upstream config reference](https://github.com/badaix/snapcast/blob/master/server/etc/snapserver.conf).

## Hosting

- [Docker Hub](https://hub.docker.com/repository/docker/buvis/snapserver)
- [GitHub Container registry](https://ghcr.io/buvis/snapserver)
