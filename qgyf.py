# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGYF
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
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QApplication, QFileDialog, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer
from qgis.gui import QgsFileWidget
from .resources import *

from .ui.qgyf_dockwidget import QGYFDockWidget
from .ui.welcome import WelcomeDialog
from .ui.settings import SettingsDialog
from .ui.layer_selector import LayerSelectorDialog
from .ui.export import ExportDialog
from .lib.db import Db
from .lib.quality_table import QualityTable
from .lib.db_view import DbView
from .lib.file_loader import FileLoader
from .lib.styles import Style
from .lib.gyf_calculator import GyfCalculator
from .lib.gyf_diagram import Diagram
from .lib.map_export import ExportCreator
#from .lib.canvasClickedEvent import CanvasClick

import os.path
import numpy as np
import inspect
from shutil import copyfile

class QGYF:

	def __init__(self, iface):
		self.iface = iface
		self.plugin_dir = os.path.dirname(__file__)

		locale = QSettings().value('locale/userLocale')[0:2]
		locale_path = os.path.join(
			self.plugin_dir,
			'i18n',
			'QGYF_{}.qm'.format(locale))

		if os.path.exists(locale_path):
			self.translator = QTranslator()
			self.translator.load(locale_path)
			if qVersion() > '4.3.3':
				QCoreApplication.installTranslator(self.translator)

		if not QSettings().value('dataPath'):
			QSettings().setValue('dataPath', os.getenv('APPDATA') + '\QGYF')
			if not os.path.exists(QSettings().value('dataPath')):
				os.makedirs(QSettings().value('dataPath'))

		if not QSettings().value('activeDataBase'):
			QSettings().setValue('activeDataBase', 'qgyf.sqlite')

		self.actions = []
		self.menu = self.translate(u'&QGYF')
		self.toolbar = self.iface.addToolBar(u'QGYF')
		self.toolbar.setObjectName(u'QGYF')
		self.pluginIsActive = False
		self.dockwidget = None
		self.area_id = None

		self.initDatabase(QSettings().value('dataPath'))
		self.layerSelectorDialog = LayerSelectorDialog()
		self.fileLoader = FileLoader(self.iface.mainWindow(), self.layerSelectorDialog, QSettings().value('dataPath'))
		self.calculator = GyfCalculator(QSettings().value('dataPath'))
		self.layerSelectorDialog.loadClassifications(QSettings().value('dataPath'))
		self.showWelcome()

	def initGui(self):
		"""Create the menu entries and toolbar icons inside the QGIS GUI."""

		icon_path = ':/plugins/qgyf/assets/load_db.png'
		self.addAction(
			icon_path,
			text=self.translate(u'Ladda databas'),
			callback=self.load,
			parent=self.iface.mainWindow())

		icon_path = ':/plugins/qgyf/assets/folder.png'
		self.addAction(
			icon_path,
			text=self.translate(u'Ladda lager'),
			callback=self.loadFile,
			parent=self.iface.mainWindow())

		icon_path = ':/plugins/qgyf/assets/tree.png'
		self.addAction(
			icon_path,
			text=self.translate(u'Beräkna grönytefaktor'),
			callback=self.openCalculationDialog,
			parent=self.iface.mainWindow())

		icon_path = ':/plugins/qgyf/assets/save.png'
		self.addAction(
			icon_path,
			text=self.translate(u'Spara databas'),
			callback=self.save,
			parent=self.iface.mainWindow())

		icon_path = ':/plugins/qgyf/assets/settings.png'
		self.addAction(
			icon_path,
			text=self.translate(u'Inställningar'),
			callback=self.openSettingsDialog,
			parent=self.iface.mainWindow())

		# icon_path = ':/plugins/qgyf/assets/edit_point.png'
		# self.addAction(
		# 	icon_path,
		# 	text=self.translate(u'Editera punktobjekt'),
		# 	callback=self.info,
		# 	parent=self.iface.mainWindow())

		# icon_path = ':/plugins/qgyf/assets/edit_polyline.png'
		# self.addAction(
		# 	icon_path,
		# 	text=self.translate(u'Editera linjeobjekt'),
		# 	callback=self.info,
		# 	parent=self.iface.mainWindow())

		# icon_path = ':/plugins/qgyf/assets/edit_polygon.png'
		# self.addAction(
		# 	icon_path,
		# 	text=self.translate(u'Editera ytobjekt'),
		# 	callback=self.info,
		# 	parent=self.iface.mainWindow())

		icon_path = ':/plugins/qgyf/assets/info.png'
		self.addAction(
			icon_path,
			text=self.translate(u'Vissa upp informationsfönstret'),
			callback=self.info,
			parent=self.iface.mainWindow())

	def load(self):
		self.addLayers(QSettings().value('dataPath'), [
			"research_area",
			"point_object",
			"line_object",
			"polygon_object",
		])

	def translate(self, message):
		"""Get the translation for a string using Qt translation API.

		We implement this ourselves since we do not inherit QObject.

		:param message: String for translation.
		:type message: str, QString

		:returns: Translated version of message.
		:rtype: QString
		"""
		# noinspection PyTypeChecker,PyArgumentList,PyCallByClass
		return QCoreApplication.translate('QGYF', message)

	def addAction(
		self,
		icon_path,
		text,
		callback,
		enabled_flag=True,
		add_to_menu=True,
		add_to_toolbar=True,
		status_tip=None,
		whats_this=None,
		parent=None):

		icon = QIcon(icon_path)
		action = QAction(icon, text, parent)
		action.triggered.connect(callback)
		action.setEnabled(enabled_flag)

		if status_tip is not None:
			action.setStatusTip(status_tip)

		if whats_this is not None:
			action.setWhatsThis(whats_this)

		if add_to_toolbar:
			self.toolbar.addAction(action)

		if add_to_menu:
			self.iface.addPluginToMenu(
				self.menu,
				action)

		self.actions.append(action)

		return action

	def saveCheckBoxStatus(self):
		QSettings().setValue('checkBoxStatus', not self.welcome.checkBox.isChecked())
		QSettings().sync()

	def showWelcome(self):
		"""Show welcome message."""
		check_state = QSettings().value('checkBoxStatus', True, type=bool)
		if check_state is True:
			self.welcome = WelcomeDialog()
			self.welcome.show()
			self.welcome.okButton.clicked.connect(self.welcome.close)
			self.welcome.checkBox.clicked.connect(self.saveCheckBoxStatus)

	def loadFile(self):
		self.fileLoader.loadFile()
		root = QgsProject.instance().layerTreeRoot()
		content = [l.name() for l in root.children()]
		if 'Kvaliteter' in content:
			if self.dockwidget:
				self.dockwidget.disableGroup(QSettings().value('dataPath'))

	def info(self):
		self.welcome = WelcomeDialog()
		self.welcome.show()
		self.welcome.okButton.clicked.connect(self.welcome.close)

	def addLayers(self, path, layers):
		self.style = Style()
		root = QgsProject.instance().layerTreeRoot()
		classificationGroup = root.findGroup('Klassificering')

		root.clear()

		# for layer in root.findLayers():
		# 	if layer.name() == "Beräkningsområde":
		# 		root.removeChildNode(layer)
		# if classificationGroup:
		# 	root.removeChildNode(classificationGroup)

		classificationGroup = root.insertGroup(0, 'Klassificering')
		layerNames =	{
		  "point_object": "Punktobjekt",
		  "line_object": "Linjeobjekt",
		  "polygon_object": "Ytobjekt",
		  "research_area": "Beräkningsområde"
		}

		for layer in layers:
			pathLayer = '{}\{}|layername={}'.format(path, QSettings().value('activeDataBase'), layer)
			vlayer = QgsVectorLayer(pathLayer, layerNames[layer], "ogr")
			if layer == 'research_area':
				self.style.styleResearchArea(vlayer)
				QgsProject.instance().addMapLayer(vlayer)
			else:
				self.style.iniStyle(vlayer)
				QgsProject.instance().addMapLayer(vlayer, False)
				classificationGroup.addLayer(vlayer)

	def initDatabase(self, path):
		self.db = Db()
		self.db.create(path)
		self.quality = QualityTable()
		self.quality.init(path)

	def onClosePlugin(self):
		self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
		# Remove this statement if dockwidget is to remain
		# for reuse if plugin is reopened
		self.pluginIsActive = False

	def unload(self):
		for action in self.actions:
			self.iface.removePluginMenu(
				self.translate(u'&QGYF'),
				action)
			self.iface.removeToolBarIcon(action)
		del self.toolbar

	def createDataView(self):
		if self.dockwidget.tabWidget.currentIndex() == 1:
			self.dbView = DbView()
			self.dbView.init(QSettings().value('dataPath'))

	def calculate(self):

		gyf, factor_areas, groups, feature_ids, area_id = self.calculator.calculate()
		self.dockwidget.gyfValue.setText("{0:.2f}".format(gyf))
		total = 0

		if factor_areas.size != 0:
			# Plot
			self.diagram = Diagram()
			self.dockwidget.plot.canvas.ax.cla()
			self.dockwidget.plot.canvas.ax.set_title('Fördelning av kvalitetspoäng')
			sizes, legend, colors, outline, total = self.diagram.init(factor_areas, groups)
			patches, text = self.dockwidget.plot.canvas.ax.pie(sizes, colors=colors, startangle=90, wedgeprops=outline)
			#self.dockwidget.plot.canvas.fig.tight_layout()
			# Legend
			patches, legend, dummy =  zip(*sorted(zip(patches, legend, sizes), key=lambda x: x[2], reverse=True))
			self.dockwidget.plot.canvas.ax2.legend(patches, legend, loc = 'center', shadow = None, frameon = False)
			self.dockwidget.plot.canvas.draw()

		self.area_id = area_id
		self.groups = groups
		self.feature_ids = feature_ids
		self.total = total

	def showExportDialog(self):
		if self.area_id == None:
			QMessageBox.warning(ExportDialog(), 'Ingen GYF', 'Beräkna GYF först för att exportera resultat!')
		else:
			self.exportDialog = ExportDialog()
			self.exportDialog.show()
			self.exportDialog.okButton.clicked.connect(self.export)
			self.exportDialog.okButton.clicked.connect(self.exportDialog.close)

	def export(self):
		chart_path = QSettings().value('dataPath') + '\PieChart.png'
		self.dockwidget.plot.canvas.fig.savefig(chart_path)
		gyf = self.dockwidget.gyfValue.text()
		groups = []
		checkboxnames = ['checkBio', 'checkBuller', 'checkVatten', 'checkKlimat', 'checkPoll', 'checkHalsa']
		checkbox_list = [getattr(self.dockwidget, n) for n in checkboxnames]
		for checkbox in checkbox_list:
			if checkbox.isEnabled() and checkbox.isChecked():
				groups.append(checkbox.text())
		groups = [g for g in groups if g in self.groups]
		self.pdfCreator = ExportCreator()
		self.pdfCreator.exportPDF(chart_path, gyf, self.exportDialog, self.area_id, groups, self.feature_ids, self.total)

	def openCalculationDialog(self):
		"""Run method that loads and starts the plugin"""
		if not self.pluginIsActive:
			self.pluginIsActive = True

		# dockwidget may not exist if:
		#    first run of plugin
		#    removed on close (see self.onClosePlugin method)
		if self.dockwidget == None:

			# Create the dockwidget (after translation) and keep reference
			self.dockwidget = QGYFDockWidget()
			self.iface.removeDockWidget(self.dockwidget)
			self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)

			# connect to provide cleanup on closing of dockwidget
			self.dockwidget.closingPlugin.connect(self.onClosePlugin)

		self.dockwidget.show()

		# Classification
		showClass = lambda : self.dockwidget.showClass(QSettings().value('dataPath'))
		showClass()
		self.dockwidget.switchLayerGroups()

		# Highlight rows in classification table
		self.iface.mapCanvas().selectionChanged.connect(self.dockwidget.highlightRows)

		# Qualities
		self.dockwidget.selectQGroup.clear()
		self.dockwidget.chooseQ(QSettings().value('dataPath'))
		getQ = lambda : self.dockwidget.getQ(QSettings().value('dataPath'))
		self.dockwidget.selectQGroup.currentIndexChanged.connect(getQ)
		getF = lambda : self.dockwidget.getF(QSettings().value('dataPath'))
		self.dockwidget.selectQ.currentIndexChanged.connect(getF)
		setQ = lambda : self.dockwidget.setQ(QSettings().value('dataPath'))
		self.dockwidget.approveButton.clicked.connect(setQ)
		self.dockwidget.approveButton.clicked.connect(showClass)
		removeQ = lambda : self.dockwidget.removeQ(QSettings().value('dataPath'))
		self.dockwidget.removeButton.clicked.connect(removeQ)
		self.dockwidget.classtable.itemSelectionChanged.connect(self.dockwidget.highlightFeatures)

		# Objects
		self.dockwidget.setLayers()
		self.dockwidget.selectLayer.currentIndexChanged.connect(self.dockwidget.selectStart)

		# Visualisation
		self.dockwidget.tabWidget.currentChanged.connect(self.createDataView)
		disableGroup = lambda : self.dockwidget.disableGroup(QSettings().value('dataPath'))
		self.dockwidget.tabWidget.currentChanged.connect(disableGroup)
		self.dockwidget.tabWidget.currentChanged.connect(self.dockwidget.switchLayerGroups)
		self.dockwidget.groupList()

		# Estimation of GYF
		# Research area
		self.dockwidget.calculate.setStyleSheet("color: #006600")
		self.dockwidget.selectRA.clicked.connect(self.dockwidget.selectArea)
		createArea = lambda : self.dockwidget.createArea(QSettings().value('dataPath'))
		self.dockwidget.createRA.clicked.connect(createArea)
		# GYF
		self.dockwidget.calculate.clicked.connect(self.calculate)

		# Export
		self.dockwidget.report.clicked.connect(self.showExportDialog)

	def openSettingsDialog(self):
		self.settings = SettingsDialog()
		self.settings.show()
		self.settings.okButton.clicked.connect(self.settings.close)

	def save(self):
		path = QFileDialog.getSaveFileName(self.iface.mainWindow(), 'Spara som', '', '.sqlite')
		new_path = "{0}{1}".format(path[0], path[1])
		database = QSettings().value('activeDataBase')
		path = "{}/{}".format(QSettings().value('dataPath'), database)
		if path and new_path:
			copyfile(path, new_path)

