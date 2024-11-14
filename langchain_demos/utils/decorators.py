import functools
import pickle
from pathlib import Path
from typing import Callable


def caching(filepath: str):

    def decorator(func: Callable):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            path = Path(filepath)

            if path.exists():
                with open(path, 'rb') as file:
                    return pickle.load(file)

            with open(path, 'wb') as file:
                pickle.dump(result := func(*args, **kwargs), file)
            return result

        return wrapper

    return decorator
