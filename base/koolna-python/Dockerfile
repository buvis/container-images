FROM ghcr.io/buvis/koolna-base:latest@sha256:e1c29a1089655a18914d431bd7d6fac320e8a102aac3e5917611bde9e547dcd8

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
