#Import the video/config.sh script as vars of this module
#Only supports strings without spaces or quotes

from subprocess import check_output, call
import sys

vconf = check_output("env -i bash -c ' . video/config.sh; set | grep ^[a-z].*'", shell=True)
module = sys.modules[__name__]
for l in vconf.splitlines():
    name, val = l.decode('utf-8').split('=', 1)
    setattr(module, name, val)
