__author__ = 'meatpuppet'
import gzip, datetime, os, logging
import urllib.request


class Blocklist():
    def __init__(self, blocklist_filepath="blocklist.p2p.gz", url="http://john.bitsurge.net/public/biglist.p2p.gz"):
        self.blocklist_filepath = blocklist_filepath
        self.url = url
        self.rules = None

    def setup_rules(self):
        ready_to_parse = True
        if not self._is_up_to_date():
            if not self._download_list():
                return False

        self.rules = self._parse_blocklist()
        if not self.rules:
            #if we got here, the gz file is broken - maybe download again?
            return False
        return True

    def get_rules(self):
        return self.rules

    def _is_up_to_date(self, old_after_hours=5):
        """checks if the blocklist file exists and fetches it doesnt exist or its old"""
        good_before = datetime.datetime.now() - datetime.timedelta(hours=old_after_hours)
        if not os.path.exists(self.blocklist_filepath):
            return False
        if datetime.datetime.fromtimestamp(os.path.getctime(self.blocklist_filepath)) < good_before:
            return False
        else:
            logging.info("blocklist is still fresh..")
            return True

    def _download_list(self):
        try:
            urllib.request.urlretrieve(self.url, self.blocklist_filepath)
            return True
        except:
            logging.info("could not download blocklist!")
            return False

    def _parse_blocklist(self):

        try:
            f = gzip.open(self.blocklist_filepath)
        except:
            logging.debug("could not gzip-open blocklist!")
            return None
        rules = []
        for line in f.readlines():
            if line.startswith(b'\n') or line.startswith(b'#'):
                #we dont want empty lines or comments
                pass
            else:
                fromto = line.split(b':')[-1].split(b'-')
                rules.append({'from': fromto[0],
                                   'to': fromto[1].split(b'\n')[0],
                                   'block': 1})
        return rules

