#!/bin/sh

while true; do
  sleep 10
  LD_LIBRARY_PATH=/opt/vc/lib python foos.py -f 25
done

