

class Campaigns:
    def __init__(self, campaign_file):
        self.keywords = {}
        self.campaigns = {}
        self.parse(campaign_file)

    def parse(self, campaign_file):
        contents = open(campaign_file, 'r')
        url = None
        line = contents.readline()
        while line:
            line = line.strip()
            if not url:
                url = line
                self.campaigns[url] = {}
            elif line == '':
                url = None
            else:
                self.campaigns[url][line] = None
                if self.keywords.has_key(line):
                    self.keywords[line].append(url)
                else:
                    self.keywords[line] = [url]

            line = contents.readline()

    def set_rank(self, url, keyword, rank):
        try:
            if not self.campaigns[url][keyword]:
                self.campaigns[url][keyword] = rank
        except:
            pass

    def get_campaigns(self):
        return self.campaigns

    def get_keywords(self):
        return self.keywords
