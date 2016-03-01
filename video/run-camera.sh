#!/bin/sh

. $(dirname $0)/config.sh

mkdir -p $base_path

sudo mount -t tmpfs -o size=256m tmpfs $base_path

mkdir -p $fragments_path


/opt/vc/bin/raspivid -w 1296 -h 730 -fps 49 -t 0 -sg 100 -wr 100 -g 10 --ev 7 -o $fragments_path/out%04d.h264 -p 0,0,128,72 -x $fragments_path/mv%04d.txt
