#!/bin/sh
if [ $# -lt 1 ]; then
  echo "Syntax: replay.sh file"
  exit 1
fi

pkill hello_video.bin 2> /dev/null

/opt/vc/src/hello_pi/hello_video/hello_video.bin $1 1> /dev/null 2>&1
