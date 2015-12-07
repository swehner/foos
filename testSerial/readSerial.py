import sys
import threading
import serial
import serial.tools.list_ports
import time

ser=None
def openSerial():
  global ser
  if ser is not None and ser.isOpen():
    ser.close()

  ports = [p for p in serial.tools.list_ports.grep("ACM|USB")]
  print >>sys.stderr, "Got ports", ports
  for p in ports:
    ser = serial.Serial(p[0], 115200)
    if ser.isOpen():
      print >>sys.stderr, "Opened port", p[0]

  if not ser.isOpen():
    time.sleep(1)

openSerial()

def readFromSerial():
  while True:
    try:
      l = ser.readline()
      if l!="":
        print >>sys.stderr, "from serial", l
        print l.strip()
	sys.stdout.flush()
    except serial.SerialException, e:
      print >>sys.stderr, "Exception occurred", e
      openSerial()

def readFromInput():
  while True:
    try:
      l = sys.stdin.readline()
      print >>sys.stderr, "from input:", l
      ser.write(l)
    except serial.SerialException, e:
      print >>sys.stderr, "Exception occurred:", e

t=threading.Thread(target=readFromSerial)
t.daemon=True
t.start()
f=threading.Thread(target=readFromInput)
f.daemon=True
f.start()

while True:
  time.sleep(1)
print >>sys.stderr, "bye"
