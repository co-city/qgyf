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
import threading
import uuid
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import QSettings, pyqtSignal, Qt
from qgis.core import QgsProject, QgsVectorLayer, QgsFeatureRequest, QgsWkbTypes, NULL
from qgis.utils import iface, spatialite_connect
from .saveResearchArea import saveRA
from ..lib.styles import Style
from .mplwidget import MplWidget

from functools import wraps

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qgyf_dockwidget_base.ui'))

def delay(delay=0.):
    """
    Decorator delaying the execution of a function for a while.
    """
    def wrap(f):
        @wraps(f)
        def delayed(*args, **kwargs):
            timer = threading.Timer(delay, f, args=args, kwargs=kwargs)
            timer.start()
        return delayed
    return wrap

class Timer():

    toClearTimer = False

    def setTimeout(self, fn, time):
        isInvokationCancelled = False
        @delay(time)
        def some_fn():
            if (self.toClearTimer is False):
                fn()
            else:
                print('Invokation is cleared!')
        some_fn()
        return isInvokationCancelled

    def setClearTimer(self):
        self.toClearTimer = True

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
        self.feature_selection_lock = False
        self.row_selection_lock = False

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
        quality = [''] + quality
        self.selectQ.addItems(quality)

        cur.close()
        con.close()

    def getF(self, path):

        if self.selectQGroup.currentIndex() == 0:
            return None

        self.textQ.clear()
        con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
        cur = con.cursor()

        if self.selectQ.count() > 0:
            if self.selectQ.currentText() != '':
                q = self.selectQ.currentText()
                q = q.split(' ')[0]
                cur.execute('SELECT faktor,namn,beskrivning FROM gyf_quality WHERE kvalitet = ?', [q])
                text = cur.fetchone()
                t = '<h4 style="color:#238973">' + text[1] + '</h4>'+ text[2] +'<p style="color:#238973">faktor = ' + str(text[0]) + '</p>'
                self.textQ.append(t)
            else:
                if self.selectQGroup.currentText():
                    i = [self.selectQGroup.currentIndex()]
                    cur.execute('SELECT faktor FROM gyf_qgroup WHERE id = ?', i)
                    text = '<p style="color:#cc0000">OBS! Ungerfärligt beräkningsläge för GYF:en.<br>Välj kvalitet för att få en noggrannt definierad faktor.</p><h4 style="color:#238973">' + \
                        self.selectQGroup.currentText() + '</h4>grov faktor = ' + str(cur.fetchone()[0])
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
            return {
                'punkt': 'Punktobjekt',
                'linje': 'Linjeobjekt'
            }.get(x, 'Ytobjekt')

        l = QgsProject.instance().mapLayersByName(lyr(self.selectLayer.currentText()))
        if l:
            iface.setActiveLayer(l[0])

    def checkGID(self, layer):
        path = QSettings().value('dataPath')
        con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
        cur = con.cursor()
        features = layer.getFeatures()
        for f in features:
            if f['gid'] == NULL:
                if layer.wkbType() == QgsWkbTypes.Point:
                    cur.execute("UPDATE point_object SET gid = (?) WHERE id = (?)", [str(uuid.uuid4()), f['id']])
                elif layer.wkbType() == QgsWkbTypes.LineString:
                    cur.execute("UPDATE line_object SET gid = (?) WHERE id = (?)", [str(uuid.uuid4()), f['id']])
                else:
                    cur.execute("UPDATE polygon_object SET gid = (?) WHERE id = (?)", [str(uuid.uuid4()), f['id']])
        cur.close()
        con.commit()
        con.close()


    def setQ(self):

        path = QSettings().value('dataPath')
        layer = iface.activeLayer()
        #self.checkGID(layer)

        selected = layer.selectedFeatures()
        if self.selectQGroup.currentIndex() == 0:
            return None

        attributes = []
        g = self.selectQGroup.currentText()

        if selected:
            for f in selected:
                attributes.append(f.attributes())
 
        def set_geom(x):
            return {QgsWkbTypes.Point: 'punkt',
                    QgsWkbTypes.LineString: 'linje'}.get(x, 'yta')
        geom = set_geom(layer.wkbType())

        con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
        cur = con.cursor()

        if self.selectQ.currentText() != '':
            q = self.selectQ.currentText()
            q = q.split(' ')[0]
            cur.execute('SELECT faktor FROM gyf_quality WHERE kvalitet = ?', [q])
        else:
            q = ''
            i = [self.selectQGroup.currentIndex()]
            cur.execute('SELECT faktor FROM gyf_qgroup WHERE id = ?', i)
        f = cur.fetchone()[0]

        data = []
        for obj in attributes:
            if obj[2] == NULL:
                obj[2] = ''
            if type(obj[-1]) is str:
                 obj[-1] = float(obj[-1])
            data.append([obj[1], geom, obj[2], g, q, f, round(obj[-1], 1), round(obj[-1]*f, 1)])

        cur.executemany('INSERT INTO classification VALUES (?,?,?,?,?,?,?,?)', data)
        # gid, geometri_typ, filnamn, grupp, kvalitet, faktor, yta, poäng
        cur.close()
        con.commit()
        con.close()

        self.showClass()

    def updateClassArea(self, path, gid, yta):
        con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
        cur = con.cursor()
        cur.execute('SELECT kvalitet, faktor FROM classification WHERE gid = (?);', [gid])
        factor = [[j[0], j[1]] for j in cur.fetchall()]
        for f in factor:
            poang = f[1]*yta
            cur.execute('UPDATE classification SET yta = (?), poang = (?) WHERE kvalitet = (?) AND gid = (?);', [yta, poang, f[0], gid])

        cur.close()
        con.commit()
        con.close()

    def removeQ(self, path):
        items = self.classtable.selectedItems()
        if items:
            selected_rows = list(set([i.row() for i in items]))
            ids = [[self.classtable.item(i,3).text(), self.classtable.item(i,7).text()] for i in selected_rows]

            con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
            cur = con.cursor()

            for i in ids:
                cur.execute('DELETE FROM classification WHERE kvalitet = (?) AND gid = (?);', i)

            cur.close()
            con.commit()
            con.close()
            self.showClass()

    def showClass(self):
        path = QSettings().value('dataPath')
        self.classtable.clear()
        root = QgsProject.instance().layerTreeRoot()
        content = [l.name() for l in root.children()]
        if 'Klassificering' in content:
            con = spatialite_connect("{}\{}".format(path, QSettings().value('activeDataBase')))
            cur = con.cursor()

            cur.execute('SELECT * FROM classification')
            data = cur.fetchall()
            data = [list(d[1:-2]) + [int(d[-2]), int(d[-1]), d[0]] for d in data]

            self.classtable.setSortingEnabled(True)
            self.classtable.setColumnCount(8)
            self.classtable.setHorizontalHeaderLabels(["geom", "filnamn", 'Grupp', 'K', 'F', 'Yta', 'Poäng', 'gid'])

            if data:
                self.classtable.setRowCount(len(data))
                for i, item in enumerate(data):
                    for j, field in enumerate(item):
                        self.classtable.setItem(i, j, QtWidgets.QTableWidgetItem(str(field)))
                        self.classtable.horizontalHeader().setSectionResizeMode(j, QtWidgets.QHeaderView.ResizeToContents)
            else:
                self.classtable.setRowCount(0)

            self.classtable.setColumnHidden(7, True)

            cur.close()
            con.close()

    def chunks(self, l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def lookupFeatures(self, gids, layer, geometry_type):
        features = list(layer.getFeatures())
        matches = []

        for gid in gids:
            for feature in features:
                if gid[0] == geometry_type and feature['gid'] == gid[1]:
                    matches.append(feature)

        return matches

    def resetFeatureSelectionLock(self):
        self.feature_selection_lock = False

    def resetRowSelectionLock(self):
        self.row_selection_lock = False

    def highlightFeatures(self):

        if self.row_selection_lock is False:
            selected_items = self.classtable.selectedItems()

            point_layer = QgsProject.instance().mapLayersByName('Punktobjekt')
            line_layer = QgsProject.instance().mapLayersByName('Linjeobjekt')
            polygon_layer = QgsProject.instance().mapLayersByName('Ytobjekt')
            layers = point_layer + line_layer + polygon_layer

            if layers:

                self.feature_selection_lock = True
                timer = Timer()
                timer.setTimeout(self.resetFeatureSelectionLock, 0.1)

                if selected_items:
                    selected_rows = list(set([i.row() for i in selected_items]))
                    gids = [[self.classtable.item(i, 0).text(), self.classtable.item(i, 7).text()] for i in selected_rows]
                    if point_layer:
                        selected_points = self.lookupFeatures(gids, point_layer[0], 'punkt')
                        point_layer[0].selectByIds([point.id() for point in selected_points])
                    if line_layer:
                        selected_lines = self.lookupFeatures(gids, line_layer[0], 'linje')
                        line_layer[0].selectByIds([line.id() for line in selected_lines])
                    if polygon_layer:
                        selected_polygons = self.lookupFeatures(gids, polygon_layer[0], 'yta')
                        polygon_layer[0].selectByIds([polygon.id() for polygon in selected_polygons])
                else:
                    if point_layer:
                        point_layer[0].removeSelection()
                    if line_layer:
                        line_layer[0].removeSelection()
                    if polygon_layer:
                        polygon_layer[0].removeSelection()

    def selectRowByFeatures(self, features, geom_type):

        for feature in features:
            feature_id = feature["gid"]
            if feature_id != NULL:
                items = self.classtable.findItems(feature_id, Qt.MatchExactly)
                rows = [item.row() for item in items]

                for row in rows:
                    geom_name = self.classtable.item(row, 0).text()
                    table_gid = self.classtable.item(row, 7).text()
                    if geom_type == geom_name and table_gid == feature_id:
                        self.classtable.selectRow(row)

    def highlightRows(self):

        point_layer = QgsProject.instance().mapLayersByName('Punktobjekt')
        line_layer = QgsProject.instance().mapLayersByName('Linjeobjekt')
        polygon_layer = QgsProject.instance().mapLayersByName('Ytobjekt')
        layers = point_layer + line_layer + polygon_layer

        if layers:
            selected_points = []
            selected_lines = []
            selected_polygons = []

            if point_layer:
                selected_points = point_layer[0].getSelectedFeatures()
            if line_layer:
                selected_lines = line_layer[0].getSelectedFeatures()
            if polygon_layer:
                selected_polygons = polygon_layer[0].getSelectedFeatures()

            self.row_selection_lock = True
            timer = Timer()
            timer.setTimeout(self.resetRowSelectionLock, 0.2)

            if self.feature_selection_lock is False and self.tabWidget.currentIndex() == 0:
                self.classtable.clearSelection()
                self.classtable.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
                self.selectRowByFeatures(selected_points, "punkt")
                self.selectRowByFeatures(selected_lines, "linje")
                self.selectRowByFeatures(selected_polygons, "yta")

            self.classtable.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def switchLayerGroups(self):
        self.style = Style()
        if self.tabWidget.currentIndex() == 0:
            self.style.visibility('Kvaliteter', False)
            self.style.visibility('Klassificering', True)
        else:
            self.style.visibility('Kvaliteter', True)
            self.style.visibility('Klassificering', False)


    #RESEARCH_AREA
    def okClicked(self, l):
        l.commitChanges()
        iface.vectorLayerTools().stopEditing(l)
        self.window.close()

    def cancelClicked(self, fid, l):
        l.deleteFeature(fid)
        l.commitChanges()
        iface.vectorLayerTools().stopEditing(l)
        l.triggerRepaint()
        self.window.close()

    def showSaveDialog(self, fid, l):
        self.window = saveRA()
        self.window.show()
        ok = lambda : self.okClicked(l)
        cancel = lambda : self.cancelClicked(fid, l)
        self.window.okButton.clicked.connect(ok)
        self.window.cancelButton.clicked.connect(cancel)

    def createArea(self, path):
        l = QgsProject.instance().mapLayersByName('Beräkningsområde')
        if l:
            l = l[0]
            iface.setActiveLayer(l)
            iface.actionToggleEditing().trigger()
            iface.actionAddFeature().trigger()
            l.featureAdded.connect(lambda fid: self.areaAdded(fid, l))
            l.featureAdded.connect(lambda fid: self.showSaveDialog(fid, l))

    def areaAdded(self, fid, layer):
        feature = layer.getFeature(fid)
        feature["yta"] = feature.geometry().area()
        layer.updateFeature(feature)

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
        view_names =	{
		  'point_class': 'Punktkvalitet',
		  'line_class': 'Linjekvalitet',
		  'polygon_class': 'Ytkvalitet'
		}
        for v in views:
            view = QgsProject.instance().mapLayersByName(view_names[v])
            if view:
                view = view[0]
                unchecked_list = [c.text() for c in checkbox_list if not c.isChecked()]
                unchecked = "', '".join(c for c in unchecked_list)
                query = "SELECT * FROM " + v + " WHERE grupp not in ('" + unchecked + "')"
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

    def disableGroup(self, path):
        if self.tabWidget.currentIndex() == 1:
            pathLayer = '{}\{}|layername={}'.format(path, QSettings().value('activeDataBase'), 'classification')
            table = QgsVectorLayer(pathLayer, 'classification', "ogr")
            features = table.getFeatures()
            current_groups = []
            for feature in features:
                index = feature.fields().indexFromName("grupp")
                group = feature.attributes()[index]
                try:
                  group = group.encode("windows-1252").decode("utf-8")
                except:
                  group = group
                current_groups.append(group)
            current_groups = list(set(current_groups))
            checkboxnames = ['checkBio', 'checkBuller', 'checkVatten', 'checkKlimat', 'checkPoll', 'checkHalsa']
            checkbox_list = [getattr(self, n) for n in checkboxnames]
            for checkbox in checkbox_list:
                if checkbox.text() in current_groups:
                    checkbox.setEnabled(True)
                else:
                    checkbox.setEnabled(False)
                    checkbox.setChecked(False)

