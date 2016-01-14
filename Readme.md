#Foosball instant replay

Ever wanted to relive your best foosball shots? Now you can with this project!
Featuring:
 * Automatic goal detection & score-keeping
 * Automatic instant replay of the last goal
 * Upload replays to Youtube
 * HipChat integration to send Youtube URLs and report game progress

See a video of it in action:

[![Instant replay video](https://img.youtube.com/vi/zIOYY5FBt6w/0.jpg)](https://www.youtube.com/watch?v=zIOYY5FBt6w)

![table]
(doc/table.jpg)

To build it you'll need
 * A foosball table ;)
 * A TV
 * A Raspberry Pi to run the UI
 * The Raspberry Pi camera module to record video
 * An arduino and some electornic components for the goal detection

You can find more info on how to build its components in the [doc folder](doc/HWSetup.md)

## Run it!

To run the UI you'll need to install a few dependencies - you can find a list of the python packages in requirements.txt.
Copy the sample confiuration and customize it according to your needs:
```
cp config.py.sample config.py
vi config.py
```

On the Raspberry Pi you can run the UI simply doing
```
LD_LIBRARY_PATH=/opt/vc/lib python3 foos.py
```

Using X11 you can change the window size changing the scaling factor (-s 3 runs at 1/3 of the size)
```
python3 foos.py -s 3
```

## Acknowledgments

Big thanks to [.Tuenti](http://www.tuenti.com) (the company we work at) where this project started as a HackMeUp.

Team:
 * Laura Andina
 * Jesús Bravo
 * Daniel Pañeda
 * Stefan Wehner
