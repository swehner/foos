#!/bin/sh
ffmpeg -loglevel quiet -i $1 -codec:v copy -f mp4 -y $2
