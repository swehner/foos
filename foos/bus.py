#!/usr/bin/python3

from threading import Thread
import queue
import time
import multiprocessing as mp
import logging

logger = logging.getLogger(__name__)


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

    def subscribe_map(self, fmap, thread=False):
        def f(ev):
            fmap[ev.name](ev.data)

        self.subscribe(f, thread=thread, subscribed_events=fmap.keys())

    def subscribe(self, f, thread=False, subscribed_events=None):
        if thread:
            f = self.__threaded_func(f, subscribed_events)

        def fs(ev):
            if ev.name in subscribed_events:
                f(ev)

        self.subscribers.append(fs if subscribed_events else f)

    def notify(self, ev, ev_data=None):
        self.queue.put(Event(ev, ev_data))

    def __threaded_func(self, f, subscribed_events=None):
        q = queue.Queue(maxsize=20)

        def trun():
            while True:
                ev = q.get()
                try:
                    f(ev)
                except:
                    logger.exception("Error delivering event")
                finally:
                    q.task_done()

        def fthread(ev):
            try:
                if subscribed_events is None or ev.name in subscribed_events:
                    q.put_nowait(ev)

            except queue.Full:
                logger.warning("Queue full when sending %s to %s", ev.name, f)

        Thread(target=trun, daemon=True).start()
        return fthread

    def __run(self):
        while True:
            e = self.queue.get()
            for s in self.subscribers:
                s(e)


if __name__ == '__main__':
    from functools import partial

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
