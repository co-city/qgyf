# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGYFDockWidget
                                 A QGIS plugin
 Green Space Factor
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-03-01
        git sha              : $Format:%H$
        copyright            : (C) 2019 by C/O City
        email                : info@cocity.se
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import QSettings, pyqtSignal, Qt
from qgis.core import QgsProject, QgsVectorLayer, QgsFeatureRequest
from qgis.utils import iface, spatialite_connect
from .saveResearchArea import saveRA
from ..lib.styles import Style

from .mplwidget import MplWidget

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qgyf_dockwidget_base.ui'))


class QGYFDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(QGYFDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

        """ Functions to classify input data"""

    # CLASSIFICATION
    def chooseQ(self, path):
        self.selectQGroup.clear()
        con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
        cur = con.cursor()

        self.textQ.clear()
        self.selectQ.clear()
        cur.execute('''SELECT grupp FROM gyf_qgroup''')
        items = [''] + [i[0] for i in cur.fetchall()]
        self.selectQGroup.addItems(items)

        cur.close()
        con.close()

    def getQ(self, path):
        self.selectQ.clear()
        self.textQ.clear()
        con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
        cur = con.cursor()

        i = str(self.selectQGroup.currentIndex())
        cur.execute('SELECT kvalitet, kort_namn FROM gyf_quality WHERE grupp_id = ' + i)
        quality = [j[0] + ' - ' + j[1] for j in cur.fetchall()]
        quality = quality + ['Vet inte']
        self.selectQ.addItems(quality)

        cur.close()
        con.close()

    def getF(self, path):
        self.textQ.clear()
        con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
        cur = con.cursor()

        if self.selectQ.count() > 0:
            if self.selectQ.currentText() != 'Vet inte':
                q = self.selectQ.currentText()
                q = q.split(' ')[0]
                cur.execute('SELECT faktor,namn FROM gyf_quality WHERE kvalitet = ?', [q])
                text = cur.fetchone()
                t = text[1] + ', faktor = ' + str(text[0])
                self.textQ.append(t)
            else:
                i = [self.selectQGroup.currentIndex()]
                cur.execute('SELECT faktor FROM gyf_qgroup WHERE id = ?', i)
                text = '<b>Ungerfärligt beräkningsläge för GYF:en!</b><br>' + \
                    self.selectQGroup.currentText() + ', grov faktor = ' + str(cur.fetchone()[0])
                self.textQ.append(text)

        cur.close()
        con.close()

    def setLayers(self):
        self.selectLayer.clear()
        items = ['', 'punkt', 'linje', 'yta']
        self.selectLayer.addItems(items)

    def selectStart(self):
        # Start object selection for QGYF
        for a in iface.attributesToolBar().actions():
            if a.objectName() == 'mActionDeselectAll':
                a.trigger()
                break

        iface.actionSelect().trigger()

        def lyr(x):
            return {'punkt': 'Punktobjekt',
                    'linje': 'Linjeobjekt'}.get(x, 'Ytobjekt')

        l = QgsProject.instance().mapLayersByName(lyr(self.selectLayer.currentText()))[0]
        iface.setActiveLayer(l)

    def setQ(self, path):
        con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
        cur = con.cursor()

        layer = iface.activeLayer()
        selected = layer.selectedFeatures()
        attributes = []
        if selected:
            for f in selected:
                attributes.append(f.attributes())

        g = self.selectQGroup.currentText()
        geom = self.selectLayer.currentText()

        if self.selectQ.currentText() != 'Vet inte':
            q = self.selectQ.currentText()
            q = q.split(' ')[0]
            cur.execute('SELECT faktor FROM gyf_quality WHERE kvalitet = ?', [q])
        else:
            q = ''
            i = [self.selectQGroup.currentIndex()]
            cur.execute('SELECT faktor FROM gyf_qgroup WHERE id = ?', i)
        f = cur.fetchone()[0]

        data = []
        for i,obj in enumerate(attributes):
            data.append([None, geom, obj[1], obj[0], g, q, f])

        cur.executemany('INSERT INTO classification VALUES (?,?,?,?,?,?,?)', data)
        cur.close()
        con.commit()
        con.close()

    def showClass(self, path):
        self.classtable.clear()
        con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
        cur = con.cursor()

        cur.execute('SELECT * FROM classification')
        data = cur.fetchall()
        data = [list(d[1:])+[d[0]] for d in data]

        if data:
            self.classtable.setSortingEnabled(True)
            self.classtable.setRowCount(len(data))
            self.classtable.setColumnCount(len(data[0]))
            self.classtable.setHorizontalHeaderLabels(["geom", "fil namn", 'id', 'Grupp', 'K', 'F', 'uid'])
            for i, item in enumerate(data):
                for j, field in enumerate(item):
                    self.classtable.setItem(i, j, QtWidgets.QTableWidgetItem(str(field)))
                    self.classtable.horizontalHeader().setSectionResizeMode(j, QtWidgets.QHeaderView.ResizeToContents)

        cur.close()
        con.close()

    def removeQ(self, path):

        ids = self.classtable.selectedItems()
        ids = [i.text() for i in ids] #i.row()
        if len(ids) == 7:
            ids = [ids[-1]]
        else:
            ids = [ids[7*n-1] for n in range(1, int(len(ids)/7 + 1))]
        ids = [int(i) for i in ids]

        con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
        cur = con.cursor()

        for i in ids:
            cur.execute('DELETE FROM classification WHERE id = (?);', [i])

        cur.close()
        con.commit()
        con.close()
        self.showClass(path)

    def highlightFeatures(self):
        items = self.classtable.selectedItems()
        items = [i.text() for i in items]

        if items[0] == 'yta':
            lyr = QgsProject.instance().mapLayersByName('Punktobjekt')
        elif items[0] == 'linje':
            lyr = QgsProject.instance().mapLayersByName('Linjeobjekt')
        else:
            lyr = QgsProject.instance().mapLayersByName('Ytobjekt')

        if lyr:
            lyr = lyr[0]
            query = '"id" = ' + items[2]
            selection = lyr.getFeatures(QgsFeatureRequest().setFilterExpression(query))
            lyr.selectByIds([k.id() for k in selection])

    def highlightRows(self):
        #iface.mapCanvas().setSelectionColor(QtGui.QColor(0, 0, 255, 127))
        lyr = iface.activeLayer()
        self.classtable.clearSelection()
        self.classtable.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        if self.tabWidget.currentIndex() == 0:
            if lyr:
                selected = list(lyr.selectedFeatures())
                selected = [f.attribute('id') for f in selected]
                rows = []
                for i in selected:
                    items = self.classtable.findItems(str(i), Qt.MatchExactly)
                    row = [item.row() for item in items]
                    for r in row:
                        self.classtable.selectRow(r)
                        rows.append(r)
        self.classtable.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)



    def switchLayerGroups(self):
        self.style = Style()
        if self.tabWidget.currentIndex() == 0:
            self.style.visibility('Visualisering', False)
            self.style.visibility('Klassificering', True)
        else:
            self.style.visibility('Visualisering', True)
            self.style.visibility('Klassificering', False)


    #RESEARCH_AREA
    def okClicked(self, l, path):
        f = [f for f in l.getFeatures()][0]
        f['yta'] = f.geometry().area()
        print (f.geometry().area())
        l.updateFeature(f)
        l.commitChanges()
        iface.vectorLayerTools().stopEditing(l)
        con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
        con.commit()
        con.close()
        self.window.close()

    def cancelClicked(self, l):
        f = [f for f in l.getFeatures()][0]
        l.deleteFeature(f.id())
        l.triggerRepaint()
        iface.vectorLayerTools().stopEditing(l)
        self.window.close()

    def showSaveDialog(self, l, path):
        self.window = saveRA()
        self.window.show()
        ok = lambda : self.okClicked(l, path)
        cancel = lambda : self.cancelClicked(l)
        self.window.okButton.clicked.connect(ok)
        self.window.cancelButton.clicked.connect(cancel)

    def createArea(self, path):
        l = QgsProject.instance().mapLayersByName('Beräkningsområde')
        if l:
            l = l[0]
            iface.setActiveLayer(l)
            iface.actionToggleEditing().trigger()
            iface.actionAddFeature().trigger()
            showSave = lambda : self.showSaveDialog(l, path)
            l.featureAdded.connect(showSave)

    def selectArea(self):
        for a in iface.attributesToolBar().actions():
            if a.objectName() == 'mActionDeselectAll':
                a.trigger()
                break

        l = QgsProject.instance().mapLayersByName('Beräkningsområde')
        if l:
            l = l[0]
            iface.setActiveLayer(l)
            iface.actionSelect().trigger()


    # Visualization
    def checkGroup(self, checkbox_list):
        views = ['polygon_class', 'line_class', 'point_class']
        for v in views:
            view = QgsProject.instance().mapLayersByName(v)
            if view:
                view = view[0]
                unchecked_list = [c.text() for c in checkbox_list if not c.isChecked()]
                unchecked = "', '".join(c for c in unchecked_list)
                query = "SELECT * FROM " + view.name() + " WHERE grupp not in ('" + unchecked + "')"
                view.setSubsetString(query)


    def groupList(self):
        checkboxnames = ['checkBio', 'checkBuller', 'checkVatten', 'checkKlimat', 'checkPoll', 'checkHalsa']
        checkbox_list = [getattr(self, n) for n in checkboxnames]
        for checkbox in checkbox_list:
            checkbox.setChecked(True)

        checkGroup = lambda : self.checkGroup(checkbox_list)
        self.checkBio.stateChanged.connect(checkGroup)
        self.checkBuller.stateChanged.connect(checkGroup)
        self.checkVatten.stateChanged.connect(checkGroup)
        self.checkKlimat.stateChanged.connect(checkGroup)
        self.checkPoll.stateChanged.connect(checkGroup)
        self.checkHalsa.stateChanged.connect(checkGroup)

