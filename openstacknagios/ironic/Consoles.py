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

import subprocess
import json
import openstacknagios.openstacknagios as osnag

class Consoles(osnag.Resource):
    """
    Determines status of ironic node consoles.
    """

    def probe(self):
        # Getting the Python Ironic client to talk SSL is a dark art
        # Use the command line client instead
        try:
            cmd = "ironic --json node-list --detail --associated=true"
            out = subprocess.check_output(cmd, shell=True)
            nodes = json.loads(out)

        except Exception as e:
            self.exit_error(str(e))

        stati = dict(disabled=0, total=0)
        stati['total'] = len(nodes)
        disabled = [x for x in nodes if not x[u'console_enabled']]
        stati['disabled'] = len(disabled)

        for r in stati.keys():
            yield osnag.Metric(r, stati[r], min=0)


@osnag.guarded
def main():        
    argp = osnag.ArgumentParser(description=__doc__)

    argp.add_argument('--warn', metavar='RANGE', default='@1:',
                      help='return warning if number of associated nodes with disabled consoles is outside RANGE (default: @1:, warn if any node in maintenance)')
    argp.add_argument('--critical', metavar='RANGE', default='0:',
                      help='return critical if number of associated nodes with disabled consoles is outside RANGE (default: 0:, never critical)')

    args = argp.parse_args()

    check = osnag.Check(
        Consoles(args=args),
        osnag.ScalarContext('disabled', args.warn, args.critical),
        osnag.ScalarContext('total', '0:', '@0'),
        osnag.Summary(show=['disabled', 'total']))
    check.main(verbose=args.verbose, timeout=args.timeout)

if __name__ == '__main__':
    main()
