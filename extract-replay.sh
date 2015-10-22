#!/bin/sh

base_path=/tmp/replay
fragments_path=$base_path/fragments

# ~300 ms
ignore_recent_chunks=3

# ~5 seconds
show_chunks=50

replay_file=$base_path/replay_`date +%Y%m%d_%H%M%S`.mp4

cd $fragments_path
cat `ls -tr out*.h264 | head -n-$ignore_recent_chunks | tail -n$show_chunks` | ffmpeg -loglevel quiet -i - -codec:v copy -f mp4 -y $replay_file

echo $replay_file
