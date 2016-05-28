import requests
import threading
import logging
import config
import json

from plugins.league import diskbackend
logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, bus):
        bus.subscribe(self.process_event, thread=False, subscribed_events=['results_written'])
        self.diskbe = diskbackend
        self.timeout = 2
        self.process_interval = 60
        self.do_process = threading.BoundedSemaphore(value=1)
        threading.Thread(daemon=True, target=self.retry_loop).start()
        self.write_params = {}
        if hasattr(config, 'league_apikey'):
            self.write_params['apiKey'] = config.league_apikey

    def process_event(self, ev):
        try:
            self.do_process.release()
        except ValueError:
            # ignore too many increments
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
        try:
            for fname in files:
                logger.info("Processing file %s", fname)
                with open(fname, 'r') as f:
                    r = requests.post(config.league_url + '/set_result', json=json.load(f), timeout=self.timeout, params=self.write_params)
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
