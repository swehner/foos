#!/bin/sh

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <replay_base_path> <w> <h>"
    exit 1;
fi

base_path=$1
fragments_path=$1/fragments

pkill raspivid 2>/dev/null

mkdir -p $fragments_path

exec /opt/vc/bin/raspivid -w $2 -h $3 -fps 49 -t 0 -sg 100 -wr 100 -g 10 --ev 7 -o $fragments_path/out%04d.h264 -p 0,0,128,72 -x $fragments_path/mv%04d.txt
