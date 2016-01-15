#!/bin/sh

cd $(dirname $0)
video/run-camera.sh &
./main.sh &
