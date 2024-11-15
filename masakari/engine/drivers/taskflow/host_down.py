# Copyright 2018 NTT DATA.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging
from masakari.engine.drivers.taskflow import base
import requests
import os
import re

LOG = logging.getLogger(__name__)

ENV_HOST_DOWN_USERNAME = "HOST_DOWN_USERNAME"
ENV_HOST_DOWN_PASSWORD = "HOST_DOWN_PASSWORD"
TOKEN = "X-Auth-Token"
VERIFY = False
NODE_NAME_PATTERN = "node[0-9]{3}-(bb|ap)[0-9]{2,3}"
NETBOX_URL = "https://netbox.global.cloud.sap"


class HostDown(base.MasakariTask):

    def __init__(self, context, novaclient, **kwargs):
        kwargs['requires'] = ["host_name"]

        super(HostDown, self).__init__(context,
                                       novaclient,
                                       **kwargs)

    def execute(self, host_name, **kwargs):
        # hardware console
        remote_console = None
        result = re.search(NODE_NAME_PATTERN, host_name)

        if result:
            name = result.group()

            if name:
                response = requests.get(f"{NETBOX_URL}/api/dcim/devices/?name={name}", json=True)

                if response.ok:
                    results = response.json()["results"]
                    results_len = len(results)

                    if results_len == 1:
                        oob = results[0].get("oob_ip")

                        if oob:
                            remote_console = oob["address"].split("/")[0]
                            LOG.debug(f"{remote_console} found for {name} in netbox")
                        else:
                            LOG.error(f"no out of band address in netbox for {name}")
                    elif results_len == 0:
                        LOG.error(f"no results in netbox for {name}")
                    else:
                        LOG.error(f"more than one result in netbox for {name}")
                else:
                    LOG.error(response.text)
            else:
                LOG.error(f"{name} ({host_name}) not found in netbox")
        else:
            LOG.error(f"regex ({NODE_NAME_PATTERN}) failed on {host_name}")

        # redfish
        if remote_console:
            base_url = f"https://{remote_console}/redfish/v1"
            username = os.environ.get(ENV_HOST_DOWN_USERNAME)
            password = os.environ.get(ENV_HOST_DOWN_PASSWORD)

            if not username:
                LOG.fatal(f"{ENV_HOST_DOWN_USERNAME} unset")
            if not password:
                LOG.fatal(f"{ENV_HOST_DOWN_PASSWORD} unset")

            response = requests.post(f"{base_url}/SessionService/Sessions", json={
                "UserName": username,
                "Password": password
            }, verify=VERIFY)

            if response.ok:
                session = response.headers.get(TOKEN)

                if session:
                    response = requests.post(f"{base_url}/Systems/System.Embedded.1/Actions/ComputerSystem.Reset",
                                             json={
                                                 "ResetType": "ForceOff"
                                             }, verify=VERIFY, headers={TOKEN: session})

                    if response.ok:
                        LOG.info(f"{host_name} powered off")
                        # todo: session close
                    else:
                        LOG.error(response.text)
            else:
                LOG.error(response.text)
