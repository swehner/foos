#!/bin/sh

[ "$1" = "manual" ] && mode="manual" || mode="auto"
[ "$2" = "false" ] && regenerate="false" || regenerate="true"

base_path=/tmp/replay
fragments_path=$base_path/fragments

ignore_recent_chunks=1
short_chunks=10
long_chunks=25

long_fragments=`ls -tr $fragments_path/out*.h264 | head -n-$ignore_recent_chunks | tail -n$long_chunks`
short_fragments=`echo "$long_fragments" | tail -n$short_chunks`


generate_video() {
  cat $fragments | ffmpeg -loglevel quiet -i - -codec:v copy -f mp4 -y $replay_file
}

#generate_video_with_intro() {
#  cat goals/GOAL$goal.h264 $fragments | ffmpeg -loglevel quiet -i - -i goals/GOAL$goal.aac -codec:v copy -codec:a copy -bsf:a aac_adtstoasc -f mp4 -y $replay_file
#}

if [ "$mode" = "auto" ]; then
  replay_file=$base_path/replay_short.mp4

  #goal=`expr 1 + $RANDOM % 5`
  #./play-exclusive.sh goals/mp4/GOAL$goal.mp4

  if [ "$regenerate" = "true" ]; then
    fragments=$short_fragments
    generate_video
  fi

  ./play-exclusive.sh $replay_file
fi

# Always generate de long version, even if we only want to play the short one
replay_file=$base_path/replay_long.mp4

if [ "$regenerate" = "true" ]; then
  fragments=$long_fragments
  generate_video
fi

if [ "$mode" = "manual" ]; then
  ./play-exclusive.sh $replay_file
fi

