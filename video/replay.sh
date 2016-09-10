#!/bin/sh

DIR=$(dirname $0)

if [ $# -lt 2 ]; then
  echo "Syntax: replay.sh file fps"
  exit 1
fi

pkill player 2> /dev/null

$DIR/player/player $1 $2

