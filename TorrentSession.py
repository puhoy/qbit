__author__ = 'meatpuppet'


import libtorrent as lt
import time
import os


from PyQt4 import QtCore

class TorrentSession(QtCore.QThread):
    def __init__(self, savepath="./"):
        QtCore.QThread.__init__(self)
        self.stat_file = 'stat.json'
        self.session = lt.session()
        self.savepath = savepath
        self.handles = []
        self.state_str = ['queued', 'checking', 'downloading metadata', \
              'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
        self.session.set_alert_mask(lt.alert.category_t.all_categories)
        #self.session.set_alert_mask(lt.alert.category_t.storage_notification)
        self.end=False

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

    def __del__(self):
        print("torrentsession exits!")
        self.exit(0)

    def safe_shutdown(self):
        self.end=True

    def run(self):
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


        self.session.listen_on(6881, 6891)
        """
        print("settings:")
        for attr, value in self.session.get_settings().items():
            print("%s: %s" % (attr, value))
        """

        print("läuft...")
        while not self.end:
            for handle in self.handles:
                stat = handle.get('handle').status()
                #print("%s - Progress: %s; Peers: %s; State: %s" % (handle.get('handle').name(), stat.progress * 100, stat.num_peers, self.state_str[stat.state]))
                handle.get('item').setText("%s - "
                                           "Progress: %.2f \n-- %s -- "
                                           "total upload: %sMB "
                                           "Peers: %s, U:%.2f D:%.2f_|" %
                                           (handle.get('handle').name(),
                                            stat.progress * 100, self.state_str[stat.state],
                                            stat.total_upload/1024/1024,
                                            stat.num_peers, stat.upload_rate, stat.download_rate))
            for alert in self.session.pop_alerts():
                print("- %s %s" % (alert.what(), alert.message()))
                if (alert.what() == "save_resume_data_alert"):
                    #print("here i should save the resume data..")  # TODO
                    #print("%s: %s" % (alert.what(), alert.message()))
                    handle = alert.handle
                    print("removing %s" % handle.name())
                    self.session.remove_torrent(handle)
                    #print(self.session.wait_for_alert(1000))
                    for h in self.handles:
                        if h.get('handle') == handle:
                            self.handles.remove(h)
                            break
                elif (alert.what() == "save_resume_data_failed_alert"):
                    handle = alert.handle
                    print("removing %s" % handle.name())
                    self.session.remove_torrent(handle)
                    for h in self.handles:
                        if h.get('handle') == handle:
                            self.handles.remove(h)
                            break
            #print(self.session.get_torrents())
                    #self.handles.remove(handle)

            time.sleep(1)

        # ending - save stuff
        for handle in self.handles:
            handle.get('handle').save_resume_data(lt.save_resume_flags_t.flush_disk_cache)

        while self.handles is not []:
            for alert in self.session.pop_alerts():
                print("- %s %s" % (alert.what(), alert.message()))
                if (alert.what() == "save_resume_data_alert"):
                    #print("here i should save the resume data..")  # TODO
                    #print("%s: %s" % (alert.what(), alert.message()))
                    handle = alert.handle
                    self.save(alert.resume_data)
                    print("removing %s" % handle.name())
                    self.session.remove_torrent(handle)
                    #print(self.session.wait_for_alert(1000))
                    for h in self.handles:
                        if h.get('handle') == handle:
                            self.handles.remove(h)
                            break
                elif (alert.what() == "save_resume_data_failed_alert"):
                    handle = alert.handle
                    print("removing %s" % handle.name())
                    self.session.remove_torrent(handle)
                    for h in self.handles:
                        if h.get('handle') == handle:
                            self.handles.remove(h)
                            break
        print("alles gespeichert")
        return True


    def add_magnetlink(self, magnetlink, widgetitem):
        print("adding mlink")
        handle = lt.add_magnet_uri(self.session, magnetlink, {'save_path': self.savepath})
        self.handles.append({'handle': handle, 'item': widgetitem})

    def add_torrent(self, torrentfilepath, widgetitem):
        print("adding torrentfile")
        info = lt.torrent_info(torrentfilepath)
        handle = self.session.add_torrent({'ti': info, 'save_path': self.savepath})
        self.handles.append({'handle': handle, 'item': widgetitem})

    def delTorrent(self, widgetitem):
        """saves the resume data for torrent
        when done, save_resume_data_alert will be thrown, then its safe to really delete the torrent
        """
        for handle in self.handles:
            if handle.get('item') == widgetitem:
                handle.get('handle').save_resume_data(lt.save_resume_flags_t.flush_disk_cache) #creates save_resume_data_alert
                #print(self.session.torrent_deleted_alert())

    def save(self, resume_data):
        if not os.path.exists("store"):
            os.makedirs("store")
        out_file = open(os.path.join("path", resume_data.get('info-hash')), "ab")
        enc = lt.bencode(resume_data)
        out_file.write(enc)
        out_file.close()

    def resume(self):
        pass

"""
class Torrent():
    def __init__(self, handle, widgetitem):
        self.widgetitem = widgetitem
        self.handle = handle
"""

""" download_rate_limit(self, session, *args, **kwargs): # real signature unknown; NOTE: unreliably restored from __doc__
        download_rate_limit( (session)arg1) -> int :


"""

