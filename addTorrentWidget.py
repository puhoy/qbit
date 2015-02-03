__author__ = 'meatpuppet'
from PyQt4 import QtGui, uic, QtCore
from gui import addmagnetlink

#addmagnetlink_window = uic.loadUiType("addmagnetlink.ui")[0]

class AddTorrentWidget(QtGui.QDialog, addmagnetlink.Ui_Dialog_add_torrent):
    mlink = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(AddTorrentWidget, self).__init__(parent)
        self.setupUi(self)

        self.btn_cancel.clicked.connect(self.btn_cancel_clicked)
        self.btn_add.clicked.connect(self.btn_add_clicked)

    def btn_cancel_clicked(self):
        self.close()

    @QtCore.pyqtSlot()
    def btn_add_clicked(self):
        if (self.lnEdt_mlink.text() is ""):
            text="magnet:?xt=urn:btih:febd9a2cb755ec82e6e7a015a8dc497fde9dd507&dn=Ubuntu+Ultimate+Edition+1.4+DVD&xl=2083522692&dl=2083522692"
        else:
            text=self.lnEdt_mlink.text()
        self.mlink.emit(text)
        self.close()
        pass