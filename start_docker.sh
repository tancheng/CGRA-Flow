#!/usr/bin/env bash

CONTAINER=CGRA-Flow
COMMAND=/bin/bash

DISP_NUM=100 # fixed display number to 100 

PORT_NUM=$((6000 + DISP_NUM))

socat TCP-LISTEN:${PORT_NUM},reuseaddr,fork UNIX-CLIENT:/tmp/.X11-unix/X0 2>&1 > /dev/null &

XSOCK=/tmp/.X11-unix

sudo docker start -i $CONTAINER
