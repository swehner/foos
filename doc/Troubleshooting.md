# Troubleshooting

### The rainbow box appears in the upper right corner

This is Raspberry PI under-power warning - it means that your power supply is not delivering 5V. Try a supply with a higher power rating. See here for recommendations:
https://www.raspberrypi.org/help/faqs/#power

### When the replay is supposed to show nothing appears on screen and the score counters don't go back to their original position

This is most likely because you don't have enoguh RAM assigned to your GPU. We recommend at least 192MB. Use raspi-config to change it. 

### Some UI elements are not drawn correctly and show as gray/black boxes instead

This is most likely because you don't have enoguh RAM assigned to your GPU. We recommend at least 192MB. Use raspi-config to change it. 
