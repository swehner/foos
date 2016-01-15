#!/bin/sh

if [ $# -lt 1 ]; then
  echo "Syntax: replay-last.sh short|long"
  exit 1
fi

. $(dirname $0)/config.sh

replay_file=$short_replay_file
if [ "$1" = "long" ]; then
	replay_file=$long_replay_file
fi

pkill hello_video.bin 2> /dev/null

/opt/vc/src/hello_pi/hello_video/hello_video.bin $replay_file 1> /dev/null 2>&1
