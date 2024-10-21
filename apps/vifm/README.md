## Purpose

Run [vifm](https://github.com/vifm/vifm) file manager in a container.

## Run

```bash
docker run \
  --detach \
  --restart=always \
  --name vifm \
  --mount type=bind,source=<path_to_expose_in_container>,target=/data \
  buvis/vifm
```

## Hosting

- [Docker Hub](https://hub.docker.com/repository/docker/buvis/vifm)
- [GitHub Container registry](https://ghcr.io/buvis/vifm)
