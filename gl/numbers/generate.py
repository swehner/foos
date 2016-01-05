from PIL import ImageFont, ImageDraw, Image
import sys

def makeImage(c, l, color):
  # most monospaced fonts have ugly zeroes use upper case O instead
  letter = l if l!='0' else 'O'
  image = Image.open('circle.png')
  draw = ImageDraw.Draw(image)

  #f = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
  f = "../../UbuntuMono-B.ttf"
  font = ImageFont.truetype(f, 480)
  sx, sy = font.getsize(letter)
  #sy for ubuntumono seems to be off
  sy = sy * 0.75
  ascent, descent = font.getmetrics()
  posx = 256 - sx/2
  posy = 256 - ascent + sy/2

  #posy = 0  
  #draw.rectangle((0,ascent-sy,512, ascent), fill='red')
  #draw.rectangle((0,0,512, sy), fill='blue')
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

