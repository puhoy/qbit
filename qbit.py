__author__ = 'meatpuppet'
import sys
from PyQt4 import QtGui, uic, QtCore
from addTorrentWidget import AddTorrentWidget
from TorrentSession import TorrentSession
import libtorrent as lt

from queue import Queue
import logging

from systray import SystemTrayIcon
from gui import qbit_main

#main_window = uic.loadUiType("qbit_main.ui")[0]                 # Load the UI

class Qbit_main(QtGui.QMainWindow, qbit_main.Ui_MainWindow):
    def __init__(self, parent=None):
        super(Qbit_main, self).__init__(parent)
        #QtGui.QMainWindow.__init__(self, parent)
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

        self.state_str = self.ts.state_str

        self.ts.statusbar.connect(self.statusBar.showMessage)
        self.ts.torrent_updated.connect(self.updateitem)
        self.ts.torrent_deleted.connect(self.deleteitem)

        self.ts.start()

    def handleContext(self, pos):
        item = self.lstWdgt_downloading.itemAt(pos)
        if item is not None:
            menu = QtGui.QMenu("Context Menu", self)
            menu.addAction("FOO")
            ret = menu.exec_(self.lstWdgt_downloading.mapToGlobal(pos))


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
        items = self.lstWdgt_downloading.selectedItems()
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
                #self.lstWdgt_downloading.takeItem(self.lstWdgt_downloading.row(item))


    def makeitem(self, handle):
        item = QtGui.QListWidgetItem()
        item.setSizeHint(QtCore.QSize(item.sizeHint().width(), 30))

        bar = QtGui.QProgressBar()
        bar.setVisible(True)
        #bar.setMinimumHeight(30)

        #list = QtGui.QListWidget
        self.lstWdgt_downloading.addItem(item)
        self.lstWdgt_downloading.setItemWidget(item, bar)
        self.items[handle] = (item, bar)

    @QtCore.pyqtSlot(object, object)
    def updateitem(self, handle, status):
        if not self.items.get(handle):
            self.makeitem(handle)
        stat = status
        values =  "%s - " \
        "Progress: %.2f \n-- %s -- " \
        "total upload: %.2fMb " \
        "Peers: %s, U:%.2f D:%.2f_|" % \
        (handle.name(),
         stat.progress * 100, self.state_str[stat.state],
         stat.total_upload/1024/1024,
         stat.num_peers, stat.upload_rate/1024, stat.download_rate/1024)
        self.items.get(handle)[1].setValue(stat.progress * 100)
        self.items.get(handle)[1].setFormat(values)



    @QtCore.pyqtSlot(object)
    def deleteitem(self, handle):
        (item, row) = self.items[handle]
        self.lstWdgt_downloading.takeItem(self.lstWdgt_downloading.row(item))
        self.items.pop(handle)

def main():
    app = QtGui.QApplication(sys.argv)
    main = Qbit_main()
    main.show()
    style = app.style()
    icon = QtGui.QIcon(style.standardPixmap(QtGui.QStyle.SP_ArrowDown))
    trayIcon = SystemTrayIcon(icon)
    trayIcon.show()
    ret = app.exec_()
    print("deleting Torrent Session..")
    main.kju.put({'shutdown': True})
    main.ts.wait()
    print("...aaaand deleted!")
    sys.exit(ret)


if __name__ == '__main__':
    main()
