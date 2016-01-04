from PIL import ImageFont, ImageDraw, Image
import sys

def makeImage(c, l, color):
  letter = l #if l!='0' else 'O'
  image = Image.open('circle.png')
  draw = ImageDraw.Draw(image)

  # use a bitmap font
  f = "/usr/share/fonts/truetype/msttcorefonts/arialbd.ttf"
  #f = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
  font = ImageFont.truetype(f, 450)

  sx, sy = font.getsize(letter)
  ascent, descent = font.getmetrics()
  posx = 256 - sx/2
  posy = 256 - ascent +sy/2 #- descent

  #draw.rectangle((0,256,512, 256+sy), fill='blue')
  draw.text((posx, posy), letter, font=font, fill=color)

  image.save("%s_%s.png" % (c, l))


for c in ['y', 'b']:
  for letter in range(ord('0'), ord('9')+1):
    letter = chr(letter)
    if c=='y':
	color = (255, 177, 0, 255)
    if c=='b':
	color = (0, 0, 0, 255)

    makeImage(c, letter, color)

