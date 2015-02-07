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

import functools

#main_window = uic.loadUiType("qbit_main.ui")[0]                 # Load the UI

class Qbit_main(QtGui.QMainWindow, qbit_main.Ui_MainWindow):
    deletetorrent = QtCore.pyqtSignal(object)
    def __init__(self, parent=None):
        super(Qbit_main, self).__init__(parent)
        #QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.items = {}

        self.mapper = QtCore.QSignalMapper(self)

        self.kju = Queue()

        addMenu = QtGui.QMenu()
        addFile = QtGui.QAction('Torrentfile', self)
        addFile.triggered.connect(self.btn_addTorrentFile_clicked)
        addMenu.addAction(addFile)
        addLink = QtGui.QAction('Magnetlink', self)
        addLink.triggered.connect(self.btn_addMagnetLink_clicked)
        addMenu.addAction(addLink)

        self.actionAdd.setMenu(addMenu)

        self.actionPause.triggered.connect(self.pauseSession)


        self.ts = TorrentSession(self.kju)

        self.state_str = self.ts.state_str

        self.ts.statusbar.connect(self.statusBar.showMessage)
        self.ts.torrent_updated.connect(self.updateitem)
        self.ts.torrent_deleted.connect(self.deleteitem)
        self.ts.torrent_added.connect(self.makeitem)

        self.ts.start()

    def handleContext(self, pos):
        item = self.treeWidget_downloading.itemAt(pos)
        if item is not None:
            menu = QtGui.QMenu("Context Menu", self)
            menu.addAction("FOO")
            ret = menu.exec_(self.treeWidget_downloading.mapToGlobal(pos))


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

    @QtCore.pyqtSlot()
    def pauseSession(self):
        self.kju.put({'pause': True})

    @QtCore.pyqtSlot(object)
    def deleteTorrent(self, handle):
        print(handle)
        reply = QtGui.QMessageBox.question(self, 'Message',
                                       "really delete?",
                                       QtGui.QMessageBox.Yes,
                                       QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.kju.put({'deletetorrent': handle})


    @QtCore.pyqtSlot(object)
    def makeitem(self, handle):
        print('making item!')
        item = QtGui.QTreeWidgetItem()

        item.setSizeHint(0, QtCore.QSize(0, 30))

        bar = QtGui.QProgressBar()
        bar.setVisible(True)
        bar.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        info = QtGui.QAction('detailed info', self)
        info.triggered.connect(functools.partial(self.deleteTorrent, handle))
        delete = QtGui.QAction('delete', self)
        delete.triggered.connect(functools.partial(self.deleteTorrent, handle))

        bar.addAction(info)
        bar.addAction(delete)

        self.treeWidget_downloading.addTopLevelItem(item)
        filestore = handle.get_torrent_info().files()
        fileitems = []
        for file in filestore:
            print(file.path)
            fileitems.append(QtGui.QTreeWidgetItem([file.path]))
        item.addChildren(fileitems)

        self.treeWidget_downloading.setItemWidget(item, 0, bar)
        self.items[handle] = (item, bar)

    @QtCore.pyqtSlot(object, object)
    def updateitem(self, handle, status):
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
        print('deleting item for')
        print(handle)
        (item, bar) = self.items[handle]
        self.treeWidget_downloading.removeItemWidget(item, 0)

        self.treeWidget_downloading.takeTopLevelItem(self.treeWidget_downloading.indexOfTopLevelItem(item))

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
