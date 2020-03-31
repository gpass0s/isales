#!/usr/bin/python
"""
.. Vertra (copyright)
.. moduleauthor:: Guilherme Passos <guilhermepassos@outlook.com>
.. created:2020-1-16
.. last modified: 2020-1-16

"""

import logging
from pythonjsonlogger.jsonlogger import JsonFormatter


def _get_logger():
    """Generate a logger."""
    logger = logging.getLogger("smarttinvest_wallet_generator")
    logger.propagate = False  # reset handler to avoid duplicates
    logger.handlers = [_get_json_handler()]
    logger.setLevel(logging.INFO)
    return logger


def _get_json_handler():
    formatter = JsonFormatter("(asctime) (levelname) (module) (funcName) (message)")
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(formatter)
    return log_handler


logger = _get_logger()
