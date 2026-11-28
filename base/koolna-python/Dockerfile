FROM ghcr.io/buvis/koolna-base:latest@sha256:d930f9f11c1a0e12d99535a3d88219f68b2c6f98579ed1fee96ea8f255bd722a

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

# python, uv and ruff installs call the GitHub API (aqua release lookups, artifact
# attestations); unauthenticated CI runners share a 60 req/h limit and get 403s. Only this
# step gets a token, as a BuildKit secret (never written to a layer). No secret (e.g. local
# builds) falls back to unauthenticated requests.
# (File mount rather than env=: CI's hadolint 2.12 cannot parse the env= option.)
RUN --mount=type=secret,id=github_token,required=false,mode=0444 \
  bash -c 'if [ -s /run/secrets/github_token ]; then GITHUB_TOKEN="$(cat /run/secrets/github_token)"; export GITHUB_TOKEN; fi; eval "$(mise activate bash)" && mise install python uv ruff'
RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
