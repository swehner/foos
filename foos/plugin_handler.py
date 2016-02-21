import os
import atexit
import pickle
import importlib
import logging
import config

logger = logging.getLogger(__name__)


class PluginHandler:
    def __init__(self, bus):
        self.status_file = '.status'
        # Register save status on exit
        atexit.register(self.save)
        self.load(bus)
        self.load_state()

    def load(self, bus):
        self.running_plugins = {}
        logger.info("Loading plugins %s", config.plugins)
        for plugin in config.plugins:
            module = importlib.import_module('plugins.' + plugin)
            p = module.Plugin(bus)
            self.running_plugins[plugin] = p
            logger.info("Loaded plugin %s", plugin)

    def save(self):
        state = {}
        for name, p in self.running_plugins.items():
            m = getattr(p, "save", None)
            if callable(m):
                s = m()
                if s:
                    state[name] = s

        with open(self.status_file, 'wb') as f:
            pickle.dump(state, f)

    def load_state(self):
        if not os.path.isfile(self.status_file):
            logger.info("Not loading state: State file not found")
            return
        try:
            with open(self.status_file, 'rb') as f:
                state = pickle.load(f)

                for name, s in state.items():
                    if name in self.running_plugins:
                        p = self.running_plugins[name]
                        m = getattr(p, "load", None)
                        if callable(m):
                            m(s)

        except:
            logger.exception("State loading failed")
