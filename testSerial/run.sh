#!/bin/bash

mkfifo x
python readSerial.py  <x | python program.py >x
