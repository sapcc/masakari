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
from slack_sdk.errors import SlackApiError
from masakari.engine.drivers.taskflow import base
from slack_sdk import WebClient
import os

LOG = logging.getLogger(__name__)

ENV_SLACK_TOKEN = "SLACK_TOKEN"
ENV_SLACK_CHANNEL = "SLACK_CHANNEL"


class SlackBase(base.MasakariTask):

    def __init__(self, context, novaclient, **kwargs):
        self.slack_token = os.environ[ENV_SLACK_TOKEN]
        self.slack_channel = os.environ[ENV_SLACK_CHANNEL]

        if not self.slack_token:
            LOG.fatal(f"{ENV_SLACK_TOKEN} unset")
        elif not self.slack_channel:
            LOG.fatal(f"{ENV_SLACK_CHANNEL} unset")
        else:
            self.slack = WebClient(token=self.slack_token)

        super(SlackBase, self).__init__(context,
                                        novaclient,
                                        **kwargs)


class SlackHost(SlackBase):

    def __init__(self, context, novaclient, **kwargs):
        kwargs['requires'] = ["host_name"]

        super(SlackHost, self).__init__(context,
                                        novaclient,
                                        **kwargs)

    def execute(self, host_name, **kwargs):
        try:
            self.slack.chat_postMessage(channel=self.slack_channel,
                                        text=f"HA Event occurred - Hypervisor: `{host_name}`")
            LOG.debug(f"Slack message sent to {self.slack_channel}")
        except SlackApiError as e:
            LOG.error(e.response["error"])
