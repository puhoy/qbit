__author__ = 'meatpuppet'
import sys
from PyQt4 import QtGui, uic, QtCore, Qt
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
        path = QtGui.QFileDialog.getOpenFileName(self.parent(), "choose torrent file", "",)
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
        storepath = self.askForPathToStore()
        if storepath:
            self.kju.put({'addmagnet': mlink,
                          'storepath': storepath})

    def addByTorrentFile(self, fpath):
        storepath = self.askForPathToStore()
        if storepath:
            self.kju.put({'addtorrent': fpath,
                          'storepath': storepath})

    def askForPathToStore(self):
        path = QtGui.QFileDialog.getExistingDirectory(self.parent(), "Pick folder to Store", "", QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontResolveSymlinks)
        return path

    @QtCore.pyqtSlot()
    def pauseTorrent(self, handle):

        self.kju.put({'pauseTorrent': handle})

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

        item.setSizeHint(0, QtCore.QSize(400, 30))
        item.setSizeHint(1, QtCore.QSize(80, 30))



        self.treeWidget_downloading.resizeColumnToContents(0)
        bar = QtGui.QProgressBar()
        bar.setVisible(True)
        bar.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        info = QtGui.QAction('detailed info', self)
        #info.triggered.connect(functools.partial(self.deleteTorrent, handle))
        pause = QtGui.QAction('(un)pause', self)
        pause.triggered.connect(functools.partial(self.pauseTorrent, handle))
        delete = QtGui.QAction('delete', self)
        delete.triggered.connect(functools.partial(self.deleteTorrent, handle))

        bar.addAction(info)
        bar.addAction(pause)
        bar.addAction(delete)

        self.treeWidget_downloading.addTopLevelItem(item)
        self.treeWidget_downloading.setItemWidget(item, 0, bar)
        self.items[handle] = {'item': item,
                              'bar': bar,
                              'files': {}}



    @QtCore.pyqtSlot(object, object)
    def updateitem(self, handle, status):
        stat = status
        state_str = self.state_str[stat.state]
        if status.paused:
            state_str = state_str + ' (paused)'
        try:
            values =  "%s - " \
            "Progress: %.2f \n-- %s -- " \
            "total upload: %.2fMb " \
            "Peers: %s, U:%.2f D:%.2f_|" % \
            (handle.name(),
             stat.progress * 100, state_str,
             stat.total_upload/1024/1024,
             stat.num_peers, stat.upload_rate/1024, stat.download_rate/1024)
            self.items.get(handle).get('bar').setValue(stat.progress * 100)
            self.items.get(handle).get('bar').setFormat(values)
        except:
            pass
        if handle.get_torrent_info() and not self.items[handle].get('files'):
            self.set_filelist(handle)

    def set_filelist(self, handle):
        filestore = handle.get_torrent_info().files()
        fileitems = []
        files = {}
        index = 0
        prios = handle.file_priorities()
        for file in filestore:
            fitem = QtGui.QTreeWidgetItem(["%s" % file.path])
            fitem.setText(1, "%.2fMb" % (file.size/1024/1024))
            if prios[index] == 1:
                fitem.setCheckState(0, QtCore.Qt.Checked)  # setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            else:
                fitem.setCheckState(0, QtCore.Qt.Unchecked)
            fileitems.append(fitem)
            files[index] = {'widget': fitem}

            index += 1
        item = self.items.get(handle).get('item')
        item.setText(1, "%.2fMb" % (handle.get_torrent_info().total_size()/1024/1024))
        item.addChildren(fileitems)
        self.treeWidget_downloading.itemChanged.connect(self.handleItemChanged)
        self.items[handle]['files'] = files

    def handleItemChanged(self, item, column):
        parent = item.parent()
        for k, vdict in self.items.items():
            if vdict['item'] is parent:
                handle = k
                index = parent.indexOfChild(item)
                if item.flags() & QtCore.Qt.ItemIsUserCheckable:
                    if item.checkState(0) == QtCore.Qt.Checked:
                        print('%s: Checked' % parent.indexOfChild(item))
                        self.set_prio(handle, index, 1)
                    else:
                        print('%s: UnChecked' % parent.indexOfChild(item))
                        self.set_prio(handle, index, 0)

    def set_prio(self, handle, fileindex, prio=0):  # see http://www.rasterbar.com/products/libtorrent/manual.html#torrent-handle -> piece prio
        # handle:
        # void file_priority (int index, int priority) const;
        #handle.file_priority(fileindex, prio)
        logging.info('setting prio')
        self.kju.put({'setprio': {'index': fileindex,
                                  'prio': prio,
                                  'handle': handle}})
        pass

    @QtCore.pyqtSlot(object)
    def deleteitem(self, handle):
        print('deleting item for')
        print(handle)
        item = self.items[handle].get('item')
        bar = self.items[handle].get('bar')
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
