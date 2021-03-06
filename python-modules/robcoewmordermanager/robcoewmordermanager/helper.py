#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
#
# This file is part of ewm-cloud-robotics
# (see https://github.com/SAP/ewm-cloud-robotics).
#
# This file is licensed under the Apache Software License, v. 2 except as noted
# otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
#

"""Helper functions for order manager."""

import logging
import time

from collections import defaultdict, namedtuple, OrderedDict

from robcoewmtypes.robot import RequestFromRobot
from robcoewmtypes.warehouseorder import ConfirmWarehouseTask
from robcoewminterface.exceptions import NoOrderFoundError

_LOGGER = logging.getLogger(__name__)

WhoIdentifier = namedtuple('WhoIdentifier', ['lgnum', 'who'])


def retry_on_connection_error(exc: Exception):
    """Return True if there is an connection error exception."""
    return isinstance(exc, (ConnectionError, TimeoutError, IOError))


def retry_on_conn_noorder_error(exc: Exception):
    """Return True if there is an NoOrderFoundError exception."""
    return isinstance(exc, (ConnectionError, TimeoutError, IOError, NoOrderFoundError))


class ProcessedMessageMemory:
    """Memorize processed Order Manager messages."""

    def __init__(self) -> None:
        """Constructor."""
        # Warehouse order confirmations
        self.who_confirmations = defaultdict(list)
        self.deleted_whos = OrderedDict()
        # Robot requests
        self.robotrequests = {}
        self.deleted_robotrequests = OrderedDict()
        self.request_count = defaultdict(int)

    def memorize_who_conf(self, conf: ConfirmWarehouseTask) -> None:
        """Memorize warehouse order confirmation."""
        whoident = WhoIdentifier(conf.lgnum, conf.who)
        self.who_confirmations[whoident].append(conf)

    def check_who_conf_processed(self, conf: ConfirmWarehouseTask) -> bool:
        """Check if warehouse order confirmation was processed before."""
        whoident = WhoIdentifier(conf.lgnum, conf.who)
        return bool(conf in self.who_confirmations[whoident])

    def delete_who_from_memory(self, conf: ConfirmWarehouseTask) -> None:
        """Delete warehouse order from memory."""
        whoident = WhoIdentifier(conf.lgnum, conf.who)
        # Save timestamp when the order was deleted
        self.deleted_whos[whoident] = time.time()

        # Keep a maximum of 500 entries in this dictionary
        to_remove = max(0, len(self.deleted_whos) - 500)
        for _ in range(to_remove):
            who, _ = self.deleted_whos.popitem(last=False)
            self.who_confirmations.pop(who, None)

    def memorize_robotrequest(self, requestident: str, robotrequest: RequestFromRobot) -> None:
        """Memorize robot request."""
        self.robotrequests[requestident] = robotrequest

    def check_robotrequest_processed(
            self, requestident: str, robotrequest: RequestFromRobot) -> bool:
        """Check if robotrequest was processed before."""
        processed_request = self.robotrequests.get(
            requestident, RequestFromRobot(robotrequest.lgnum, robotrequest.rsrc))
        return bool(robotrequest != processed_request)

    def delete_robotrequest_from_memory(
            self, requestident: str, robotrequest: RequestFromRobot) -> None:
        """Delete robotrequest from memory."""
        # Save timestamp when the robotrequest was deleted
        self.deleted_robotrequests[requestident] = time.time()

        # Keep a maximum of 500 entries in this dictionary
        to_remove = max(0, len(self.deleted_robotrequests) - 500)
        for _ in range(to_remove):
            robotrequest_del, _ = self.deleted_robotrequests.popitem(last=False)
            self.robotrequests.pop(robotrequest_del, None)
