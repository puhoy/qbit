__author__ = 'meatpuppet'

import libtorrent as lt
import time, sys
from PyQt4 import QtCore

class TorrentHandleThread(QtCore.QThread):
    updatestrsig = QtCore.pyqtSignal(str)
    def __init__(self, session, magnetlink, savepath):
        QtCore.QThread.__init__(self)
        self.handle = lt.add_magnet_uri(session, magnetlink, {'save_path': savepath})

        print(self.handle.get_peer_info())

        self.state_str = ['queued', 'checking', 'downloading metadata', \
              'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']

    def __del__(self):
        self.wait()

    def run(self):
        print('getting metadata for', self.handle.name())
        self.handle.connect_peer(("192.168.178.20", 51413), 6881)
        s = self.handle.status()
        # metadaten holen
        while (not self.handle.has_metadata()):
            time.sleep(1)
            self.updatestrsig.emit(
                '%s -  %.2f peers: %s complete (%s)' %
                (self.handle.name(), s.progress * 100, s.num_peers, self.state_str[s.state])
            )
        info = self.handle.get_torrent_info()

        while (not self.handle.is_seed()):
            """print('\r%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % \
            (s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, \
            s.num_peers, state_str[s.state]),)"""
            time.sleep(1)
            self.updatestrsig.emit(
                '%s - %.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' %
                (self.handle.name(), s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000,
                 s.num_peers, self.state_str[s.state])
            )
            print(
                '%s - %.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' %
                (self.handle.name(), s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000,
                 s.num_peers, self.state_str[s.state])
            )
            sys.stdout.flush()



