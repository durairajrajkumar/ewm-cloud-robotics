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

"""Run the FetchCore mission controller."""

import sys
import traceback
import logging

from prometheus_client import start_http_server

from fetchcontroller.fetchcore import FetchInterface
from fetchcontroller.fetchrobot import FetchRobots
from fetchcontroller.helper import MainLoopController
from fetchcontroller.mission import MissionController
from fetchcontroller.robot import RobotController

_LOGGER = logging.getLogger(__name__)


def run_missioncontroller():
    """Run one instance of the FetchCore mission controller."""
    # Start prometheus client
    start_http_server(8000)
    # Register handler to control main loop
    loop_control = MainLoopController()

    # Create instance for FetchCore interface
    fetch_api = FetchInterface()
    # Start thread to update FetchCore bearer token
    fetch_api.auth_fetchcore()
    fetch_api.refresh_bearer_thread.start()

    # Create instance for Fetch robots
    fetch_robots = FetchRobots(fetch_api)

    # Create K8S handler instances
    k8s_rc = RobotController(fetch_robots)
    k8s_mc = MissionController(fetch_robots)

    # Start
    k8s_rc.run(reprocess=True)
    k8s_mc.run(reprocess=False)

    _LOGGER.info('FetchCore mission controller started')

    try:
        # Looping while Pub/Sub subscriber is running
        while loop_control.shutdown is False:
            # Check if K8S CRD handler exception occured
            for k, exc in k8s_mc.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of mission controller. Raising it in main '
                    'thread', k)
                raise exc
            for k, exc in k8s_rc.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robot controller. Raising it in main '
                    'thread', k)
                raise exc
            # Sleep maximum 1.0 second
            loop_control.sleep(1.0)
    except KeyboardInterrupt:
        _LOGGER.info('Keyboard interrupt - terminating')
    except SystemExit:
        _LOGGER.info('System exit - terminating')
    finally:
        # Stop K8S CRD watchers
        _LOGGER.info('Stopping K8S CRD watchers')
        k8s_mc.stop_watcher()
        k8s_rc.stop_watcher()


if __name__ == '__main__':
    # Create root logger if running as main program
    ROOT_LOGGER = logging.getLogger()
    ROOT_LOGGER.setLevel(logging.INFO)

    # Create console handler and set level to info
    CH = logging.StreamHandler()
    CH.setLevel(logging.INFO)

    # Create formatter
    FORMATTER = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add formatter to ch
    CH.setFormatter(FORMATTER)

    # Add ch to logger
    ROOT_LOGGER.addHandler(CH)
    # Run order manager
    try:
        run_missioncontroller()
    except Exception:  # pylint: disable=broad-except
        EXC_INFO = sys.exc_info()
        _LOGGER.fatal(
            'Unexpected error "%s" - "%s" - TRACEBACK: %s', EXC_INFO[0],
            EXC_INFO[1], traceback.format_exception(*EXC_INFO))
        sys.exit('Application terminated with exception: "{}" - "{}"'.format(
            EXC_INFO[0], EXC_INFO[1]))
