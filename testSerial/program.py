import sys
import time
import threading

def doIt():
  while True:
    print "hello"
    sys.stdout.flush()
    time.sleep(2)

t=threading.Thread(target=doIt)
t.daemon=True
t.start()

while True:
  l = sys.stdin.readline()
  print >>sys.stderr, "Got: ", l

