from PIL import ImageFont, ImageDraw, Image
import sys


def makeImage(s):
    # most monospaced fonts have ugly zeroes use upper case O instead
    string = s.replace("0", "O")
    mask = Image.open('circle_m.png')
    draw = ImageDraw.Draw(mask)

    image = Image.new("LA", (512, 512), "white")

    f = "../UbuntuMono-B_circle.ttf"
    if len(string) > 1:
      font = ImageFont.truetype(f, 430)
    else:
      font = ImageFont.truetype(f, 480)

    sx, sy = font.getsize(string)
    #sy for ubuntumono seems to be off
    fsy = sy * 0.77
    posx = 256 - sx / 2
    posy = 256 - sy + fsy / 2
    draw.text((posx, posy), string, font=font, fill=0)

    image.putalpha(mask)
    image.save("%s.png" % (s))


for number in range(0, 11):
    makeImage(str(number))
