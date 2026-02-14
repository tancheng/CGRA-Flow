#!/usr/bin/env bash

CONTAINER=cgra/neura-flow:latest
NIC=en0

# Grab the ip address of this box
IPADDR=$(ifconfig $NIC | grep "inet " | awk '{print $2}')
DISP_NUM=$(jot -r 1 100 200)  # random display number between 100 and 200
PORT_NUM=$((6000 + DISP_NUM)) # so multiple instances of the container won't interfer with eachother
socat TCP-LISTEN:${PORT_NUM},reuseaddr,fork UNIX-CLIENT:\"$DISPLAY\" 2>&1 > /dev/null &

XSOCK=/tmp/.X11-unix
XAUTH=/tmp/.docker.xauth.$USER.$$
touch $XAUTH
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -

docker run \
    -it \
    --rm \
    -v $XSOCK:$XSOCK:rw \
    -v $XAUTH:$XAUTH:rw \
    -e DISPLAY=$IPADDR:$DISP_NUM \
    -e XAUTHORITY=$XAUTH \
    -e QT_X11_NO_MITSHM=1 \
    -e _X11_NO_MITSHM=1 \
    -e NO_AT_BRIDGE=1 \
    $CONTAINER
