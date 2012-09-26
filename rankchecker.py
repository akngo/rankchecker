import os
import time
import traceback
import sys

from collections import deque

from campaigns import Campaigns
from xgoogle.search import GoogleSearch
from xgoogle.search import SearchError

verbose = True

class RankChecker:
    def __init__(self, config, campaigns):
        self.config = config
        self.campaigns = campaigns
        self.init_proxies(config['proxies'])

    def init_proxies(self, proxies):
        self.proxies = deque(proxies)
        self.failed_proxies = {}
        for proxy in proxies:
            self.failed_proxies[proxy] = 0

    def get_ranks(self):
        for keyword, urls in campaigns.get_keywords().iteritems():
            gs = GoogleSearch(keyword)
            gs.results_per_page = self.config['limits']['results_per_page']

            sys.stderr.write('\n\nChecking keyword: %s\n' % keyword)
            results = self.get_results(gs)
            offset = 1
            query_count = 0
            while len(urls) > 0 and results:
                # Display a period for every hit we make to Google
                if query_count % 5 == 0: sys.stderr.write(' ')
                sys.stderr.write('.')

                for rank, row in enumerate(results):
                    if (len(urls) > 0):
                        # Find results containing one of our sites
                        found = filter(lambda x: row.url.find(x) != -1, urls)
                        for entry in found:
                            campaigns.set_rank(entry, keyword, rank + offset)

                        # Using sets to get remaining sites to check for
                        urls = list(set(urls) - set(found))
                    else:
                        break

                # Don't collect another time if no more URLs are left to check
                offset += len(results)
                results = None

                # We want to sleep here regardless because we might scrape
                # really fast if all the results are on the first page
                time.sleep(self.config['limits']['delay'])

                # Only check if there are sites remaining and we have not
                # surpassed our maximum configured depth
                if (len(urls) > 0 and
                        offset <= self.config['limits']['search_depth'] + 1):
                    results = self.get_results(gs)
                    query_count += 1
                elif verbose:
                    sys.stderr.write('Not retrieving more results\n')

                if verbose:
                    sys.stderr.write('URLs: %s\n' % ', '.join(urls))
                    if results:
                        sys.stderr.write('Results: %s\n' % len(results))

    def get_results(self, gs):
        # Setting the proxy by utilizing the http_proxy environment variable
        while len(self.proxies) > 0:
            proxy = self.proxies[0]
            self.proxies.rotate(-1)
            if verbose:
                sys.stderr.write('Using proxy: %s\n' % proxy)
            os.environ['http_proxy'] = proxy

            try:
                result = gs.get_results()

                # Success will mean we need to reset failed attempts to 0
                self.failed_proxies[proxy] = 0

                return result
            except SearchError, e:
                self.failed_proxies[proxy] += 1

                # Failed 3 consecutive times, remove from list of proxies
                cfg = self.config
                if (self.failed_proxies[proxy] >=
                        cfg['limits']['proxy_retries']):
                    # pop() from the right, which is the targeted proxy
                    # because of the rotate(-1) we did earlier
                    self.proxies.pop()

                # Just to be safe, we sleep before retrying
                time.sleep(self.config['limits']['delay'])
                pass

        # If we reach here and the length of failed_proxies is not 0, it means
        # that we have failed on all the proxies. We throw an exception
        if len(self.failed_proxies) > 0:
            raise Exception('Ran out of proxies')

        # Normal case, no proxies are used
        return gs.get_results()


if __name__ == '__main__':
    import argparse
    from config import Config

    parser = argparse.ArgumentParser(description='Check your ranks on Google')
    parser.add_argument('--config',
                        default='config.json',
                        help='the name of the config file')
    parser.add_argument('--campaign',
                        default='campaigns.ini',
                        help='the name of the campaign file')
    args = parser.parse_args()

    config = Config(args.config).get_config()
    if verbose:
        print 'Delay between requests: %s\n' % config['limits']['delay']

    campaigns = Campaigns(args.campaign)
    checker = RankChecker(config, campaigns)

    try:
        checker.get_ranks()
    except:
        # Ignore all errors and hopefully it can print out whatever it can
        # before exiting
        traceback.print_exc()
        pass

    sys.stderr.write('\n\nRanking results:\n')
    for campaign, keywords in campaigns.get_campaigns().iteritems():
        print(campaign)
        for keyword,rank in keywords.iteritems():
            print("    %s\t%s" % ((rank or 'N/A'), keyword))

        print


