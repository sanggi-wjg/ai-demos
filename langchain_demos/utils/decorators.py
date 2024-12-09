import functools
from typing import Callable, Type

from langchain_demos.utils.cache_loader import LocalCacheLoader, CacheLoader


def cacheable(cache_loader: Type[CacheLoader] = LocalCacheLoader):

    def decorator(func: Callable):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            loader = cache_loader(create_cache_key_by(str(func), *args, **kwargs))
            if loader.is_cached():
                return loader.read()

            loader.write(result := func(*args, **kwargs))
            return result

        return wrapper

    return decorator


def create_cache_key_by(*args, **kwargs):
    args_key = [f"{str(arg)}" for arg in args]
    kwargs_key = [f"{str(k)}:{str(v)}" for k, v in kwargs.items()]
    return f"{args_key}-{kwargs_key}"
