#!/usr/bin/env bash

CONTAINER=CGRA-Flow-OpenRoad

xhost + 

sudo docker start -i $CONTAINER
