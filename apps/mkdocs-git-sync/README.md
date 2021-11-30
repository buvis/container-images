## Purpose
Build MkDocs site in Docker and have it automatically synced from the source git repository.

## Run
This image only builds the site to container's `/app/site` directory. Use Docker Compose to run `nginx` web server to host the site.

1. Create file `docker-compose.yml`
  ``` yaml
  version: '3'

  services:
    syncer:
      image: buvis/mkdocs-git-sync
      environment:
        - GIT_REPO=https://github.com/buvis-net/mkdocs-zettelkasten.git
        - GIT_BRANCH=main
        - UPDATE_INTERVAL=60
      volumes:
        - ./config/syncer:/app/config
        - site:/app/site
    nginx:
      image: nginx
      ports:
        - 8000:80
      volumes:
        - ./config/nginx:/etc/nginx/conf.d
        - site:/site
      depends_on:
        - syncer
  volumes:
    site:
```
2. Copy `https://github.com/buvis-net/container-images/tree/main/apps/mkdocs-git-sync/config` to `config` directory
3. Run Docker Compose
  ``` bash
  docker-compose up
  ```

This will run two services: `syncer` built from the `Dockerfile` in this repository and `nginx` web server. They share `site` volume, where `syncer` outputs the site built by MkDocs and `nginx` serves it from there.

Once started, navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000). You will see MkDocs Zettelkasten documentation generated from [its repository](https://github.com/buvis-net/mkdocs-zettelkasten)

## Configure

### Files
- [MkDocs configuration](https://www.mkdocs.org/user-guide/configuration/) mount as `/app/config/mkdocs.yml` inside the container
- [pip requirements](https://pip.pypa.io/en/latest/reference/requirements-file-format/) mount as `/app/config/requirements.txt` inside the container

### Environment variables
  - **GIT_CREDENTIALS**: if using a private repo, use this variable to pass `<username>:<password>` or `<token_name>:<token>`
  - **GIT_REPO**: source of markdown files for MkDocs build
  - **GIT_BRANCH**: repository's branch to use (`default: main`)
  - **UPDATE_INTERVAL**: pull from repository every x seconds (`default: 900`)
