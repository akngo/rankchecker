import time
import sys

from campaigns import Campaigns
from xgoogle.search import GoogleSearch

class RankChecker:
    def __init__(self, config, campaigns):
        self.config = config
        self.campaigns = campaigns

    def get_ranks(self):
        for keyword, urls in campaigns.get_keywords().iteritems():
            gs = GoogleSearch(keyword)
            gs.results_per_page = self.config['limits']['results_per_page']

            sys.stderr.write('\n\nChecking keyword: %s\n' % keyword)
            results = gs.get_results()
            offset = 1
            while len(urls) > 0 and results:
                # Display a period for every hit we make to Google
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
                    results = gs.get_results()


if __name__ == '__main__':
    from config import Config
    config = Config('config.json').get_config()
    #print config['limits']['results_per_page']
    #print config['limits']['delay']
    campaigns = Campaigns('campaigns.ini')
    checker = RankChecker(config, campaigns)

    try:
        checker.get_ranks()
    except:
        # Ignore all errors and hopefully it can print out whatever it can
        # before exiting
        pass

    sys.stderr.write('\n\nRanking results:\n')
    for campaign, keywords in campaigns.get_campaigns().iteritems():
        print(campaign)
        for keyword,rank in keywords.iteritems():
            print("    %s\t%s" % ((rank or 'N/A'), keyword))

        print


