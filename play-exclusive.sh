#!/bin/sh

if [ $# -lt 1 ]; then
  echo "Syntax: play-exclusive.sh <file_name>"
  exit 1
fi

pkill hello_video.bin 2> /dev/null
#pkill omxplayer.bin 2> /dev/null

./hello_video.bin $1 > /dev/null 2>&1 &
#omxplayer $1 > /dev/null 2>&1 &
