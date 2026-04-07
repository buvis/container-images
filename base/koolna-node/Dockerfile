FROM ghcr.io/buvis/koolna-base:latest@sha256:c3db8d1920abb5ef48ede1a65897cba4ffa56f55601fe8988ed1b5f694fd980d

ARG USERNAME=bob

ENV HOME=/home/$USERNAME
ENV MISE_NODE_DEFAULT_PACKAGES_FILE="$HOME/.default-npm-packages"

USER $USERNAME

# Import Node.js release signing keys for GPG verification (fallback keyserver for CI reliability)
RUN gpg --keyserver hkps://keys.openpgp.org --recv-keys 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4 \
  || gpg --keyserver hkps://keyserver.ubuntu.com --recv-keys 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4

COPY --chown=${USERNAME}:${USERNAME} assets/config/.default-npm-packages /home/$USERNAME/.default-npm-packages
COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
