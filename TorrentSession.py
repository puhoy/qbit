__author__ = 'meatpuppet'


import libtorrent as lt
import time
import sys





class TorrentSession():
    def __init__(self, savepath="./"):
        self.session = lt.session()
        self.session.listen_on(6881, 6891)

        self.savepath=savepath

        self.handles = []

"""
 download_rate_limit(self, session, *args, **kwargs): # real signature unknown; NOTE: unreliably restored from __doc__
        download_rate_limit( (session)arg1) -> int :


"""

