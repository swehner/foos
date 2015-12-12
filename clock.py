import time


class Clock:
    name = None
    time = None

    def __init__(self, name):
        self.name = name

    def get(self):
        return self.time

    def reset(self):
        self.time = time.time()

    def get_diff(self):
        if self.time:
            return time.time() - self.time
        else:
            return None
