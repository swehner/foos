import threading
import Queue

class Clock:
    name = None
    event_queue = None
    clock_queue = None
    seconds = None

    def __init__(self, name, event_queue):
        self.name = name
        self.event_queue = event_queue
        self.clock_queue = Queue.Queue()
        self.seconds = 0
        self.thread = threading.Thread(target=self.clock_thread)
        self.thread.daemon = True
        self.thread.start()

    def get(self):
        return self.seconds

    def clock_thread(self):
        while True:
            try:
                self.clock_queue.get(True, 1)
                self.seconds = 0
            except Queue.Empty:
                self.seconds += 1
            self.event_queue.put({'type': 'clock', 'name': self.name, 'value': self.seconds})

    def reset(self):
        self.clock_queue.put(True)

