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
    Nagios/Icinga plugin to check ironic nodes.

    This corresponds to the output of 'ironic node-list'
"""

import subprocess
import openstacknagios.openstacknagios as osnag

class IronicNodes(osnag.Resource):
    """
    Determines the status of the ironic nodes.
    """
    def probe(self):
        # Getting the Python Ironic client to talk SSL is a dark art
        # Use the command line client instead
        try:
            cmd = "ironic node-list | awk '/(True|False)/ { print $(NF-1); }'"
            out = subprocess.check_output(cmd, shell=True)
        except Exception as e:
           self.exit_error(str(e))

        lines = out.splitlines()[1:]

        stati = dict(maintenance=0, total=0)

        for node in lines:
           stati['total'] += 1
           if node.strip() == 'True':
                stati['maintenance'] += 1

        for r in stati.keys():
           yield osnag.Metric(r, stati[r], min=0)

@osnag.guarded
def main():
    argp = osnag.ArgumentParser(description=__doc__)

    argp.add_argument('--warn', metavar='RANGE', default='@1:',
                      help='return warning if number of nodes in maintenance is outside RANGE (default: @1:, warn if any node in maintenance)')
    argp.add_argument('--critical', metavar='RANGE', default='0:',
                      help='return critical if number of nodes in maintenance is outside RANGE (default: 0:, never critical)')

    args = argp.parse_args()

    check = osnag.Check(
        IronicNodes(args=args),
        osnag.ScalarContext('maintenance', args.warn, args.critical),
        osnag.ScalarContext('total', '0:', '@0'),
        osnag.Summary(show=['maintenance','total']))
    check.main(verbose=args.verbose,  timeout=args.timeout)

if __name__ == '__main__':
    main()
