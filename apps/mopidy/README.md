## Purpose

Run [Mopidy](https://docs.mopidy.com/en/latest/) in a container. Works on amd64,arm64,arm. I use it on Raspberries a lot.

## Prepare

1. Create directories for [Mopidy](https://docs.mopidy.com/en/latest/): `sudo mkdir -p {/var/local/docker/mopidy/config,/var/local/docker/mopidy/local,/var/local/docker/mopidy/media,/var/local/docker/mopidy/playlists}`
2. Create Mopidy user: `sudo useradd mopidy -u 105`
3. Make Mopidy owner of its directories: `sudo chown -R mopidy:root /var/local/docker/mopidy`
4. Get `mopidy.conf` from [source repository](https://raw.githubusercontent.com/buvis-net/container-images/main/apps/mopidy/config/mopidy.conf)
5. Edit `mopidy.conf` to configure [Mopidy](https://docs.mopidy.com/en/latest/config/). Don't forget to replace the secrets by their real content.
6. Copy `mopidy.conf` to host's `/var/local/docker/mopidy/config/mopidy.conf`
7. Mount or copy media and playlists to host's `/var/local/docker/mopidy/media` and `/var/local/docker/mopidy/playlists`

## Run

``` bash
docker run --detach --restart=always \
  -p 6680:6680 -p 6600:6600 \
  --device /dev/snd \
  --mount type=bind,source=/var/local/docker/mopidy/config,target=/app/config,readonly \
  --mount type=bind,source=/var/local/docker/mopidy/media,target=/var/lib/mopidy/media,readonly \
  --mount type=bind,source=/var/local/docker/mopidy/local,target=/var/lib/mopidy/local \
  --mount type=bind,source=/var/local/docker/mopidy/playlists,target=/var/lib/mopidy/playlists \
  --name mopidy buvis/mopidy
```

## Post-run activities

[Mopidy-YTMusic](https://github.com/OzymandiasTheGreat/mopidy-ytmusic#configuration) requires authentication to be done after running [Mopidy](https://docs.mopidy.com/en/latest/).

1. Get container's shell: `docker exec -it mopidy bash`
2. Run YTMusic setup: `mopidy --config /app/config/mopidy.conf ytmusic setup`
3. Select `/var/lib/mopidy/local` as directory where to save `auth.json`

## Hosting

- [Docker Hub](https://hub.docker.com/repository/docker/buvis/mopidy)
- [GitHub Container registry](https://ghcr.io/buvis-net/mopidy)
