#!/usr/bin/python3
# -*- coding: utf-8 -*- 
""" 
Created on Wed Mar 11 20:28 BRT 2020 | Edited for the last time on Fri Mar 27 15:16 BRT 2020 
 
@author: guilherme passos |twiiter: @gpass0s 

This module refreshes the HubSpot API token
""" 

import json 
import os 
import redis 
import requests 
 
client_id = os.environ["CLIENT_ID"] 
client_secret = os.environ["CLIENT_SECRET"] 
redirect_url = os.environ["REDIRECT_URL"]
refresh_token = os.environ["REFRESH_TOKEN"] 
 
redis_client = redis.Redis()  
 
oatuh_url = "https://api.hubapi.com/oauth/v1/token" 
form_data = { 
    "grant_type": "refresh_token", 
    "client_id": client_id, 
    "client_secret": client_secret, 
    "redirect_uri": redirect_url, 
    "refresh_token": refresh_token 
} 
response = requests.post(oatuh_url, data=form_data) 
 
if response.status_code == 200: 
    response_content = json.loads(response.text) 
    redis_client.mset({ 
        "access_token": response_content["access_token"], 
        "refresh_token": response_content["refresh_token"] 
    }) 
