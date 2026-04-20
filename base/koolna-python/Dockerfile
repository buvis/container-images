FROM ghcr.io/buvis/koolna-base:latest@sha256:2ab0f4986a8cbf3d228c2dc556d31252de7b40951a6c2942c0c53b7cb29f2138

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
