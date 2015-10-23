#!/bin/sh

if [ $# -lt 1 ]; then
  echo "Syntax: play-exclusive.sh <file_name>"
  exit 1
fi

pkill omxplayer.bin 2> /dev/null

omxplayer $1 > /dev/null 2>&1 &
