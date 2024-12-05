import abc
import os
import pickle
from pathlib import Path
from typing import Any

import redis


class CacheLoader(abc.ABC):

    def __init__(self, key: str):
        self.key = key

    @abc.abstractmethod
    def is_cached(self) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def read(self) -> Any:
        raise NotImplementedError()

    @abc.abstractmethod
    def write(self, dataset: Any):
        raise NotImplementedError()


class LocalCacheLoader(CacheLoader):

    def __init__(self, key: str):
        super().__init__(key)

    def is_cached(self) -> bool:
        return Path(self.key).exists()

    def read(self) -> Any:
        with open(self.key, 'rb') as file:
            return pickle.load(file)

    def write(self, dataset: Any):
        with open(self.key, 'wb') as file:
            pickle.dump(dataset, file)


class RedisCacheLoader(CacheLoader):

    def __init__(self, key: str):
        super().__init__(key)
        self.client = redis.StrictRedis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=os.getenv("REDIS_PORT", 6379),
            db=os.getenv("REDIS_DATABASE", 7),
        )
        self.expire_ttl = os.getenv("REDIS_EXPIRE_TTL", 60 * 60)

    def is_cached(self) -> bool:
        return self.client.exists(self.key)

    def read(self) -> Any:
        return pickle.loads(
            self.client.get(self.key),
        )

    def write(self, dataset: Any):
        self.client.set(
            self.key,
            pickle.dumps(dataset),
            ex=self.expire_ttl,
        )
