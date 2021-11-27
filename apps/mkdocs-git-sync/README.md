## Purpose
Run MkDocs site in Docker and have it automatically synced from the source git repository.

## Configure

- [MkDocs configuration](./config/syncer/mkdocs.yml)
- [Additional Python modules](./config/syncer/requirements.txt)
- [Docker Compose](docker-compose.yml) - use the following environment variables
  - **GIT_CREDENTIALS**: if using a private repo, use this variable to pass <username>:<password> or <token_name>:<token>
  - **GIT_REPO**: source of markdown files for MkDocs build
  - **GIT_BRANCH**: repository's branch to use (`default: main`)
  - **UPDATE_INTERVAL**: pull from repository every x seconds (`default: 900`)

## Run
``` bash
docker-compose up
```

This will run two services: `syncer` built from the `Dockerfile` in this repository and `nginx` web server. They share `site` volume, where `syncer` outputs the site built by MkDocs and `nginx` serves it from there.

Once started, navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000). You will see MkDocs Zettelkasten documentation generated from [its repository](https://github.com/tbouska/mkdocs-zettelkasten)
