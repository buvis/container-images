FROM ghcr.io/buvis/koolna-base:latest@sha256:b4612ce17970262944a8514013c4961d28b0f23bc99a44b775f73dbf850c0733

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
