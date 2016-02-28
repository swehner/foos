import time


class Clock:
    def __init__(self, name):
        self.name = name
        self.time = None

    def set(self, ts):
        self.time = ts

    def get(self):
        return self.time

    def reset(self):
        self.time = time.time()

    def get_diff(self):
        if self.time:
            return time.time() - self.time
        else:
            return None
