#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 10:59 BRT 

author: guilherme passos | twitter: @gpass0s

This module performs unit testing on fetcher module
"""

from isales import fetcher 
from isales.fetcher import DataFetcher
from unittest.mock import MagicMock, patch

_REDIS_QUEUE = [
    b"[{'objectId': 1549880507, 'propertyName': 'closedate', 'propertyValue': '1587753210242'}]",
    b"[{'objectId': 1398572107, 'propertyName': 'closed_lost_reason'}]"
]

@patch.dict("os.environ", {"MAX_BUFFER": "2"})
@patch.dict("os.environ", {"QUEUE_TO_READ": "QUEUE_A"})
@patch.object(fetcher, "RedisConnectionManager", autospec=True)
def test_pull_from_redis(mocked_redis):

    mocked_redis_client = MagicMock()
    mocked_redis.return_value = mocked_redis_client

    mocked_redis_client.lrange.return_value = _REDIS_QUEUE
    expected_response = [
        {"objectId": 1549880507, "propertyName": "closedate", "propertyValue": "1587753210242"},
        {"objectId": 1398572107, "propertyName": "closed_lost_reason"}
    ]

    fetcher = DataFetcher()
    response = fetcher._pull_from_redis()

    assert expected_response == response
