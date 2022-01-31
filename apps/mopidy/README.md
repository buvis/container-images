## Purpose

Run [Mopidy](https://docs.mopidy.com/en/latest/) in a container.

## Prepare

1. Create directories for Mopidy: `sudo mkdir -p {/var/local/docker/mopidy/local,/var/local/docker/mopidy/media,/var/local/docker/mopidy/playlists}`
2. Create Mopidy user: `sudo useradd mopidy -u 105`
3. Make Mopidy owner of its directories: `sudo chown -R 105:staff /var/local/docker/mopidy`
4. Configure [Mopidy](https://docs.mopidy.com/en/latest/config/) in [config/mopidy.conf](https://github.com/buvis-net/container-images/blob/0f86f9beeba54f77d0301e4d31a2ae6d022815ec/apps/mopidy/config/mopidy.conf) mount as `/app/config/mopidy.conf` inside the container. Don't forget to replace the secrets by their real content.
5. Copy [config/mopidy.conf](https://github.com/buvis-net/container-images/blob/0f86f9beeba54f77d0301e4d31a2ae6d022815ec/apps/mopidy/config/mopidy.conf) to host's `/var/local/docker/mopidy/config/mopidy.conf`
6. Mount or copy media and playlists to host's `/var/local/docker/mopidy/media` and `/var/local/docker/mopidy/playlists`

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

Mopidy-YTMusic requires authentication to be done after running mopidy. Follow [Mopidy-YTMusic Configuration](https://github.com/OzymandiasTheGreat/mopidy-ytmusic#configuration)
