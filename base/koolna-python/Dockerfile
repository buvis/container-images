FROM ghcr.io/buvis/koolna-base:latest@sha256:d40c1c533df9d402129ce1c029096cbed3f2b3e66bd633bdf4008361aedb44a0

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
