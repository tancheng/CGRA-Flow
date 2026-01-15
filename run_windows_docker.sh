#!/usr/bin/env bash

IMAGE=cgra/neura-flow:20260114

CONTAINER=neuraflow20260114

XSOCK=/tmp/.X11-unix

sudo docker run \
    -it \
    --name=$CONTAINER \
    -v $XSOCK:$XSOCK:rw \
    -e DISPLAY=$DISPLAY \
    $IMAGE \
    /bin/bash

