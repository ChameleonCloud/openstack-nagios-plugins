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
import openstacknagios.openstacknagios as osnag
from multiprocessing import Pool

def check_console(node):

    try:
        cmd = "ironic node-get-console %s | awk '/(True|False)/ { print $(NF - 1); }'" % (
            node.strip())
        out = subprocess.check_output(cmd, shell=True)
        return out.strip()
    except Exception as e:
        print(e)
        return None

class Consoles(osnag.Resource):
    """
    Determines status of ironic node consoles.
    """

    def probe(self):
        try:
            cmd = "ironic node-list | awk '/(True|False)/ { print $(2); }'"
            out = subprocess.check_output(cmd, shell=True)
        except Exception as e:
            self.exit_error(str(e))

        lines = out.splitlines()[1:]
        stati = dict(maintenance=0, total=0) 

        def chunks(l, n):
            for i in range(0, len(l), n):
                yield l[i:i + n]

        for nodes_chunk in chunks(lines, 10):

            p = Pool(len(nodes_chunk))

            results = (p.map(check_console, nodes_chunk))
            stati['total'] += len(results)

            disabled = list(filter(lambda x: x == 'False', results))
            stati['maintenance'] += len(disabled)

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
        Consoles(args=args),
        osnag.ScalarContext('maintenance', args.warn, args.critical),
        osnag.ScalarContext('total', '0:', '@0'),
        osnag.Summary(show=['maintenance', 'total']))
    check.main(verbose=args.verbose, timeout=args.timeout)

if __name__ == '__main__':
    main()
