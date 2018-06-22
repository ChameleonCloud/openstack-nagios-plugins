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

from datetime import datetime
from datetime import timedelta
import re

class GnocchiMetrics(osnag.Resource):
    """
    Poll the latest metric measurements and report on the total amount found
    """
    DURATION_REGEX = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?')

    def __init__(self, metric=None, since=None, limit=None, args=None):
        self.metric = metric
        self.since = self._parse_duration(since)
        self.limit = limit
        osnag.Resource.__init__(self, args=args)

    def probe(self):
        try:
            session_options = dict(auth=self.auth_plugin)
            adapter_options = dict(interface=self.interface)
            gnocchi = client.Client(self.api_version,
                                    adapter_options=adapter_options,
                                    session_options=session_options)
        except Exception as e:
            self.exit_error('cannot get client: ' + str(e))

        now = datetime.utcnow()
        some_time_ago = now - self.since
        query = {
            '=': {
                'ended_at': None
            }
        }

        try:
            sorts = ['started_at:desc']
            # (diurnalist)
            # We try to limit the query to Gnocchi to only include resources
            # still active (ended_at = None), but there is no way to only
            # ask for resources having a given metric. We therefore might end
            # up throwing out lots of resources. Set a high limit for this
            # reason. If it ends up being possible to query based on the
            # existence of a metric name, we should change to do that.
            resources = gnocchi.resource.search(query=query, limit=self.limit, sorts=sorts)
        except Exception as e:
            self.exit_error('cannot load: ' + str(e))

        measures = []
        for r in resources:
            if not self.metric in r['metrics']:
                continue

            measures += gnocchi.metric.get_measures(self.metric,
                                                   resource_id=r.get('id'),
                                                   start=some_time_ago)

        yield osnag.Metric('measures', len(measures), min=0)

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
    argp.add_argument('-s', '--since', metavar='DURATION', default='5m',
                      help='time range of metrics to examine')
    argp.add_argument('--resource-limit', metavar='LIMIT', default=100,
                      help='max number of resources to poll metrics for')

    argp.add_argument('-w', '--warn', metavar='RANGE', default='1:',
                      help='return warning if number of metrics is outside RANGE (default: 1:, warn if 0)')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='0:',
                      help='return critical if number of metrics is outside RANGE (default 0:, never critical)')

    args = argp.parse_args()

    check = osnag.Check(
        GnocchiMetrics(metric=args.metric, since=args.since, limit=limit,
                       args=args),
        osnag.ScalarContext('measures', args.warn, args.critical),
        osnag.Summary(show=['measures']))
    check.main(verbose=args.verbose, timeout=args.timeout)

if __name__ == '__main__':
    main()
