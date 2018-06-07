#
#    Copyright (C) 2015 University of Chicago
#    Pierre Riteau <priteau@uchicago.edu>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
 Nagios/Icinga plugin to check keystone.
 The check will list endpoints and warn if there are more than expected.
"""

import json
import time
import openstacknagios.openstacknagios as osnag

import keystoneclient.v2_0.client as ksclient


class KeystoneEndpoints(osnag.Resource):
    """
    Nagios/Icinga plugin to check keystone.

    """

    def __init__(self, args=None):
        self.openstack = self.get_openstack_vars(args=args)
        osnag.Resource.__init__(self)

    def probe(self):
        try:
           keystone=ksclient.Client(username    = self.openstack['username'],
                                    password    = self.openstack['password'],
                                    tenant_name = self.openstack['tenant_name'],
                                    auth_url    = self.openstack['auth_url'],
                                    cacert      = self.openstack['cacert'],
                                    insecure    = self.openstack['insecure'])
        except Exception as e:
           self.exit_error('cannot create keystone client')

        try:
            endpoints = keystone.service_catalog.get_endpoints()
        except Exception as e:
            self.exit_error('cannot get endpoints')

        yield osnag.Metric('endpoints', len(endpoints), min=0)


@osnag.guarded
def main():
    argp = osnag.ArgumentParser(description=__doc__)

    argp.add_argument('-w', '--warn', metavar='RANGE', default='0:',
                      help='return warning if number of endpoints is outside RANGE (default: 0:, never warn)')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='0:',
                      help='return critical if number of endpoints is outside RANGE (default 0:, never critical)')

    args = argp.parse_args()

    check = osnag.Check(
        KeystoneEndpoints(args=args),
        osnag.ScalarContext('endpoints', args.warn, args.critical),
        osnag.Summary(show=['endpoints'])
        )
    check.main(verbose=args.verbose, timeout=args.timeout)

if __name__ == '__main__':
    main()

