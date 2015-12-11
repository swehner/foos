#!/bin/sh

echo -ne "BI_D\nBD_D\n" > /tmp/foos-debug.in
sleep 0.2
echo -ne "BI_U\nBD_U\n" > /tmp/foos-debug.in
