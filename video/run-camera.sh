#!/bin/bash

function runcam {
    base_path=$1
    fragments_path=$base_path/fragments
    w=$2
    h=$3
    fps=$4

    shift 4
    mkdir -p $fragments_path

    exec /opt/vc/bin/raspivid -o $fragments_path/out%04d.h264 -x $fragments_path/mv%04d.txt -w $w -h $h -fps $fps -t 0 $@
}

pkill raspivid 2>/dev/null

export PYTHONPATH=$(dirname $(dirname $0))

GET_CONFIG="python3 -m foos.config_getter"

runcam $($GET_CONFIG replay_path video_size video_fps camera_preview camera_chunk_settings camera_extra_params)

