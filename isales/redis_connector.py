#!/usr/bin/python3
# -*- coding: utf-8 -*- 
""" 
Created on Fri Mar 27 13:25 BRT 2020 
 
@author: guilherme passos |twiiter: @gpass0s 
""" 
import os
import redis

class RedisConnectionManager(object):

    _client = None

    def __init__(self):
        self.redis_host = os.environ["REDIS_HOST"]
        self.redis_port = os.environ["REDIS_PORT"]
    
    @classmethod
    def get_client(cls):
        """
        Returns a redis client
        This's a singleton implementation 
        """

        if cls._client:
            return cls._client

        cls._client = cls()._setup_redis()
        return cls._client

    def _setup_redis(self):
        redis_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
        )
        return redis_client
