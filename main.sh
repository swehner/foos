#!/bin/sh

while true; do
  sleep 10
  LD_LIBRARY_PATH=/opt/vc/lib python3 foos.py
done

