#!/bin/sh

. $(dirname $0)/config.sh

long_fragments=`ls -tr $fragments_path/out*.h264 | head -n-$ignore_recent_chunks | tail -n$long_chunks`
short_fragments=`echo "$long_fragments" | tail -n$short_chunks`

generate_video() {
  if [ -n "$fragments" ]; then
    cat $fragments > $replay_file
  fi
}

# generate short replay
replay_file=$short_replay_file
fragments=$short_fragments
generate_video

# generate long replay
replay_file=$long_replay_file
fragments=$long_fragments
generate_video
