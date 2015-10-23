#!/bin/sh

goal=`expr 1 + $RANDOM % 5`
#omxplayer goals/mp4/GOAL$goal.mp4 &
#pid=$!

replay_file=`./extract-replay.sh`

#wait $pid
omxplayer $replay_file
