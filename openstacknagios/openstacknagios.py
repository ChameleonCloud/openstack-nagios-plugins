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

from nagiosplugin import Resource as NagiosResource
from nagiosplugin import Summary as NagiosSummary
from nagiosplugin import Check
from nagiosplugin import Metric
from nagiosplugin import guarded
from nagiosplugin import ScalarContext

from argparse import ArgumentParser as ArgArgumentParser

from keystoneauth1 import adapter
from keystoneauth1 import loading

from os import environ as env
import sys


class Resource(NagiosResource):
    """
    Base definition of OpenStack Nagios resource
    """
    DEFAULT_API_VERSION = '2'

    def __init__(self, args=None):
        NagiosResource.__init__(self)
        self.api_version = args.os_api_version or self.DEFAULT_API_VERSION

        auth = loading.cli.load_from_argparse_arguments(args)
        sess = loading.session.load_from_argparse_arguments(args)
        # TODO: loading Adapter parameters automatically is not yet supported.
        # This is due to missing functionality in keystoneauth
        self.session = adapter.Adapter(sess, auth=auth,
            service_type=args.os_service_type,
            service_name=args.os_service_name,
            interface=args.os_interface,
            region_name=args.os_region_name,
            endpoint_override=args.os_endpoint_override,
            version=self.api_version)

    def exit_error(self, text):
       print 'UNKNOWN - ' + text
       sys.exit(3)


class Summary(NagiosSummary):
    """
    Create status line with info
    """
    def __init__(self, show):
        self.show = show
        super(NagiosSummary, self).__init__()

    def ok(self, results):
        return '[' + ' '.join(
            r + ':' + str(results[r].metric) for r in self.show) + ']'

    def problem(self, results):
        return str(results.first_significant) + '[' + ' '.join(
            r + ':' + str(results[r].metric) for r in self.show) + ']'


class ArgumentParser(ArgArgumentParser):
    def __init__(self, description, epilog=''):
        ArgArgumentParser.__init__(self, description=description, epilog=epilog)
        argv = sys.argv[1:]
        loading.cli.register_argparse_arguments(self, argv)
        loading.session.register_argparse_arguments(self)
        loading.adapter.register_argparse_arguments(self)

        self.add_argument('-v', '--verbose', action='count', default=0,
                          help='increase output verbosity (use up to 3 times)'
                               '(not everywhere implemented)')
