#!/usr/bin/env bash

IMAGE=cgra/cgra-flow:demo

CONTAINER=CGRA-Flow-OpenRoad

XSOCK=/tmp/.X11-unix

sudo docker run \
    -it \
    --name=$CONTAINER \
    -v $XSOCK:$XSOCK:rw \
    -e DISPLAY=unix$DISPLAY \
    $IMAGE

