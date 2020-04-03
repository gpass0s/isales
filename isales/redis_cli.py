#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 13:25 BRT 2020
Last modified on Fri 03 16:49 BRT 2020
@author: guilherme passos |twiiter: @gpass0s
This module performs all redis operations such as connecting, reading and writing
"""
import ast
import os
import redis
import time
import random
from redis import WatchError, ConnectionError, TimeoutError

from isales.logger import logger


class RedisConnectionLost(Exception):
    """This exception occurs when is not possible to connect with Redis after a few retries"""

    pass


class RedisConnectionManager(object):

    _client = None

    def __init__(self):
        self.redis_host = os.environ["REDIS_HOST"]
        self.redis_port = os.environ["REDIS_PORT"]

    @classmethod
    def get_client(cls):
        """
        Returns a redis client
        This's a singleton implementation to avoid openning multiple redis connections
        """
        if cls._client:
            return cls._client

        cls._client = cls()._setup_redis()
        return cls._client

    def _setup_redis(self):
        redis_client = redis.Redis(host=self.redis_host, port=self.redis_port,)
        return redis_client


def try_again(func):

    max_tries = 3

    def wrapper(*args, **kwargs):
        for retry_count in range(max_tries):
            try:
                return func(*args, **kwargs)
            except (ConnectionError, TimeoutError, WatchError):
                logger.warning(
                    "Failed to execute redis trying again.",
                    extra={
                        "retries": retry_count,
                        "function": func.__name__,
                        "function_arguments": args,
                    },
                    exc_info=True,
                )
                time.sleep(random.uniform(0.2, 1))
            except Exception:
                logger.error(
                    msg="Error to execute redis command.",
                    extra={"function": func.__name__, "function_arguments": args},
                    exc_info=True,
                )
                raise
        logger.error(
            msg="Error to execute redis command. Connection lost.",
            extra={"function": func.__name__},
            exc_info=True,
        )
        raise RedisConnectionLost

    return wrapper


class RedisReader:
    """Reads redis subscritption queue"""

    def __init__(self, queue_to_read, max_buffer):
        self.redis_client = RedisConnectionManager().get_client()
        self.queue_to_read = queue_to_read
        self.max_buffer = max_buffer

    def __call__(self):
        redis_items = self._read_from_redis()
        return redis_items

    @try_again
    def _read_from_redis(self):
        """Reads items from redis queue and convertes them to a list of dictonaries"""
        redis_items = []
        items = self.redis_client.lrange(self.queue_to_read, 0, self.max_buffer)

        for item in items:
            parsed_item = ast.literal_eval(item.decode("utf-8"))
            redis_items = redis_items + parsed_item

        if redis_items:
            logger.info(
                msg=f"{len(redis_items)} items were read from redis {self.queue_to_read}"
            )
        return redis_items

    @try_again
    def remove_items(self):
        """Removes data from Redis"""
        queue_length = self.redis_client.llen(self.queue_to_read)
        self.redis_client.ltrim(self.queue_to_read, self.max_buffer + 1, queue_length)
        logger.info(msg=f"Items were deleted from {self.queue_to_read} redis queue")


class RedisWriter:
    """Writes data to redis"""

    def __init__(self):
        self.redis_client = RedisConnectionManager().get_client()

    def __call__(self, contacts):
        self._insert_to_redis(contacts)

    @try_again
    def _insert_to_redis(self, contacts):
        """Inserts contacts to redis"""
        for key in contacts.keys():
            if contacts[key]:
                for contact in contacts[key]:
                    self.redis_client.rpush(key, str(contact))
                logger.info(
                    msg=f"{len(contacts[key])} contacts were inserted into {key} queue."
                )
