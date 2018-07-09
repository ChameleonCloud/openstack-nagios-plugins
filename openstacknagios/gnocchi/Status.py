#
#    Copyright (C) 2018 University of Chicago
#    Jason Anderson <jasonanderson@uchicago.edu>
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
  Nagios/Icinga plugin to check gnocchi status.

  Checks that number of pending measurements is within a given threshold.
"""

import openstacknagios.openstacknagios as osnag
from gnocchiclient import client

class GnocchiStatus(osnag.Resource):
    def probe(self):
        try:
            session_options = dict(auth=self.auth_plugin)
            adapter_options = dict(interface=self.interface,
                                   region_name=self.region_name)
            gnocchi = client.Client(self.api_version,
                                    adapter_options=adapter_options,
                                    session_options=session_options)
        except Exception as e:
            self.exit_error('cannot get client: ' + str(e))

        status = gnocchi.status.get()
        measures = status.get('storage', {}).get('summary', {}).get('measures')
        yield osnag.Metric('measures_to_process', measures)

@osnag.guarded
def main():
    argp = osnag.ArgumentParser(description=__doc__)

    # (diurnalist)
    # Override default value of '2' - gnocchi only supports v1 at the moment
    argp.set_defaults(os_api_version='1')

    argp.add_argument('-w', '--warn', metavar='RANGE', default='1:',
                      help='return warning if number of metrics is outside RANGE (default: 1:, warn if 0)')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='0:',
                      help='return critical if number of metrics is outside RANGE (default 0:, never critical)')

    args = argp.parse_args()

    check = osnag.Check(
        GnocchiStatus(args=args),
        osnag.ScalarContext('measures_to_process', args.warn, args.critical),
        osnag.Summary(show=['measures_to_process']))
    check.main(verbose=args.verbose, timeout=args.timeout)

if __name__ == '__main__':
    main()
