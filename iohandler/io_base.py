import threading

class IOBase:
    reader = None
    writer = None
    serial = None
    write_queue = []
    write_lock = None

    def __init__(self):
        self.reader = threading.Thread(target=self.reader_thread)
        self.reader.daemon = True
        self.reader.start()
        self.writer = threading.Thread(target=self.writer_thread)
        self.writer.daemon = True
        self.writer.start()
        self.read_lock = threading.Lock()
        self.write_lock = threading.Lock()

    def reader(self):
        raise NotImplementedError()

    def writer(self):
        raise NotImplementedError()

    def writeline(self, line):
        self.write_lock.acquire()
        self.write_queue.append(line + '\n')
        self.write_lock.release()
