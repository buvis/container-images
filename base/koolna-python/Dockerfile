FROM ghcr.io/buvis/koolna-base:latest@sha256:d789a6b4d65268f9600e142bbadf56baa057d960d1b1c564303eb1e6b3e3440d

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
