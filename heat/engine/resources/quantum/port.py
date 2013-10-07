# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from heat.engine import clients
from heat.openstack.common import log as logging
from heat.engine.resources.quantum import quantum

logger = logging.getLogger(__name__)


class Port(quantum.QuantumResource):

    properties_schema = {
        'network_id': {'Type': 'String', 'Required': True},
        'name': {'Type': 'String'},
        'value_specs': {'Type': 'Map', 'Default': {}},
        'admin_state_up': {'Default': True, 'Type': 'Boolean'},
        'fixed_ips': {
            'Type': 'List',
            'Schema': {'Type': 'Map', 'Schema': {
                'subnet_id': {'Type': 'String'},
                'ip_address': {'Type': 'String'}
            }}
        },
        'mac_address': {'Type': 'String'},
        'device_id': {'Type': 'String'},
        'security_groups': {'Type': 'List'},
        'allowed_address_pairs': {
            'Type': 'List',
            'Schema': {'Type': 'Map', 'Schema': {
                'mac_address': {'Type': 'String'},
                'ip_address': {'Type': 'String', 'Required': True}
            }}
        }
    }

    attributes_schema = {
        "admin_state_up": "the administrative state of this port",
        "device_id": "unique identifier for the device",
        "device_owner": "name of the network owning the port",
        "fixed_ips": "fixed ip addresses",
        "id": "the unique identifier for the port",
        "mac_address": "mac address of the port",
        "name": "friendly name of the port",
        "network_id": "unique identifier for the network owning the port",
        "security_groups": "a list of security groups for the port",
        "status": "the status of the port",
        "tenant_id": "tenant owning the port",
        "allowed_address_pairs": "additional mac/ip address pairs allowed to "
                                 "pass through a port"
    }

    def __init__(self, name, json_snippet, stack):
        super(Port, self).__init__(name, json_snippet, stack)

    # def add_dependencies(self, deps):
    #     super(Port, self).add_dependencies(deps)
    #     # Depend on any Subnet in this template with the same
    #     # network_id as this network_id.
    #     # It is not known which subnet a port might be assigned
    #     # to so all subnets in a network should be created before
    #     # the ports in that network.
    #     for resource in self.stack.resources.itervalues():
    #         if (resource.has_interface('OS::Quantum::Subnet') and
    #             resource.properties.get('network_id') ==
    #                 self.properties.get('network_id')):
    #                     deps += (self, resource)

    def handle_create(self):
        props = self.prepare_properties(
            self.properties,
            self.physical_resource_name())

        for fixed_ip in props.get('fixed_ips', []):
            for key, value in fixed_ip.items():
                if value is None:
                    fixed_ip.pop(key)

        for pair in props.get('allowed_address_pairs', []):
            if 'mac_address' in pair and pair['mac_address'] is None:
                del pair['mac_address']

        port = self.quantum().create_port({'port': props})['port']
        self.resource_id_set(port['id'])

    def handle_delete(self):
        from quantumclient.common.exceptions import QuantumClientException

        client = self.quantum()
        try:
            client.delete_port(self.resource_id)
        except QuantumClientException as ex:
            if ex.status_code != 404:
                raise ex

    def FnGetAtt(self, key):
        attributes = self.quantum().show_port(
            self.resource_id)['port']
        return self.handle_get_attributes(self.name, key, attributes)


def resource_mapping():
    if clients.quantumclient is None:
        return {}

    return {
        'OS::Quantum::Port': Port,
    }
