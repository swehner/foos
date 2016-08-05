import config
import sys
import collections

def toString(value):
    if isinstance(value, collections.Iterable) and not isinstance(value, str):
        return(" ".join(map(toString, value)))
    else:
        return str(value)

if __name__ == "__main__":
    value = getattr(config, sys.argv[1])

    print(toString(value))
