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
Try disabling the camera preview in config.py:
```
camera_preview="-n"
```
Or enabling offline compositing in dispmanx in /boo/config.txt (reboot required!):
```
dispmanx_offline=1
```

