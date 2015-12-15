#!/bin/sh

base_path=/tmp/replay
fragments_path=$base_path/fragments

mkdir -p $base_path $fragments_path

#/opt/vc/bin/raspivid -w 640 -h 480 -fps 90 -t 0 -sg 100 -wr 300 -g 10 -n -o $fragments_path/out%04d.h264
/opt/vc/bin/raspivid -w 1297 -h 730 -fps 49 -t 0 -sg 100 -wr 300 -g 10 -n --ev 7 -o $fragments_path/out%04d.h264 -p 1792,0,128,72
