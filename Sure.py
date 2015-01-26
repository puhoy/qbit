__author__ = 'meatpuppet'

from PyQt4 import QtGui, QtCore


class SureDialog(QtGui.QDialog):
    def __init__(self, parent = None):
        super(SureDialog, self).__init__(parent)

        self.layout = QtGui.QVBoxLayout(self)

        # OK and Cancel buttons
        self.buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        self.layout.addWidget(self.buttons)

    @staticmethod
    def getOk(parent = None):
        dialog = SureDialog(parent)
        result = dialog.exec_()
        return result