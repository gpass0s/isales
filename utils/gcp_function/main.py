#!/usr/bin/python3
# -*- coding: utf-8 -*-
""" 
Created on Wed Mar 09 10:54 BRT 2020 | Edited for the last time on Fri Mar 27 14:48 BRT 2020 
 
@author: guilherme passos |twiiter: @gpass0s

This module inserts data that is coming in from Hubspot webhook into Redis 
"""

import os
import random
import redis

_redis_host = os.environ["REDIS_HOST"]
_redis_port = os.environ["REDIS_PORT"]
_redis_queues = ["SUBSCRIPTION_QUEUE"]
redis_client = redis.Redis(host=_redis_host, port=_redis_port)


def insert_data_into_redis(request):

    # Set CORS headers for preflight requests
    if request.method == "OPTIONS":
        # Allows GET requests from origin https://mydomain.com with
        # Authorization header
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-:Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
            "Access-Control-Allow-Credentials": "true",
        }
        return ("", 204, headers)

    # Set CORS headers for main requests
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
    }

    payload = request.get_json()
    # queue_to_insert = round(random.uniform(0, 3))
    redis_client.rpush(_redis_queues[0], str(payload))
    return "Data successfully inserted to Redis"
