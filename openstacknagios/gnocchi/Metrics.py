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
  Nagios/Icinga plugin to check gnocchi metric measurements.

  Currently supports checking for the number of measurements reported for a
  given metric for monitoring/operational purposes.
"""

import openstacknagios.openstacknagios as osnag
from gnocchiclient import client
from nagiosplugin import Summary as NagiosSummary
from nagiosplugin import Ok

from datetime import datetime
from datetime import timedelta
import re

class GnocchiMetricsSummary(NagiosSummary):
    def ok(self, results):
        return 'all resources reporting metrics'

    def problem(self, results):
        resources = [r.metric.name for r in results if r.state != Ok]
        return '{num} resources have not reported metrics: {list}'.format(num=len(resources),
                                                                          list=', '.join(resources))

class GnocchiMetrics(osnag.Resource):
    """
    Poll the latest metric measurements and report on the total amount found
    """
    DURATION_REGEX = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?')

    def __init__(self, metric=None, since=None, resources=None,
                 resources_file=None, args=None):
        self.metric = metric
        self.since = self._parse_duration(since)
        self.resources = None

        if resources:
            self.resources = resources.split(',')
        elif resources_file:
            with open(resources_file, 'r') as f:
                self.resources = [line.rstrip('\n') for line in f]

        if not self.resources:
            self.exit_error('no Gnocchi resources specified!')

        osnag.Resource.__init__(self, args=args)

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

        now = datetime.utcnow()
        some_time_ago = now - self.since

        for resource_id in self.resources:
            measures = gnocchi.metric.get_measures(self.metric,
                                                   resource_id=resource_id,
                                                   start=some_time_ago)
            yield osnag.Metric(resource_id, len(measures), context='measures', min=0)

    def _parse_duration(self, duration_str):
        parts = self.DURATION_REGEX.match(duration_str)
        if not parts:
            return
        parts = parts.groupdict()
        time_params = {}
        for (name, param) in parts.iteritems():
            if param:
                time_params[name] = int(param)
        return timedelta(**time_params)

@osnag.guarded
def main():
    argp = osnag.ArgumentParser(description=__doc__)

    # (diurnalist)
    # Override default value of '2' - gnocchi only supports v1 at the moment
    argp.set_defaults(os_api_version='1')

    argp.add_argument('-m', '--metric', metavar='METRIC_NAME', required=True,
                      help='metric name (required)')
    argp.add_argument('-s', '--since', metavar='DURATION', default='1h',
                      help='time range of metrics to examine')
    argp.add_argument('-r', '--resources', metavar='RESOURCE_LIST',
                      help=('list of resources to poll metrics for (comma-separated). '
                            'Either this or --resources-file must be used.'))
    argp.add_argument('-f', '--resources-file', metavar='FILE',
                      help=('file with list of resources to poll metrics for. '
                            'Each resource should be on a separate line. '
                            'Not used if --resources is specified.'))

    argp.add_argument('-w', '--warn', metavar='RANGE', default='1:',
                      help='return warning if number of metrics is outside RANGE (default: 1:, warn if 0)')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='0:',
                      help='return critical if number of metrics is outside RANGE (default 0:, never critical)')

    args = argp.parse_args()

    check = osnag.Check(
        GnocchiMetrics(metric=args.metric, since=args.since,
                       resources=args.resources,
                       resources_file=args.resources_file,
                       args=args),
        osnag.ScalarContext('measures', args.warn, args.critical),
        GnocchiMetricsSummary())
    check.main(verbose=args.verbose, timeout=args.timeout)

if __name__ == '__main__':
    main()
