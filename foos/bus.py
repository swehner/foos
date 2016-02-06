#!/usr/bin/python3

from threading import Thread
import queue
from functools import partial
import time
import multiprocessing as mp


class Event:
    def __init__(self, name, data=None, ts=None):
        self.name = name
        self.data = data
        self.ts = ts if ts is not None else time.time()

    def __repr__(self):
        return "Ev %s (%s)" % (self.name, repr(self.data))


class Bus:
    def __init__(self):
        self.queue = mp.Queue()
        self.subscribers = []
        Thread(target=self.__run, daemon=True).start()

    def subscribe(self, f, thread=False):
        if thread:
            f = self.__threaded_func(f)

        self.subscribers.append(f)

    def notify(self, ev):
        self.queue.put(ev)

    def __threaded_func(self, f):
        q = queue.Queue(maxsize=20)

        def trun():
            while True:
                ev = q.get()
                f(ev)
                q.task_done()

        def fthread(ev):
            try:
                q.put_nowait(ev)
            except queue.Full:
                print("Queue full for", f, ev)

        t = Thread(target=trun, daemon=True).start()
        return fthread

    def __run(self):
        while True:
            e = self.queue.get()
            for s in self.subscribers:
                s(e)


if __name__ == '__main__':
    def log(*args):
        args = (time.time(),) + args
        print(*args)

    def logAndSleep(*args):
        l = args[1:]
        time.sleep(args[0])
        log(*l)

    b = Bus()
    b.subscribe(partial(log, 'sub_1'))
    b.subscribe(partial(logAndSleep, 1, 'sub_2'), thread=True)
    b.subscribe(partial(log, 'sub_3'))
    b.notify("a")
    b.notify("b")
    log("finished notifying")
    time.sleep(10)
