#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 10:59 BRT 2020
Last modified on Mon Mar 30 18:47 BRT 2020
author: guilherme passos | twitter: @gpass0s

This module teests fetcher module's methods
"""
from isales import fetcher
from isales.fetcher import RedisReader, HubSpotFetcher
from unittest.mock import MagicMock, patch

_SUBSCRIPTION_ITEMS = [
    {"objectId": 1549880507, "subscriptionType": "deal.propertyChange"},
    {"objectId": 383611195, "subscriptionType": "contact.creation"},
]


@patch.dict("os.environ", {"MAX_BUFFER": "2"})
@patch.dict("os.environ", {"QUEUE_TO_READ": "QUEUE_A"})
@patch.object(fetcher, "RedisConnectionManager", autospec=True)
def test_read_from_redis(mocked_redis_connection_manager):

    mocked_redis_client = MagicMock()
    mocked_redis_connection_manager.return_value = mocked_redis_client
    redis_queue = [
        b"[{'objectId': 1549880507, 'subscriptionType': 'deal.propertyChange'}]",
        b"[{'objectId': 383611195, 'subscriptionType': 'contact.creation'}]",
    ]
    mocked_redis_client.lrange.return_value = redis_queue

    redis_reader = RedisReader()
    response = redis_reader()

    assert response == _SUBSCRIPTION_ITEMS


@patch.dict("os.environ", {"DEAL_API_URL": "https://api.hubapi.com/deals/v1/deal/"})
@patch.dict("os.environ", {"CONTACT_API_URL": "https://api.hubapi.com/contacts/v1/"})
@patch.dict("os.environ", {"CONTACT_CREATION_SUBSCRIPTION": "contact.creation"})
@patch.object(fetcher, "RedisConnectionManager", autospec=True)
@patch.object(HubSpotFetcher, "_request")
@patch.object(HubSpotFetcher, "_build_url")
def test_fetch_from_hubspot(
    mocked_build_url, mocked_request, mocked_redis_connection_manager
):

    mocked_build_url.return_value = "https://api.hubapi.com/"
    mocked_request.return_value = {"associations": {"associatedVids": [383216495]}}

    hubspot_fetcher = HubSpotFetcher()
    response = hubspot_fetcher(_SUBSCRIPTION_ITEMS)
    expected_response = {
        "non_predictable_contacts": [_SUBSCRIPTION_ITEMS[1]],
        "predictable_contacts": [{"associations": {"associatedVids": [383216495]}}],
    }

    assert response == expected_response


@patch.dict("os.environ", {"DEAL_API_URL": "https://api.hubapi.com/deals/v1/deal/"})
@patch.dict("os.environ", {"CONTACT_API_URL": "https://api.hubapi.com/contacts/v1/"})
@patch.dict("os.environ", {"CONTACT_CREATION_SUBSCRIPTION": "contact.creation"})
@patch.object(fetcher, "RedisConnectionManager", autospec=True)
@patch.object(HubSpotFetcher, "_request")
@patch.object(HubSpotFetcher, "_build_url")
def test_fetch_from_hubspot_no_contacts(
    mocked_build_url, mocked_request, mocked_redis_connection_manager
):

    mocked_build_url.return_value = "https://api.hubapi.com/"
    mocked_request.return_value = {"associations": {"associatedVids": []}}

    hubspot_fetcher = HubSpotFetcher()
    response = hubspot_fetcher(_SUBSCRIPTION_ITEMS)
    expected_response = {
        "non_predictable_contacts": [_SUBSCRIPTION_ITEMS[1]],
        "predictable_contacts": [],
    }

    assert response == expected_response


@patch.dict("os.environ", {"DEAL_API_URL": "https://api.hubapi.com/deals/v1/deal/"})
@patch.dict("os.environ", {"CONTACT_API_URL": "https://api.hubapi.com/contacts/v1/"})
@patch.dict("os.environ", {"CONTACT_CREATION_SUBSCRIPTION": "contact.creation"})
@patch.object(fetcher, "RedisConnectionManager", autospec=True)
@patch.object(HubSpotFetcher, "_request")
@patch.object(HubSpotFetcher, "_build_url")
def test_fetch_from_hubspot_error(
    mocked_build_url, mocked_request, mocked_redis_connection_manager
):

    mocked_build_url.return_value = "https://api.hubapi.com/"
    mocked_request.return_value = {"associations": None}

    hubspot_fetcher = HubSpotFetcher()
    response = hubspot_fetcher(_SUBSCRIPTION_ITEMS)
    expected_response = {
        "non_predictable_contacts": [_SUBSCRIPTION_ITEMS[1]],
        "predictable_contacts": [],
    }

    assert response == expected_response


@patch.dict("os.environ", {"DEAL_API_URL": "https://api.hubapi.com/deals/v1/deal/"})
@patch.dict("os.environ", {"CONTACT_API_URL": "https://api.hubapi.com/contacts/v1/"})
@patch.dict("os.environ", {"CONTACT_CREATION_SUBSCRIPTION": "contact.creation"})
@patch.object(fetcher, "RedisConnectionManager", autospec=True)
@patch.object(fetcher, "requests", autospec=True)
def test_hubspot_fetcher_request(mocked_requests, mocked_redis_connection_manager):

    mocked_redis_client = MagicMock()
    mocked_redis_connection_manager.return_value = mocked_redis_client

    hubspot_fetcher = HubSpotFetcher()
    mocked_redis_client.get.return_value = b"ACCESS_TOKEN"
    headers = {"Authorization": "Bearer ACCESS_TOKEN"}
    url = "https://api.hubapi.com/contacts/v1/"
    hubspot_fetcher._request(url)

    mocked_requests.get.assert_called_once_with(url, headers=headers)


@patch.dict("os.environ", {"DEAL_API_URL": "https://api.hubapi.com/deals/v1/deal/"})
@patch.dict("os.environ", {"CONTACT_API_URL": "https://api.hubapi.com/contacts/v1/"})
@patch.dict("os.environ", {"CONTACT_CREATION_SUBSCRIPTION": "contact.creation"})
@patch.object(fetcher, "RedisConnectionManager", autospec=True)
def test_hubspot_fetcher_build_contact_url(mocked_redis_connection_manager):

    base_url = "https://api.hubapi.com/contacts/v1/vid="
    ids = [1, 2, 3, 4, 5]

    hubspot_fetcher = HubSpotFetcher()
    response = hubspot_fetcher._build_url(base_url, *ids)
    expected_response = (
        "https://api.hubapi.com/contacts/v1/vid=1&vid=2&vid=3&vid=4&vid=5"
    )

    assert response == expected_response
