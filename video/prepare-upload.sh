#!/bin/bash

. $(dirname $0)/config.sh

out_file=${long_replay_file%.h264}.mp4
avconv -loglevel quiet -i $long_replay_file -codec:v copy -f mp4 -y $out_file
echo $out_file

