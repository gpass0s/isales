#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 03 23:51 BRT 2020

author: guilherme passos | twitter: @gpass0s

This module tests sender module's methods
"""
import pytest
from unittest.mock import MagicMock, patch

from isales import sender
from isales.sender import HubSpotWriter


@pytest.fixture
@patch.dict("os.environ", {"CONTATCS_FOR_UPDATE_QUEUE": "CONTACTS_FOR_UPDATE"})
@patch.dict(
    "os.environ",
    {"CONTACT_POST_API_URL": "https://api.hubapi.com/contacts/v1/contact/batch"},
)
@patch.dict("os.environ", {"MAX_BUFFER_SENDER": "10"})
@patch.object(sender, "RedisConnectionManager")
@patch.object(sender, "RedisReader")
def hubspot_writer_object(RedisReader, RedisConnectionManager):
    hubspot_writer = HubSpotWriter()
    return hubspot_writer


def test_build_payload(hubspot_writer_object):
    # arange
    contacts_for_update = [
        {"contact_id": "383611195", "prediction": "0.8"},
        {"contact_id": "383216724", "prediction": "404"},
    ]
    expected_response = [
        {"vid": "383611195", "properties": [{"property": "ML", "value": "0.8"}]},
        {"vid": "383216724", "properties": [{"property": "ML", "value": "404"}]},
    ]
    # act
    hubspot_writer_object._build_payload(contacts_for_update)
    # assert
    assert hubspot_writer_object.payload == expected_response


@patch.object(sender, "requests", autospec=True)
def test_hubspot_fetcher_request(mocked_requests, hubspot_writer_object):
    # arrange
    mocked_redis_client = MagicMock()
    hubspot_writer_object.redis_client = mocked_redis_client
    mocked_redis_client.get.return_value = b"ACCESS_TOKEN"
    headers = {"Authorization": "Bearer ACCESS_TOKEN"}
    payload = []
    url = "https://api.hubapi.com/contacts/v1/contact/batch"
    # act
    hubspot_writer_object._update()
    # assert
    mocked_requests.post.assert_called_once_with(url=url, headers=headers, data=payload)
