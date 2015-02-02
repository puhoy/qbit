__author__ = 'meatpuppet'
import sys
from PyQt4 import QtGui, uic, QtCore, Qt
from addTorrentWidget import AddTorrentWidget
from TorrentSession import TorrentSession
import libtorrent as lt

from queue import Queue

main_window = uic.loadUiType("qbit_main.ui")[0]                 # Load the UI

class TestWidget(QtGui.QMainWindow, main_window):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.items = {}

        self.kju = Queue()

        #self.lstWdgt_torrents.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        #self.lstWdgt_torrents.customContextMenuRequested.connect(self.handleContext)

        #knoepfe verkabeln
        self.btn_addMagnetLink.clicked.connect(self.btn_addMagnetLink_clicked)
        self.btn_deleteTorrent.clicked.connect(self.btn_deleteTorrent_clicked)
        self.btn_addTorrentFile.clicked.connect(self.btn_addTorrentFile_clicked)


        self.ts = TorrentSession(self.kju)

        self.ts.statusbar.connect(self.statusBar.showMessage)
        self.ts.torrent_updated.connect(self.updateitem)
        self.ts.torrent_deleted.connect(self.deleteitem)

        self.ts.start()

    def handleContext(self, pos):
        item = self.lstWdgt_torrents.itemAt(pos)
        if item is not None:
            menu = QtGui.QMenu("Context Menu", self)
            menu.addAction("FOO")
            ret = menu.exec_(self.lstWdgt_torrents.mapToGlobal(pos))


    @QtCore.pyqtSlot()
    def btn_addMagnetLink_clicked(self):
        add_torrent_widget = AddTorrentWidget(self)
        add_torrent_widget.mlink.connect(self.addByMagnet)
        add_torrent_widget.show()

    @QtCore.pyqtSlot()
    def btn_addTorrentFile_clicked(self):
        path = QtGui.QFileDialog.getOpenFileName()
        if path is "":
            return
        try:
            lt.torrent_info(lt.bdecode(open(path, 'rb').read()))
        except RuntimeError as e:
            QtGui.QMessageBox.question(self, 'Runtime Error',
                                           "%s" % e,
                                           QtGui.QMessageBox.Ok)
            return
        except:
            QtGui.QMessageBox.question(self, 'Error while adding',
                                           "Something bad happend while trying to add...\n",
                                           QtGui.QMessageBox.Ok)
        self.addByTorrentFile(path)

    def addByMagnet(self, mlink):
        self.kju.put({'addmagnet': mlink})

    def addByTorrentFile(self, fpath):
        self.kju.put({'addtorrent': fpath})

    def btn_deleteTorrent_clicked(self):
        items = self.lstWdgt_torrents.selectedItems()
        if items is not None:
            reply = QtGui.QMessageBox.question(self, 'Message',
                                           "really delete?",
                                           QtGui.QMessageBox.Yes,
                                           QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                for item in items:
                    for k in self.items.keys():  # k == handle
                        if self.items[k] == item:
                            self.kju.put({'deletetorrent': k})
                #self.ts.delTorrent(item)
                #self.lstWdgt_torrents.takeItem(self.lstWdgt_torrents.row(item))


    def makeitem(self, handle):
        item = QtGui.QListWidgetItem()
        self.items[handle] = item
        self.lstWdgt_torrents.addItem(item)

    @QtCore.pyqtSlot(object, str)
    def updateitem(self, handle, values):
        if not self.items.get(handle):
            self.makeitem(handle)
        self.items.get(handle).setText(values)

    @QtCore.pyqtSlot(object)
    def deleteitem(self, handle):
        item = self.items[handle]
        self.lstWdgt_torrents.takeItem(self.lstWdgt_torrents.row(item))
        self.items.pop(handle)



def main():
    app = QtGui.QApplication(sys.argv)
    ex = TestWidget()
    ex.show()
    ret = app.exec_()
    print("deleting Torrent Session..")
    ex.kju.put({'shutdown': True})
    ex.ts.wait()
    print("...aaaand deleted!")
    sys.exit(ret)


if __name__ == '__main__':
    main()
