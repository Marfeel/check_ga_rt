import argparse
import nagiosplugin
import httplib2

from oauth2client import file
from oauth2client import client
from oauth2client import tools
from apiclient.discovery import build

class RealtimeAnalytics(nagiosplugin.Resource):

    def __init__(self, credentials, filters, view):
        self.filters = filters
        self.view = view
        self.credentials = credentials

    def probe(self):

            http = httplib2.Http()
            http = self.credentials.authorize(http)
            service = build('analytics', 'v3', http=http)
            request = service.data().realtime().get(
                ids="ga:%s"%(self.view),
                metrics="rt:activeVisitors",
                filters=self.filters)
            response = request.execute()
            activeVisitors =  int(response["totalsForAllResults"]["rt:activeVisitors"])
            return [nagiosplugin.Metric("activeVisitors", activeVisitors, min=0,context='activeVisitors')]


def main():

    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-w', '--warning', metavar='RANGE', default='',
                      help='return warning if activeVisitors is outside RANGE')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='',
                      help='return critical if activeVisitors is outside RANGE')
    argp.add_argument('-C', '--credentialsFile', action='store',required=True)
    argp.add_argument('-D', '--authData', action='store',required=True)
    argp.add_argument('-F', '--filters', action='store',required=True)
    argp.add_argument('-V', '--view', action='store',required=True)
    argp.add_argument('-v', '--verbose', action='count', default=0,
                      help='increase output verbosity (use up to 3 times)')

    args = argp.parse_args()
    check = nagiosplugin.Check(
        RealtimeAnalytics(authenticate(args.authData, args.credentialsFile),
                          args.filters,
                          args.view),
        nagiosplugin.ScalarContext('activeVisitors',args.warning, args.critical))
    check.main(verbose=args.verbose)



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