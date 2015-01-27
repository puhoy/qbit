__author__ = 'meatpuppet'
import sys
from PyQt4 import QtGui, uic, QtCore
from AddTorrentWidget import AddTorrentWidget
from TorrentSession import TorrentSession
import libtorrent as lt


main_window = uic.loadUiType("test.ui")[0]                 # Load the UI

class TestWidget(QtGui.QMainWindow, main_window):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.torrents = []

        #knöpfe verkabeln
        self.btn_addMagnetLink.clicked.connect(self.btn_addMagnetLink_clicked)
        self.btn_deleteTorrent.clicked.connect(self.btn_deleteTorrent_clicked)
        self.btn_addTorrentFile.clicked.connect(self.btn_addTorrentFile_clicked)
        #events

        self.ts = TorrentSession()
        self.ts.start()

    @QtCore.pyqtSlot()
    def btn_addMagnetLink_clicked(self):
        add_torrent_widget = AddTorrentWidget(self)
        add_torrent_widget.mlink.connect(self.addByMagnet)
        add_torrent_widget.show()

    @QtCore.pyqtSlot()
    def btn_addTorrentFile_clicked(self):
        path = QtGui.QFileDialog.getOpenFileName()
        item = QtGui.QListWidgetItem()
        try:
            lt.torrent_info(path)
        except:
            QtGui.QMessageBox.question(self, 'Message',
                                           "Something happend while adding...\n"
                                           "torrent already added? corrupt file?",
                                           QtGui.QMessageBox.Ok)
            return
        self.lstWdgt_torrents.addItem(item)
        self.addByTorrentFile(path, item)

    def addByMagnet(self, mlink):
        item = QtGui.QListWidgetItem()
        self.lstWdgt_torrents.addItem(item)
        self.ts.add_magnetlink(mlink, item)
        pass

    def addByTorrentFile(self, fpath, item):
        self.ts.add_torrent(fpath, item)

    def btn_deleteTorrent_clicked(self):
        item = self.lstWdgt_torrents.selectedItems()[0]
        if item is not None:
            reply = QtGui.QMessageBox.question(self, 'Message',
                                           "really delete?",
                                           QtGui.QMessageBox.Yes,
                                           QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.No:
                return
            self.ts.delTorrent(item)
            self.lstWdgt_torrents.takeItem(self.lstWdgt_torrents.row(item))

        pass

def main():
    app = QtGui.QApplication(sys.argv)
    ex = TestWidget()
    ex.show()
    ret = app.exec_()
    print("deleting Torrent Session..")
    ex.ts.safe_shutdown()
    ex.ts.wait()
    print("...aaaand deleted!")
    sys.exit(ret)


if __name__ == '__main__':
    main()
