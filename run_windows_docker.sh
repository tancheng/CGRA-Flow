#!/usr/bin/env bash

IMAGE=cgra/neura-flow:latest

CONTAINER=neuraflow

XSOCK=/tmp/.X11-unix

sudo docker run \
    -it \
    --name=$CONTAINER \
    -v $XSOCK:$XSOCK:rw \
    -e DISPLAY=$DISPLAY \
    $IMAGE \
    /bin/bash

