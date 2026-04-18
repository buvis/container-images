FROM ghcr.io/buvis/koolna-base:latest@sha256:c287e44a9ea8ae055fb304adc038cb7562d922a6b70e05880030caa00f1a12ae

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
