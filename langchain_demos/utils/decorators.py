import functools
from typing import Callable, Type

from langchain_demos.utils.cache_loader import LocalCacheLoader, CacheLoader


def cacheable(key: str, loader: Type[CacheLoader] = LocalCacheLoader):

    def decorator(func: Callable):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_loader = loader(key)
            if cache_loader.is_cached():
                return cache_loader.read()

            cache_loader.write(result := func(*args, **kwargs))
            return result

        return wrapper

    return decorator
