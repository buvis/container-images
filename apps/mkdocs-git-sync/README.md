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
    - GIT_REPO=https://github.com/buvis/mkdocs-zettelkasten.git
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

2. Copy `https://github.com/buvis/container-images/tree/main/apps/mkdocs-git-sync/config` to `config` directory
3. Run Docker Compose

  ``` bash
  docker compose up
  ```

This will run two services: `syncer` built from the `Dockerfile` in this repository and `nginx` web server. They share `site` volume, where `syncer` outputs the site built by MkDocs and `nginx` serves it from there.

Once started, navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000). You will see MkDocs Zettelkasten documentation generated from [its repository](https://github.com/buvis/mkdocs-zettelkasten)

## Configure

### Files

- [MkDocs configuration](https://www.mkdocs.org/user-guide/configuration/) mount as `/app/config/mkdocs.yml` inside the container
- [pip requirements](https://pip.pypa.io/en/latest/reference/requirements-file-format/) mount as `/app/config/requirements.txt` inside the container

### Environment variables

    - **GIT_CREDENTIALS**: if using a private repo, use this variable to pass `<username>:<password>` or `<token_name>:<token>`
    - **GIT_REPO**: source of markdown files for MkDocs build
    - **GIT_BRANCH**: repository's branch to use (`default: main`)
    - **UPDATE_INTERVAL**: pull from repository every x seconds (`default: 900`)
    - **LOG_LEVEL**: [logging library](https://docs.python.org/3/library/logging.html#logging-levels) minimum message level to be logged (`default: INFO`)
    - **GITHUB_WEBHOOK_SECRET**: HMAC-SHA256 secret for GitHub webhook validation
    - **GITLAB_WEBHOOK_SECRET**: token for GitLab webhook validation
    - **BITBUCKET_WEBHOOK_SECRET**: token for Bitbucket webhook URL path authentication
    - **WEBHOOK_PORT**: port for the webhook HTTP server (`default: 9000`)

### Webhooks

Set any provider secret to enable near-instant rebuilds on push. The webhook server listens on `WEBHOOK_PORT` (default 9000). Multiple providers can be active simultaneously. Polling continues as a fallback. Without any secret, the app behaves exactly as before (polling only).

#### GitHub

1. Set `GITHUB_WEBHOOK_SECRET` env var on the container
2. In your GitHub repo, go to Settings > Webhooks > Add webhook
3. Set Payload URL to `http://<your-host>:9000/hooks/github`
4. Set Content type to `application/json`
5. Set Secret to the same value as `GITHUB_WEBHOOK_SECRET`
6. Select "Just the push event"

#### GitLab

1. Set `GITLAB_WEBHOOK_SECRET` env var on the container
2. In your GitLab project, go to Settings > Webhooks
3. Set URL to `http://<your-host>:9000/hooks/gitlab`
4. Set Secret token to the same value as `GITLAB_WEBHOOK_SECRET`
5. Check "Push events"

#### Bitbucket

1. Set `BITBUCKET_WEBHOOK_SECRET` env var on the container
2. In your Bitbucket repo, go to Repository settings > Webhooks > Add webhook
3. Set URL to `http://<your-host>:9000/hooks/bitbucket/<BITBUCKET_WEBHOOK_SECRET>`
4. Select "Repository push" trigger

### Link checking

Mount a `linkcheck.yml` file to `/app/config/linkcheck.yml` to enable periodic broken link detection. See `config/syncer/linkcheck.yml` for all options.

Features:
- Checks both internal and external links in the built site
- Runs after every build and on its own configurable interval
- Sends notifications to Slack, Discord, generic webhooks, and/or email
- Configurable URL exclusion patterns

## Develop

### Update

1. Set `mkdocs-zettelkasten` to latest version (<https://pypi.org/project/mkdocs-zettelkasten/>) in `config/syncer/requirements.txt`
2. Set `GitPython` to latest version (<https://pypi.org/project/GitPython/>) in `Dockerfile`
3. Increment version in `VERSION`

### Fix/enhance

1. Do the work
2. Build image: `make build`
3. Run it: `make run` (`docker-compose.yml` is required, create it following run instructions above)
4. Repeat steps 1-3 untill the work is done
5. Increment version in `VERSION`
