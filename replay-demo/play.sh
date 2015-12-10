#!/bin/sh

./pngview score.png -y 800 &

(while true; do 
  ./pngview replay.png -x 50 -y 50 -t 500 -b 0x0000
  sleep 0.5
done) &


./hello_video.bin ./test.h264

pkill -P $$
