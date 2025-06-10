#!/usr/bin/env bash

IMAGE=cgra/cgraflow:v1

CONTAINER=mycgraflow

XSOCK=/tmp/.X11-unix

sudo docker run \
    -it \
    --name=$CONTAINER \
    -v $XSOCK:$XSOCK:rw \
    -e DISPLAY=unix$DISPLAY \
    $IMAGE

