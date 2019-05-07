'''
---------------------------------------------------------------------------
settings.py
Created on: 2019-04-09 12:04:28
QGYF settings dialog
---------------------------------------------------------------------------
'''
import os, fnmatch
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from qgis.utils import iface
from ..lib.db import Db
from qgis.gui import QgsProjectionSelectionDialog
from qgis.core import QgsCoordinateReferenceSystem

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'settings.ui'))

class SettingsDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, dockwidget, parent=None, parentWidget=None):
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)
        self.populate()
        self.dataPath.setText(QSettings().value('dataPath'))
        crs = QgsCoordinateReferenceSystem(QSettings().value('CRS'))
        self.crs.setText(crs.description())
        self.selectPathButton.clicked.connect(self.openFileDialog)
        clearDataBase = lambda : self.clearDataBase(dockwidget)
        self.clearDatabaseButton.clicked.connect(clearDataBase)
        self.activeDatabase.currentIndexChanged.connect(self.setDatabase)
        self.parent = parentWidget
        self.selectCRSButton.clicked.connect(self.setCRS)

    def clearDataBase(self, dockwidget):
        db = Db()
        db.clear("{}\{}".format(QSettings().value('dataPath'), QSettings().value('activeDataBase')))
        self.msg = QMessageBox()
        self.msg.setIcon(QMessageBox.Information)
        self.msg.setWindowTitle("Information")
        self.msg.setText("Databasen rensades")
        self.msg.show()
        dockwidget.showClass()
        iface.mapCanvas().refreshAllLayers()

    def openFileDialog(self):
        path = QFileDialog.getExistingDirectory(self, 'Öppna fil', '', QFileDialog.ShowDirsOnly)
        if path:
            QSettings().setValue('dataPath', path)
            self.dataPath.setText(QSettings().value('dataPath'))
            self.activeDatabase.clear()
            self.populate()

    def setDatabase(self, index):
        self.activeDatabase.setCurrentIndex(index)
        if self.activeDatabase.currentText():
            QSettings().setValue('activeDataBase', self.activeDatabase.currentText())
        else:
            QSettings().setValue('activeDataBase', 'qgyf.sqlite')

    def populate(self):
        if not os.path.exists(QSettings().value('dataPath')):
            QSettings().setValue('dataPath', os.getenv('APPDATA') + '\QGYF')
        listOfFiles = os.listdir(QSettings().value('dataPath'))
        pattern = "*.sqlite"
        self.activeDatabase.clear()
        activeIndex = 0
        index = 0
        for entry in listOfFiles:
            if fnmatch.fnmatch(entry, pattern):
                self.activeDatabase.addItem(entry)
                if entry == QSettings().value('activeDataBase'):
                    activeIndex = index
                index += 1

        self.setDatabase(activeIndex)

    def setCRS(self):
        projSelector = QgsProjectionSelectionDialog()
        projSelector.exec()
        crs_id = projSelector.crs().authid()
        if crs_id:
             QSettings().setValue('CRS', crs_id)
        self.crs.setText(projSelector.crs().description())
