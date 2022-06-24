## Purpose

Run [Mopidy](https://docs.mopidy.com/en/latest/) in a container. Works on amd64,arm64,arm. I use it on Raspberries a lot.

## Prepare

1. Create directories for [Mopidy](https://docs.mopidy.com/en/latest/): `sudo mkdir -p {/var/local/docker/mopidy/config,/var/local/docker/mopidy/data,/var/local/docker/mopidy/media}`
2. Create kah user: `sudo useradd -u 568 kah` (kah is the user executing the entrypoint in the container)
3. Let Mopidy control audio devices: `sudo usermod -G audio kah`
4. Make kah owner of its directories: `sudo chown -R kah:audio /var/local/docker/mopidy`
5. Get `mopidy.conf` from [source repository](https://raw.githubusercontent.com/buvis/container-images/main/apps/mopidy/config/mopidy.conf)
6. Edit `mopidy.conf` to configure [Mopidy](https://docs.mopidy.com/en/latest/config/). Don't forget to replace the secrets by their real content.
7. Copy `mopidy.conf` to host's `/var/local/docker/mopidy/config/mopidy.conf`
8. Mount or copy media and playlists to host's `/var/local/docker/mopidy/media`
  For example, mount from NAS over NFS:
  ```
  # add this to /etc/fstab
  <NAS_IP>:/mnt/tank/media/music /var/local/docker/mopidy/media nfs ro,auto,_netdev,noatime,nolock,bg,intr,tcp,actimeo=1800 0 0
  ```

## Run

``` bash
docker run \
  --detach \
  --restart=always \
  --name mopidy \
  --publish 6600:6600 \
  --publish 6680:6680 \
  --user kah:audio \
  --group-add $(getent group audio | cut -d: -f3) \
  --device /dev/snd \
  --mount type=bind,source=/var/local/docker/mopidy/data,target=/app \
  --mount type=bind,source=/var/local/docker/mopidy/config,target=/config,readonly \
  --mount type=bind,source=/var/local/docker/mopidy/media,target=/media \
  buvis/mopidy
```

### Use host's pulseaudio server

1. Modify the run command above by replacing `--device /dev/snd \` by `--env PULSE_SERVER=tcp:<HOST_IP>:34567 \`
2. Set the `output = pulsesink server=<HOST_IP>:34567` in `mopidy.conf` `[audio]` section

## Post-run activities

[Mopidy-Tidal](https://pypi.org/project/Mopidy-Tidal/) requires authentication to be done after running [Mopidy](https://docs.mopidy.com/en/latest/).

1. Get container's logs: `docker logs mopidy`
2. Get OAuth link from line looking like: "Visit link.tidal.com/AAAAA to log in, the code will expire in 300 seconds"
3. Copy&paste the link to your browser and approve

## Hosting

- [Docker Hub](https://hub.docker.com/repository/docker/buvis/mopidy)
- [GitHub Container registry](https://ghcr.io/buvis/mopidy)
