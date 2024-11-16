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

LOG = logging.getLogger(__name__)


class HostServiceDown(base.MasakariTask):

    def __init__(self, context, novaclient, **kwargs):
        kwargs['requires'] = ["host_name"]

        super(HostServiceDown, self).__init__(context,
                                              novaclient,
                                              **kwargs)

    def execute(self, host_name, **kwargs):
        self.update_details(f"forcing down for {host_name}")
        self.novaclient.force_down(self.context, host_name, True)
        self.update_details(f"service down forced for {host_name}", 1.0)
