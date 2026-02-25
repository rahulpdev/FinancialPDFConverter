import os
import sys

x = 1+1  # missing spaces around operator (E225)

def greet(name):  # missing return type annotation — caught by UP/B rules
    msg = 'Hello, ' + name  # single quotes (formatter), string concat (not SIM but style)
    if msg == True:  # comparison to True (E712)
        pass
    return msg


def process(items: list) -> dict:
    result = {}
    for i in range(len(items)):  # use enumerate instead (B007 / SIM)
        result[i] = items[i]
    return result


def main() -> None:
    print(greet("world"))
    data = process(["a", "b", "c"])
    print(data)
    path = os.path.join(sys.prefix, "lib")
    print(path)


if __name__ == "__main__":
    main()
