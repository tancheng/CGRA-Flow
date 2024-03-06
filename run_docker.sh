#!/usr/bin/env bash

IMAGE=cgra/cgra-flow:demo
#COMMAND=/bin/bash
NIC=$(sudo cat /proc/net/dev | awk 'END {print $1}' | sed 's/^[\t]*//g' | sed 's/[:]*$//g')

# Grab the ip address of this box
IPADDR=$(ifconfig "$NIC" | grep "inet " | awk '{print $2}')

DISP_NUM=100 # fixed display number to 100 

PORT_NUM=$((6000 + DISP_NUM))

socat TCP-LISTEN:${PORT_NUM},reuseaddr,fork UNIX-CLIENT:/tmp/.X11-unix/X0  > /dev/null 2>&1 &

XSOCK=/tmp/.X11-unix

sudo docker run \
    -it \
    --name=CGRA-Flow \
    -v $XSOCK:$XSOCK:rw \
    -e DISPLAY="$IPADDR":$DISP_NUM \
    $IMAGE

