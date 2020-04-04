#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 13:27 BRT 2020
Last modified on Fri 03 18:45 BRT 2020
author: guilherme passos | twitter: @gpass0s
This module tests redis cli module's methods
"""

from unittest.mock import call, patch
from isales.redis_cli import RedisConnectionManager, RedisReader, RedisWriter


_EXPECTED_RESPONSE = [
    {"objectId": 1549880507, "subscriptionType": "deal.propertyChange"},
    {"objectId": 383611195, "subscriptionType": "contact.creation"},
]


@patch.dict("os.environ", {"REDIS_HOST": "redis"})
@patch.dict("os.environ", {"REDIS_PORT": "6379"})
def test_redis_connection_singleton():
    redis_client = RedisConnectionManager()
    c1 = redis_client.get_client()
    c2 = redis_client.get_client()

    assert hex(id(c1)) == hex(id(c2))


@patch.object(RedisConnectionManager, "get_client")
def test_read_from_redis(mocked_get_client):

    queue_to_read = "QUEUE_A"
    max_buffer = 2
    redis_queue = [
        b"[{'objectId': 1549880507, 'subscriptionType': 'deal.propertyChange'}]",
        b"[{'objectId': 383611195, 'subscriptionType': 'contact.creation'}]",
    ]
    mocked_get_client.return_value.lrange.return_value = redis_queue

    redis_reader = RedisReader(queue_to_read, max_buffer)
    response = redis_reader()

    assert response == _EXPECTED_RESPONSE


@patch.object(RedisConnectionManager, "get_client")
def test_insert_to_redis(mocked_redis_client):

    insert_to_redis_data = {
        "queue_a": [_EXPECTED_RESPONSE[0]],
        "queue_b": [_EXPECTED_RESPONSE[1]],
    }

    redis_writer = RedisWriter()
    redis_writer(insert_to_redis_data)

    calls = [
        call("queue_a", str(_EXPECTED_RESPONSE[0])),
        call("queue_b", str(_EXPECTED_RESPONSE[1])),
    ]

    mocked_redis_client.rpush.has_calls(calls)
