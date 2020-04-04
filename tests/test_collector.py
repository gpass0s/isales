#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 10:59 BRT 2020
Last modified on Fri 03 18:41 BRT 2020
author: guilherme passos | twitter: @gpass0s

This module tests fetcher module's methods
"""
import pytest
from unittest.mock import call, MagicMock, patch

from isales import collector
from isales.collector import HubSpotFetcher


@pytest.fixture
@patch.dict("os.environ", {"DEAL_API_URL": "https://api.hubapi.com/deals/v1/deal/"})
@patch.dict(
    "os.environ", {"CONTACT_GET_API_URL": "https://api.hubapi.com/contacts/v1/"}
)
@patch.dict("os.environ", {"CONTACT_CREATION_SUBSCRIPTION": "contact.creation"})
@patch.dict("os.environ", {"PREDICTABLE_CONTACTS_QUEUE": "CONTACTS_FOR_PREDICTION"})
@patch.dict("os.environ", {"CONTATCS_FOR_UPDATE_QUEUE": "CONTACTS_FOR_UPDATE"})
@patch.dict("os.environ", {"MAX_BUFFER_COLLETOR": "10"})
@patch.object(collector, "RedisConnectionManager")
@patch.object(collector, "RedisReader")
@patch.object(collector, "RedisWriter")
def hubspot_fetcher_object(RedisWriter, RedisReader, RedisConnectionManager):
    hubspot_fetcher = HubSpotFetcher()
    return hubspot_fetcher


@patch.object(HubSpotFetcher, "_format_new_contact")
@patch.object(HubSpotFetcher, "_fetch_deal_info")
def test_fetch_from_hubspot(
    mocked_fetch_deal_info, mocked_format_new_contact, hubspot_fetcher_object
):
    # arange
    subscription_items = [
        {"objectId": 1549880507, "subscriptionType": "deal.propertyChange"},
        {"objectId": 383611195, "subscriptionType": "contact.creation"},
        {"objectId": 383611095, "subscriptionType": "contact.propertyChange"},
        {"objectId": 383611095, "subscriptionType": "contact.propertyChange"},
    ]
    call_fetch_deal_info = [call(1549880507)]
    call_format_new_contact = [call(383611195)]
    # act
    hubspot_fetcher_object._fetch_from_hubspot(subscription_items)
    # assert
    mocked_fetch_deal_info.assert_has_calls(call_fetch_deal_info)
    mocked_format_new_contact.assert_has_calls(call_format_new_contact)
    assert hubspot_fetcher_object.contacts_id_to_fetch == [383611095]


def test_format_new_contact(hubspot_fetcher_object):
    # arange
    contact_id = 383611195
    expected_response = {"contact_id": 383611195, "prediction": "0"}
    # act
    hubspot_fetcher_object._format_new_contact(contact_id)
    # assert
    assert hubspot_fetcher_object.contacts["CONTACTS_FOR_UPDATE"] == [expected_response]


@patch.object(HubSpotFetcher, "_build_url")
@patch.object(HubSpotFetcher, "_request")
def test_fetch_deal_info(mocked_request, mocked_build_url, hubspot_fetcher_object):
    # arange
    deal_id = 1549880507
    mocked_build_url.return_value = "deal_url_to_fetch"
    mocked_request.return_value = {"associations": {"associatedVids": [383216495]}}
    hubspot_fetcher_object.contacts_id_to_fetch.append(383611095)
    # act
    hubspot_fetcher_object._fetch_deal_info(deal_id)
    # assert
    mocked_build_url.assert_called_once_with(
        "https://api.hubapi.com/deals/v1/deal/", deal_id
    )
    mocked_request.assert_called_once_with("deal_url_to_fetch")
    assert hubspot_fetcher_object.contacts_id_to_fetch == [383611095, 383216495]


@patch.object(HubSpotFetcher, "_build_url")
@patch.object(HubSpotFetcher, "_request")
def test_fetch_contact_info(mocked_request, mocked_build_url, hubspot_fetcher_object):
    # arange
    hubspot_fetcher_object.contacts_id_to_fetch = [383611095, 383216495]
    mocked_build_url.return_value = "contact_url_to_fetch"
    fetched_contats = {
        "383216495": {"vid": 383216495, "properties": {}},
        "383216724": {"vid": 383216724, "properties": {}},
    }
    mocked_request.return_value = fetched_contats
    # act
    hubspot_fetcher_object._fetch_contact_info()
    # assert
    mocked_build_url.assert_called_once_with(
        "https://api.hubapi.com/contacts/v1/", 383611095, 383216495
    )
    mocked_request.assert_called_once_with("contact_url_to_fetch")
    assert hubspot_fetcher_object.contacts_id_to_fetch == []
    assert hubspot_fetcher_object.contacts["CONTACTS_FOR_PREDICTION"] == [
        fetched_contats
    ]


@patch.object(collector, "requests", autospec=True)
def test_hubspot_fetcher_request(mocked_requests, hubspot_fetcher_object):
    # arrange
    mocked_redis_client = MagicMock()
    hubspot_fetcher_object.redis_client = mocked_redis_client
    mocked_redis_client.get.return_value = b"ACCESS_TOKEN"
    headers = {"Authorization": "Bearer ACCESS_TOKEN"}
    url = "https://api.hubapi.com/contacts/v1/"
    # act
    hubspot_fetcher_object._request(url)
    # assert
    mocked_requests.get.assert_called_once_with(url, headers=headers)


def test_hubspot_fetcher_build_contact_url(hubspot_fetcher_object):

    # arrange
    base_url = "https://api.hubapi.com/contacts/v1/vid="
    ids = [1, 2, 3, 4, 5]
    expected_response = (
        "https://api.hubapi.com/contacts/v1/vid=1&vid=2&vid=3&vid=4&vid=5"
    )
    # act
    response = hubspot_fetcher_object._build_url(base_url, *ids)
    # assert
    assert response == expected_response
