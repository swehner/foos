import config
import sys

if __name__ == "__main__":
    print(getattr(config, sys.argv[1]))
