#!/bin/sh

omxplayer goals/$(ls goals | sort -R | tail -n 1)

