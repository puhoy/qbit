__author__ = 'meatpuppet'
import sys
from PyQt4 import QtGui, uic, QtCore
from AddTorrentWidget import AddTorrentWidget
from TorrentSession import TorrentSession
from TorrentHandle import TorrentHandleThread
from Sure import SureDialog

main_window = uic.loadUiType("test.ui")[0]                 # Load the UI

class TestWidget(QtGui.QMainWindow, main_window):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.torrents = []

        #knöpfe verkabeln
        self.btn_addTorrent.clicked.connect(self.btn_addTorrent_clicked)
        self.btn_deleteTorrent.clicked.connect(self.btn_deleteTorrent_clicked)
        #events

        self.ts = TorrentSession()
        self.threadPool = {}

    @QtCore.pyqtSlot()
    def btn_addTorrent_clicked(self):
        add_torrent_widget = AddTorrentWidget(self)
        add_torrent_widget.mlink.connect(self.torrent_added)
        add_torrent_widget.show()


    @QtCore.pyqtSlot(str)
    def torrent_added(self, mlink):
        t = TorrentHandleThread(self.ts.session, mlink, self.ts.savepath)

        item = QtGui.QListWidgetItem()
        t.updatestrsig.connect(item.setText)
        self.lstWdgt_torrents.addItem(item)
        self.threadPool[item] = t
        t.start()
        pass

    def btn_deleteTorrent_clicked(self):

        item = self.lstWdgt_torrents.selectedItems()[0]
        if item is not None:
            ok = SureDialog.getOk()
            if not ok:
                return
            t = self.threadpool[{item}]
            del t
            del item



        pass



def main():
    app = QtGui.QApplication(sys.argv)
    ex = TestWidget()
    ex.show()
    ret = app.exec_()
    print("deleting Torrent Session..")
    del ex.ts
    print("...aaaand deleted!")
    sys.exit(ret)



if __name__ == '__main__':
    main()
