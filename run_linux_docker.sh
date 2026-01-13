#!/usr/bin/env bash

CONTAINER=cgra/cgra-flow:20260110

# Allow local connections to X server
xhost +local:docker

docker run \
    -it \
    --rm \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -e DISPLAY=$DISPLAY \
    -e QT_X11_NO_MITSHM=1 \
    -e NO_AT_BRIDGE=1 \
    --net=host \
    $CONTAINER

# Revoke access when done (optional, runs after container exits)
xhost -local:docker