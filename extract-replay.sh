#!/bin/sh

base_path=/tmp/replay
fragments_path=$base_path/fragments

# ~300 ms (review after resolution change)
ignore_recent_chunks=1

# ~3 seconds
show_chunks=15

replay_file=$base_path/replay.mp4
fragments=`ls -tr $fragments_path/out*.h264 | head -n-$ignore_recent_chunks | tail -n$show_chunks`
goal=`expr 1 + $RANDOM % 5`
#cat goals/GOAL$goal.h264 $fragments | ffmpeg -loglevel quiet -i - -i goals/GOAL$goal.aac -codec:v copy -codec:a copy -bsf:a aac_adtstoasc -f mp4 -y $replay_file
cat $fragments | ffmpeg -loglevel quiet -i - -codec:v copy -f mp4 -y $replay_file
echo $replay_file
