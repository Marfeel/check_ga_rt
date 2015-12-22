import argparse
import nagiosplugin
import httplib2

from oauth2client import file
from oauth2client import client
from oauth2client import tools
from apiclient.discovery import build

class RealtimeAnalytics(nagiosplugin.Resource):

    def __init__(self, credentials, filters, view, dimensions):
        self.filters = filters
        self.view = view
        self.credentials = credentials
        self.dimensions = dimensions

    def probe(self):

            http = httplib2.Http()
            http = self.credentials.authorize(http)
            service = build('analytics', 'v3', http=http)
            request = service.data().realtime().get(
                ids="ga:%s"%(self.view),
                metrics="rt:activeVisitors",
                dimensions=self.dimensions,
                filters=self.filters)
            response = request.execute()
            yield nagiosplugin.Metric('TotalErrors',int(response["totalsForAllResults"]["rt:activeVisitors"]),min=0, context='activeVisitors')
            for row in response["rows"]:
                yield nagiosplugin.Metric(row[0],int(row[1]),min=0, context='activeVisitors')

class LoadSummary(nagiosplugin.Summary):

    def ok(self, results):
        msgs = ''
        for result in results:
            msgs += '{0} \n'.format(result)
        return msgs


@nagiosplugin.guarded
def main():

    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-w', '--warning', type=int, default=0,
                      help='return warning if activeVisitors is outside RANGE')
    argp.add_argument('-c', '--critical', type=int, default=0,
                      help='return critical if activeVisitors is outside RANGE')
    argp.add_argument('-C', '--credentialsFile', action='store',required=True)
    argp.add_argument('-t', '--timeout', type=int, default=20,
                      help='abort after this number of seconds')
    argp.add_argument('-D', '--authData', action='store',required=True)
    argp.add_argument('-F', '--filters', action='store',required=True)
    argp.add_argument('-d', '--dimensions', action='store',required=True)
    argp.add_argument('-V', '--view', action='store',required=True)
    argp.add_argument('-v', '--verbose', action='count', default=0,
                      help='increase output verbosity (use up to 3 times)')

    args = argp.parse_args()
    check = nagiosplugin.Check(
        RealtimeAnalytics(authenticate(args.authData, args.credentialsFile),
                          args.filters,
                          args.view,
                          args.dimensions),
        nagiosplugin.ScalarContext('activeVisitors',
                                   nagiosplugin.Range("%s" % args.warning),
                                   nagiosplugin.Range("%s" % args.critical)),
        LoadSummary())
    check.main(verbose=args.verbose,timeout=args.timeout)



def authenticate(authData, credentialsFile):
    storage = file.Storage(authData)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(
            client.flow_from_clientsecrets(
                credentialsFile,
                scope=[
                    'https://www.googleapis.com/auth/analytics.readonly',
                ],
                message=tools.message_if_missing(credentialsFile)),
            storage,
            tools.argparser.parse_args(args=[]))
    return credentials

if __name__ == '__main__':
    main()