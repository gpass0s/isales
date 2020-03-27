#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 13:27 BRT 2020

author: guilherme passos | twitter: @gpass0s
"""
import pytest

from unittest.mock import Mock, patch
from isales import redis_connector


@patch.dict("os.environ", {"REDIS_HOST": "redis"})
@patch.dict("os.environ", {"REDIS_PORT": "6379"})
def test_redis_connection_singleton():
    redis_connection = redis_connector.RedisConnectionManager()
    c1 = redis_connection.get_client()
    c2 = redis_connection.get_client()

    assert hex(id(c1)) == hex(id(c2))





