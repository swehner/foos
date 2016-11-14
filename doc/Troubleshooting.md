# Troubleshooting

### The rainbow box appears in the upper right corner

This is Raspberry PI under-power warning - it means that your power supply is not delivering 5V. Try a supply with a higher power rating. See here for recommendations:
https://www.raspberrypi.org/help/faqs/#power

### When the replay is supposed to show nothing appears on screen and the score counters don't go back to their original position

This is most likely because you don't have enough RAM assigned to your GPU. See next question.

### Some UI elements are not drawn correctly and show as gray/black boxes instead

This is most likely because you don't have enoguh RAM assigned to your GPU. We recommend 256MB. Use raspi-config to change it.

### The player blacks out after a few seconds or video shows tearing

This could be related to issues with dispmanx compositing.
A solution to this problem is reducing the dispmanx layers - you have several options for that:

You can turn off the framebuffer doing the following before launching foos.py
```
tvservice -o && tvserice -p
```

To get the frame buffer back you can do:
```
fbset -depth 16
```

Another option is to disable the camera preview in config.py:
```
camera_preview="-n"
```

If nonw of these work you can try enabling offline compositing in dispmanx in /boot/config.txt (reboot required!):
```
dispmanx_offline=1
```

### Replay video doesn't cover full screen

Probably your screen doesn't have a 16/9 aspect ratio.
You can configure the recording size in config.py. This is the config I use for a 16/10 monitor:

```
video_size=(1152, 720)
camera_preview="-p 0,0,115,72"
```
