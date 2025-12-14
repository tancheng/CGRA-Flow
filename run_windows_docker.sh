#!/usr/bin/env bash

IMAGE=cgra/cgra-flow::20251214_demo

CONTAINER=mycgraflow

XSOCK=/tmp/.X11-unix

sudo docker run \
    -it \
    --name=$CONTAINER \
    -v $XSOCK:$XSOCK:rw \
    -e DISPLAY=$DISPLAY \
    $IMAGE \
    /bin/bash

