#!/bin/sh

filename=`date +%Y%m%d_%H%M%S`.mp4

curl -s -T /tmp/replay/replay_long.mp4 http://10.0.11.53:8080/foosball/$filename -o /dev/null
