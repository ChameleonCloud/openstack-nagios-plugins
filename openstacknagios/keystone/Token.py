#
#    Copyright (C) 2014  Cirrax GmbH  http://www.cirrax.com
#    Benedikt Trefzer <benedikt.trefzer@cirrax.com>
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
 The check will get a token and mesure the
 time used.
"""

import time
import openstacknagios.openstacknagios as osnag
from keystoneclient.client import Client

class KeystoneToken(osnag.Resource):
    """
    Nagios/Icinga plugin to check keystone.
    """
    def probe(self):
        start = time.time()
        try:
           Client(session=self.session, region_name=self.region_name)
        except Exception as e:
           self.exit_error('cannot get token')

        get_time = time.time()

        yield osnag.Metric('gettime', get_time-start, min=0)


@osnag.guarded
def main():
    argp = osnag.ArgumentParser(description=__doc__)

    argp.add_argument('-w', '--warn', metavar='RANGE', default='0:',
                      help='return warning if number of up agents is outside RANGE (default: 0:, never warn)')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='0:',
                      help='return critical if number of up agents is outside RANGE (default 1:, never critical)')

    args = argp.parse_args()

    check = osnag.Check(
        KeystoneToken(args=args),
        osnag.ScalarContext('gettime', args.warn, args.critical),
        osnag.Summary(show=['gettime']))
    check.main(verbose=args.verbose, timeout=args.timeout)

if __name__ == '__main__':
    main()
