__author__ = 'meatpuppet'


import libtorrent as lt
import time
import os
import sqlite3
import logging
import datetime

from queue import Queue

#from PyQt4 import QtCore, QtGui
from PyQt4 import QtCore

class TorrentSession(QtCore.QThread):
    statusbar = QtCore.pyqtSignal(str)
    torrent_updated = QtCore.pyqtSignal(object, object)  # handle, torrentinfo
    torrent_deleted = QtCore.pyqtSignal(object)
    torrent_added = QtCore.pyqtSignal(object)

    def __init__(self, queue, savepath="./", loglevel=logging.INFO):
        QtCore.QThread.__init__(self)
        logging.basicConfig(level=loglevel)
        self.statdb = 'stat.db'
        self.settingname = 'defaultsetting'
        self.session = lt.session()
        self.savepath = savepath
        self.handles = []
        self.kju = queue
        self.state_str = ['queued', 'checking', 'downloading metadata', \
              'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
        self.session.set_alert_mask(lt.alert.category_t.all_categories)
        #self.session.set_alert_mask(lt.alert.category_t.storage_notification)

        """-----alert categories-----
        error_notification
        peer_notification
        port_mapping_notification
        storage_notification
        tracker_notification
        debug_notification
        status_notification
        progress_notification
        ip_block_notification
        performance_warning
        stats_notification
        dht_notification
        rss_notification
        all_categories
        """

        self.end = False

        self.status = "stopped"

        self.setup_settings()
        self.setup_db()


    def setup_settings(self):
        #settings
        pesettings = lt.pe_settings()
        pesettings.in_enc_policy = lt.enc_policy.forced
        pesettings.out_enc_policy = lt.enc_policy.forced
        pesettings.allowed_enc_level = lt.enc_level.rc4
        self.session.set_pe_settings(pesettings)

        session_settings = lt.session_settings()

        session_settings.announce_to_all_tiers = True
        session_settings.announce_to_all_trackers = True
        session_settings.connection_speed = 100
        session_settings.peer_connect_timeout = 2
        session_settings.rate_limit_ip_overhead = True
        session_settings.request_timeout = 5
        session_settings.torrent_connect_boost = 100
        self.session.set_settings(session_settings)

        #extensions
        self.session.add_extension(lt.create_metadata_plugin)  # Allows peers to download the metadata (.torren files) from the swarm directly. Makes it possible to join a swarm with just a tracker and info-hash.
        self.session.add_extension(lt.create_ut_metadata_plugin)  # same, utorrent compatible
        self.session.add_extension(lt.create_ut_pex_plugin)  # Exchanges peers between clients.
        self.session.add_extension(lt.create_smart_ban_plugin)  # A plugin that, with a small overhead, can ban peers that sends bad data with very high accuracy. Should eliminate most problems on poisoned torrents.

        self.session.start_dht()
        self.session.start_lsd()
        self.session.start_upnp()
        self.session.start_natpmp()
        #self.session.stop_dht()
        #self.session.stop_lsd()
        #self.session.stop_natpmp()
        #self.session.stop_upnp()

    def checkblocklist(self, path, url=None):
        blockfile = path

        self.statusbar.emit("%s - getting blocklist" % self.status)
        url = "http://john.bitsurge.net/public/biglist.p2p.gz"
        goodbefore = datetime.datetime.now() - datetime.timedelta(hours=5)

        import urllib.request
        if not os.path.exists(blockfile):
            urllib.request.urlretrieve(url, blockfile)
        if datetime.datetime.fromtimestamp(os.path.getctime(blockfile)) < goodbefore:
            urllib.request.urlretrieve(url, blockfile)
        else:
            logging.info("blocklist is still fresh..")


    def setup_blocklist(self):
        blockfile = "blocklist.p2p.gz"

        import gzip
        self.checkblocklist(blockfile)

        self.statusbar.emit("%s - setting blocklist" % self.status)
        try:
            f = gzip.open(blockfile)
        except:
            self.corrupt_list()
            return
        filter = lt.ip_filter()
        exceptions = 0
        for line in f.readlines():
            if line.startswith(b'\n') or line.startswith(b'#'):
                #we dont want empty lines or comments
                pass
            else:
                fromto = line.split(b':')[-1].split(b'-')
                try:
                    filter.add_rule(fromto[0], fromto[1].split(b'\n')[0], 1)
                except:
                    print("exc: %s" % line.split(b':'))
                    exceptions += 1
                    if exceptions > 10:
                        self.corrupt_list()
                        break
        self.session.set_ip_filter(filter)
        self.statusbar.emit("%s" % self.status)
        pass

    def corrupt_list(self):
        self.statusbar.emit("%s - !!! corrupt blocklist?" % self.status)
        exit(0)

    def setup_db(self):
        dbfile = self.statdb
        if not os.path.exists(dbfile):
            conn = sqlite3.connect(dbfile)
            c = conn.cursor()
            c.execute("CREATE TABLE torrents (magnetlink varchar PRIMARY KEY, torrent blob, status blob)")
            c.execute("CREATE TABLE sessionstatus (settingname varchar PRIMARY KEY, status blob)")
            conn.commit()
            conn.close()


    def __del__(self):
        logging.info("torrentsession exits!")
        self.exit(0)

    def safe_shutdown(self):
        self.end=True

    def handle_queue(self):
        while not self.kju.empty():
            d = self.kju.get()
            if d.get('addmagnet'):
                self.add_magnetlink(d.get('addmagnet'))
            elif d.get('addtorrent'):
                self.add_torrent(d.get('addtorrent'))
            elif d.get('deletetorrent'):
                self.delTorrent(d.get('deletetorrent'))
            elif d.get('shutdown'):
                self.end = True
            elif d.get('pause'):
                if self.session.is_paused():
                    self.pause(False)
                else:
                    self.pause(True)

    def pause(self, what):
        if what:
            self.session.pause()
            self.status = 'paused'
        else:
            self.session.resume()
            self.status = 'running'

    def run(self):
        self.statusbar.emit(self.status)
        self.setup_blocklist()
        self.resume()

        self.session.listen_on(6881, 6891)
        self.status = "running"
        """
        print("settings:")
        for attr, value in self.session.get_settings().items():
            print("%s: %s" % (attr, value))
        """

        logging.info("lt läuft...")
        while not self.end:
            # neue events abarbeiten
            self.handle_queue()

            sessionstat = self.session.status()
            self.statusbar.emit("%.2f up, %.2f down @ %s peers - %s" % (sessionstat.upload_rate/1024, sessionstat.download_rate/1024, sessionstat.num_peers, self.status))
            for handle in self.handles:
                stat = handle.status()
                logging.debug("%s - Progress: %s; Peers: %s; State: %s" %
                              (handle.name(), stat.progress * 100, stat.num_peers, self.state_str[stat.state]))
                self.torrent_updated.emit(handle, handle.status())

            for alert in self.session.pop_alerts():
                logging.debug("- %s %s" % (alert.what(), alert.message()))
                if (alert.what() == "save_resume_data_alert")\
                        or (alert.what() == "save_resume_data_failed_alert"):
                    handle = alert.handle

                    self.session.remove_torrent(handle)
                    self.handles.remove(handle)
            time.sleep(1)

        logging.debug("ending")
        # ending - save stuff
        # erase previous torrents first
        self.erase_all_torrents_from_db()
        # then trigger saving resume data
        for handle in self.handles:
            handle.save_resume_data(lt.save_resume_flags_t.flush_disk_cache)
        # set alert mast to get the right alerts
        self.session.set_alert_mask(lt.alert.category_t.storage_notification)
        # wait for everything to save and finish!
        while self.handles:
            for alert in self.session.pop_alerts():
                logging.debug("- %s %s" % (alert.what(), alert.message()))
                if (alert.what() == "save_resume_data_alert"):
                    handle = alert.handle
                    self.save(handle, alert.resume_data)
                    logging.debug("removing %s" % handle.name())
                    self.session.remove_torrent(handle)
                    #print(self.session.wait_for_alert(1000))
                    self.handles.remove(handle)
                elif (alert.what() == "save_resume_data_failed_alert"):
                    handle = alert.handle
                    logging.debug("removing %s" % handle.name())
                    self.session.remove_torrent(handle)
                    self.handles.remove(handle)

        self.save_state()
        time.sleep(1)
        logging.debug("handles at return: %s" % self.handles)
        return

    def add_magnetlink(self, magnetlink):
        logging.info("adding mlink")
        handle = lt.add_magnet_uri(self.session, magnetlink, {'save_path': self.savepath})
        self.handles.append(handle)
        self.torrent_added.emit(handle)

    def add_torrent(self, torrentfilepath):
        logging.info("adding torrentfile")
        #info = lt.torrent_info(torrentfilepath)
        info = lt.torrent_info(lt.bdecode(open(torrentfilepath, 'rb').read()))
        self.add_torrent_by_info(info)

    def add_torrent_by_info(self, torrentinfo, resumedata=None):
        if not resumedata:
            handle = self.session.add_torrent({'ti': torrentinfo, 'save_path': self.savepath})
        else:
            handle = self.session.add_torrent({'ti': torrentinfo, 'resume_data': resumedata,
                                               'save_path': self.savepath})

        handle
        self.handles.append(handle)
        print("emitting 'added'...")
        self.torrent_added.emit(handle)

    def delTorrent(self, handle):
        """saves the resume data for torrent
        when done, save_resume_data_alert will be thrown, then its safe to really delete the torrent
        """
        handle.save_resume_data(lt.save_resume_flags_t.flush_disk_cache) #creates save_resume_data_alert
        self.torrent_deleted.emit(handle)


    def save(self, handle, resume_data):
        torrent = lt.create_torrent(handle.get_torrent_info())
        torfile = lt.bencode(torrent.generate())
        magnet = lt.make_magnet_uri(handle.get_torrent_info())
        status = lt.bencode(resume_data)

        db = sqlite3.connect(self.statdb)
        # create table torrents (magnetlink varchar(256), torrent blob, status blob);
        c = db.cursor()
        c.execute("INSERT or REPLACE INTO torrents VALUES (?, ?, ?)", (magnet, sqlite3.Binary(torfile), sqlite3.Binary(status)))
        db.commit()
        db.close()

    def save_state(self):
        # create table sessionstatus (status blob)
        entry = self.session.save_state()
        encentry = lt.bencode(entry)
        db = sqlite3.connect(self.statdb)
        # create table torrents (magnetlink varchar(256), torrent blob, status blob);
        c = db.cursor()
        c.execute("INSERT or REPLACE INTO sessionstatus VALUES (?, ?)", (self.settingname, sqlite3.Binary(encentry)))
        db.commit()
        db.close()

    def resume(self):
        #load state
        db = sqlite3.connect(self.statdb)
        c = db.cursor()
        erg = c.execute("SELECT * FROM sessionstatus")
        f = erg.fetchone()
        if f:
            encsettings = f[1]
            settings = lt.bdecode(encsettings)
            self.session.load_state(settings)
            logging.info("loaded settings: %s" % settings)

        #load last torrents
        erg = c.execute("SELECT * FROM torrents")
        for t in erg.fetchall():
            logging.info("importing %s" % t[0])
            entry = lt.bdecode(t[1])
            fastresumedata = t[2]
            torrentinfo = lt.torrent_info(entry)
            self.add_torrent_by_info(torrentinfo, fastresumedata)
        db.close()
        pass

    def erase_all_torrents_from_db(self):
        db = sqlite3.connect(self.statdb)
        c = db.cursor()
        c.execute("DELETE FROM torrents")
        db.commit()
        db.close()
