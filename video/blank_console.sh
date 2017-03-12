#!/bin/sh


case "$1" in
  blank)
    echo "Blank console"
    sudo sh -c "setterm -term linux -blank force >/dev/tty0 </dev/tty0"
    vcgencmd dispmanx_list
    ;;
  restore)
    echo "Restore console"
    sudo sh -c "setterm -term linux -blank poke >/dev/tty0 </dev/tty0"
    vcgencmd dispmanx_list
    ;;
  *)
    echo "Invalid command: blank or restore"
    exit 1
    ;;
esac
