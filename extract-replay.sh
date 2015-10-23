#!/bin/sh

base_path=/tmp/replay
fragments_path=$base_path/fragments

ignore_recent_chunks=1
long_chunks=25
short_chunks=10

if [ "$1" = "long" ]; then
  fragments=`ls -tr $fragments_path/out*.h264 | head -n-$ignore_recent_chunks | tail -n$long_chunks`
  replay_file=$base_path/replay_long.mp4
else
  fragments=`ls -tr $fragments_path/out*.h264 | head -n-$ignore_recent_chunks | tail -n$short_chunks`
  replay_file=$base_path/replay_short.mp4
fi

#goal=`expr 1 + $RANDOM % 5`
#cat goals/GOAL$goal.h264 $fragments | ffmpeg -loglevel quiet -i - -i goals/GOAL$goal.aac -codec:v copy -codec:a copy -bsf:a aac_adtstoasc -f mp4 -y $replay_file

cat $fragments | ffmpeg -loglevel quiet -i - -codec:v copy -f mp4 -y $replay_file
echo $replay_file
