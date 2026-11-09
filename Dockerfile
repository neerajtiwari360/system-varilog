FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

RUN apt-get update && apt-get install -y --no-install-recommends \
    iverilog \
    verilator \
    yosys \
    graphviz \
    gtkwave \
    make \
    python3 \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    xfonts-base \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["bash"]