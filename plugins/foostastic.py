import requests
import threading
import logging
import foos.config as config

logger = logging.getLogger(__name__)

class Plugin:
    def __init__(self, bus):
        bus.subscribe(self.process_event, thread=False, subscribed_events=['results_written'])
        self.timeout = 10
        self.process_interval = 60
        self.do_process = threading.BoundedSemaphore(value=1)
        threading.Thread(daemon=True, target=self.retry_loop).start()

    def process_event(self, ev):
        try:
            self.do_process.release()
        except ValueError:
            # ignore too many increments
            pass

    def retry_loop(self):
        while True:
            self.do_process.acquire(timeout=self.process_interval)
            self.notify_webhook()

    def notify_webhook(self):
        try:
            r = requests.get(config.foostastic_webhook_url, timeout=self.timeout)
            r.raise_for_status()
            logger.info("Foostastic webhook triggered")
        except Exception as e:
            logger.error("Error notifying foostastic %s", e)

# Basic testing...
if __name__ == '__main__':
        from foos.bus import Bus
        from time import sleep
        b = Bus()
        foostastic = Plugin(b)
        b.notify('results_written')
        print("Sleeping while the plugin thread does its stuff...")
        sleep(60)
