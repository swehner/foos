#Foosball slow motion instant replay

Ever wanted to relive your best foosball shots? Now you can with this project!
Featuring:
 * Automatic goal detection & score-keeping
 * Automatic instant replay (2x slow motion) of the last goal
 * Upload replays to Youtube
 * HipChat integration to send Youtube URLs and report game progress
 * Integration with a league system

See a video of it in action:

[![Instant replay video](https://img.youtube.com/vi/BXMhitiaXEE/0.jpg)](https://www.youtube.com/watch?v=BXMhitiaXEE)

![table]
(doc/table.jpg)

To build it you'll need
 * A foosball table ;)
 * A TV
 * A Raspberry Pi to run the UI
 * The Raspberry Pi camera module to record video
 * An arduino and some electronic components for the goal detection

You can find more info on how to build its components in the [doc folder](doc/HWSetup.md)

## Run it!

To run the UI you'll need to install a few dependencies - you can find a list of the python packages in requirements.txt.
Other dependencies you'll need on your system (raspbian packages) are: `libav-tools sox cec-utils`
Verify the default configuration in config_base.py and override it if necessary. To override config copy config.py.sample to config.py and edit it:
```
cp config.py.sample config.py
vi config.py
```

To verify that you have all the dependencies you can run the check script. It will check most of the dependencies for you.
```
pi@raspberrypi:~/foos $ ./check
Checking environment...

* Binary deps:
[ OK] play (needed for sound) found
[ OK] avconv (needed for upload) found
[ OK] cec-client (needed for standby) found
[ OK] python3 (needed for foos) found
[ OK] pip3 (needed for foos) found

* RaspberryPi specific deps:
[ OK] /opt/vc/bin/raspivid (needed for camera)
[ OK] /opt/vc/src/hello_pi/hello_video/hello_video.bin (needed for replay)

* tmpfs for replays:
[ OK] /dev/shm writable - use it to store replays. See replay_path in config

* GPU settings:
[ OK] GPU memory set to 128

* Python deps
[   ] Can't check python3 deps for the moment - if you have issues:
====> Try: pip3 install -r requirements 
```

On the Raspberry Pi you can run the UI simply doing
```
python3 foos.py
```

When running in X11 it's often useful to change the window size changing the scaling factor (-s 3 runs at 1/3 of the size)
```
python3 foos.py -s 3
```

If you want to use a keyboard on the Raspberry PI you can enable the io_evdev_keyboard plugin.
This will read directly from the evdev input device (make sure pi user is in the input group and has access to /dev/input/*)
Remember this will only work on physical keyboards attached to the PI - not if you're pressing keys in a ssh session!

Keys in X11 and Raspberry PI:
 * Increment goal counter: `q, KP7, e, KP9`
 * Decrement goal counter: `z, KP1, c, KP3`
 * Ok: `s, KP5`
 * Simulate goal: `a, KP4, d, KP6`
 * Exit: `.`

## Troubleshooting

Please check the [Troubleshooting](doc/Troubleshooting.md) section for some common issues.

## Acknowledgments

Big thanks to [Tuenti](http://www.tuenti.com), where this project started as a HackMeUp and to Laura Andina for the UI design!

Team:
 * Jesús Bravo
 * Daniel Pañeda
 * Stefan Wehner

Made with Pi3d

[![Pi3d logo](https://raw.githubusercontent.com/tipam/pi3d/master/images/rpilogoshad128.png)](https://pi3d.github.io/)
