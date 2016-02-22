import os
import atexit
import pickle
import importlib
import logging
import config
import inspect

logger = logging.getLogger(__name__)

class FoosPlugin(object):
    def save(self):
        return None

    def load(self, state):
        pass

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
            mname = 'plugins.' + plugin
            module = importlib.import_module(mname)
            ps = inspect.getmembers(module, lambda x: inspect.isclass(x) and
                                    x.__module__==mname and issubclass(x, FoosPlugin))

            for pname, p in ps:
                pname = p.__module__ + '.' + pname
                self.running_plugins[pname] = p(bus)
                logger.info("Loaded plugins %s: %s", plugin, pname)

    def save(self):
        state = {}
        for name, p in self.running_plugins.items():
            s = p.save()
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
                        p.load(s)

        except:
            logger.exception("State loading failed")
