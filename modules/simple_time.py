import time


def entry_call() -> str:
    ret = f"It is currently: \n\t{time.ctime(time.time())}"
    return ret