import time
import requests
import threading
import logging
import config
import json

from foos.bus import Bus, Event
from plugins.league import diskbackend
logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, bus):
        bus.subscribe(self.process_event)
        self.diskbe = diskbackend
        self.timeout = 2
        self.process_interval = 60
        self.do_process = threading.BoundedSemaphore(value=1)
        threading.Thread(daemon=True, target=self.retry_loop).start()

    def process_event(self, ev):
        if ev.name == 'results_written':
            try:
                self.do_process.release()
            except ValueError:
                #ignore too many increments
                pass

    def request_games(self):
        try:
            r = requests.get(config.league_url + '/get_open_matches', timeout=self.timeout)
            r.raise_for_status()
            competition = r.json()
            self.diskbe.write_games(competition)
        except Exception as e:
            logger.error("API get games error: %s", e)

    def process_files(self):
        files = self.diskbe.get_result_files()
        logger.info("Processing files %s", files)
        try:
            for fname in files:
                with open(fname, 'r') as f:
                    r = requests.post(config.league_url + '/set_result', json=json.load(f), timeout=self.timeout)
                r.raise_for_status()

            # reload games from api
            self.request_games()

            # move all files to processed dir
            for fname in files:
                self.diskbe.mark_result_as_processed(fname)
        except Exception as e:
            logger.error("Error processing results %s", e)

    def retry_loop(self):
        while True:
            self.do_process.acquire(timeout=self.process_interval)
            self.process_files()
