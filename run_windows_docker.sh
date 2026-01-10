#!/usr/bin/env bash

IMAGE=cgra-flow:20260110

CONTAINER=cgraflow20260110

XSOCK=/tmp/.X11-unix

sudo docker run \
    -it \
    --name=$CONTAINER \
    -v $XSOCK:$XSOCK:rw \
    -e DISPLAY=$DISPLAY \
    $IMAGE \
    /bin/bash

