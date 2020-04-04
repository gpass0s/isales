#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 03 23:51 BRT 2020

author: guilherme passos | twitter: @gpass0s

This module tests sender module's methods
"""
import pytest
from unittest.mock import patch

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
    hubspot_writer_object.contacts_for_update = contacts_for_update
    # act
    hubspot_writer_object._build_payload()
    # assert
    assert hubspot_writer_object.payload == expected_response
