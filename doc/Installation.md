# Installation

## Install Raspbian on SD

Install Raspbian image from here:

https://www.raspberrypi.org/documentation/installation/installing-images/README.md

I usually use the lite image because it comes without the desktop.

I find it a lot easier to connect the raspberry pi to the network and access it via ssh. If you want to do so you need to enable it.

https://www.raspberrypi.org/documentation/remote-access/ssh/


## Install foos and dependencies

Install git:
```
pi@raspberrypi:~ $ sudo apt-get update
...
pi@raspberrypi:~ $ sudo apt-get install git
...
```

Clone the repo:
```
pi@raspberrypi:~ $ git clone http://www.github.com/swehner/foos
Cloning into 'foos'...
remote: Enumerating objects: 2331, done.
remote: Total 2331 (delta 0), reused 0 (delta 0), pack-reused 2331
Receiving objects: 100% (2331/2331), 28.52 MiB | 1.26 MiB/s, done.
Resolving deltas: 100% (1463/1463), done.
```

Copy the config file:

```
pi@raspberrypi:~/foos $ cp config.py.sample config.py
```

Run the check.sh program to see what's missing

```
pi@raspberrypi:~/foos $ ./check 
Checking environment...

* Binary deps:
[ERR] play (needed for sound) not found!
[ERR] avconv (needed for upload) not found!
[ERR] cec-client (needed for standby) not found!
[ OK] python3 (needed for foos) found
[ERR] pip3 (needed for foos) not found!
====> Try: sudo apt-get install python3-pip cec-utils libav-tools sox 

* RaspberryPi specific deps:
[ OK] /opt/vc/bin/raspivid (needed for camera)
[ERR] video/player/player (needed for replay) not found
====> Try: pushd video/player; make && popd 

* Replay path:
[ OK] /dev/shm/replay is on a tmpfs
[ OK] /dev/shm/replay is writable

* GPU settings:
[ERR] GPU memory too low: 64 - we recommend 192 or more
====> Try: sudo raspi-config # and raise the split memory setting 

* evdev input:
[ OK] /dev/input seems readable io_evdev_keyboard should work

* Python deps
[   ] Can't check python3 deps for the moment - if you have issues:
====> Try: pip3 install -r requirements.txt 

* Test Replays - press Y to test N to skip
Running camera...
mmal: mmal_vc_component_create: failed to create component 'vc.ril.camera' (1:ENOMEM)
mmal: mmal_component_create_core: could not create component 'vc.ril.camera' (1)
mmal: Failed to create camera component
mmal: main: Failed to create camera component
mmal: Camera is not enabled in this build. Try running "sudo raspi-config" and ensure that "camera" has been enabled

ls: cannot access '/dev/shm/replay/fragments/out*.h264': No such file or directory
video/replay.sh: 12: video/replay.sh: video/player/player: not found

* Finished!
```

This program should guide you with all the required steps. Please follow its output rather than this guide, as it should be more up-to-date.

* Install dependencies:

```
sudo apt-get install python3-pip cec-utils libav-tools sox libatlas-base-dev libtiff5
```

* Compile deps:
```
pi@raspberrypi:~/foos $ pushd /opt/vc/src/hello_pi; ./rebuild.sh; popd
```

* Compile the player:
```
pi@raspberrypi:~/foos $ pushd video/player; make && popd
```

* Check GPU memory settings & enable camera:

```
pi@raspberrypi:~/foos $ sudo raspi-config
```

* Python deps:

```
pip3 install -r requirements.txt
```

* Reboot and run check again to see if everything is working as expected :D

### Configure your foos installation

Foos uses a set of plugins to configure what features are enabled.
Review the config.py file you've copied before to enable different features.
You should only have to uncomment the corresponding lines in the config file.

### Start foos on boot

To start foos on boot you can add it to /etc/rc.local

```
$ sudo vi /etc/rc.local
```

Add

```
sudo -u pi /home/pi/foos/foos.sh &
``` 

before

```
exit 0
```