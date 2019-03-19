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
from PyQt5.QtWidgets import QAction
from qgis.core import QgsProject, QgsVectorLayer
from .resources import *
from .qgyf_dockwidget import QGYFDockWidget
from .ui.welcome import WelcomeDialog
from .lib.db import Db
from .lib.qualityTable import QualityTab
import os.path

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

		self.actions = []
		self.menu = self.translate(u'&QGYF')
		self.toolbar = self.iface.addToolBar(u'QGYF')
		self.toolbar.setObjectName(u'QGYF')
		self.pluginIsActive = False
		self.dockwidget = None

		self.path = os.path.expanduser('~') + r'\Documents\QGYF'
		self.initDatabase(self.path)

		self.showWelcome()

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

	def add_action(
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
		"""Add a toolbar icon to the toolbar.

		:param icon_path: Path to the icon for this action. Can be a resource
			path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
		:type icon_path: str

		:param text: Text that should be shown in menu items for this action.
		:type text: str

		:param callback: Function to be called when the action is triggered.
		:type callback: function

		:param enabled_flag: A flag indicating if the action should be enabled
			by default. Defaults to True.
		:type enabled_flag: bool

		:param add_to_menu: Flag indicating whether the action should also
			be added to the menu. Defaults to True.
		:type add_to_menu: bool

		:param add_to_toolbar: Flag indicating whether the action should also
			be added to the toolbar. Defaults to True.
		:type add_to_toolbar: bool

		:param status_tip: Optional text to show in a popup when mouse pointer
			hovers over the action.
		:type status_tip: str

		:param parent: Parent widget for the new action. Defaults None.
		:type parent: QWidget

		:param whats_this: Optional text to show in the status bar when the
			mouse pointer hovers over the action.

		:returns: The action that was created. Note that the action is also
			added to self.actions list.
		:rtype: QAction
		"""

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
		print(QSettings().value('checkBoxStatus', type=bool))

	def showWelcome(self):
		"""Show welcome message."""
		check_state = QSettings().value('checkBoxStatus', True, type=bool)
		print(check_state)
		if check_state is True:
			self.welcome = WelcomeDialog()
			self.welcome.show()
			self.welcome.okButton.clicked.connect(self.welcome.close)
			self.welcome.checkBox.clicked.connect(self.saveCheckBoxStatus)
			

	def load(self):
		self.addLayers(self.path, [
			"point_object",
			"line_object",
			"polygon_object",
			"research_area"
		])

	def info(self):
		self.welcome = WelcomeDialog()
		self.welcome.show()
		self.welcome.okButton.clicked.connect(self.welcome.close)

	def initGui(self):
		"""Create the menu entries and toolbar icons inside the QGIS GUI."""

		icon_path = ':/plugins/qgyf/assets/folder.png'
		self.add_action(
			icon_path,
			text=self.translate(u'Ladda lager'),
			callback=self.load,
			parent=self.iface.mainWindow())

		icon_path = ':/plugins/qgyf/assets/tree.png'
		self.add_action(
			icon_path,
			text=self.translate(u'Beräkna grönytefaktor'),
			callback=self.run,
			parent=self.iface.mainWindow())

		icon_path = ':/plugins/qgyf/assets/edit_point.png'
		self.add_action(
			icon_path,
			text=self.translate(u'Editera punktobjekt'),
			callback=self.info,
			parent=self.iface.mainWindow())
		
		icon_path = ':/plugins/qgyf/assets/edit_polyline.png'
		self.add_action(
			icon_path,
			text=self.translate(u'Editera linjeobjekt'),
			callback=self.info,
			parent=self.iface.mainWindow())

		icon_path = ':/plugins/qgyf/assets/edit_polygon.png'
		self.add_action(
			icon_path,
			text=self.translate(u'Editera ytobjekt'),
			callback=self.info,
			parent=self.iface.mainWindow())

		icon_path = ':/plugins/qgyf/assets/info.png'
		self.add_action(
			icon_path,
			text=self.translate(u'Vissa upp informationsfönstret'),
			callback=self.info,
			parent=self.iface.mainWindow())

	def addLayers(self, path, layers):
		for layer in layers:
			pathLayer = path + r"\qgyf.sqlite|layername=" + layer
			vlayer = QgsVectorLayer(pathLayer, layer, "ogr")
			QgsProject.instance().addMapLayer(vlayer)

	def initDatabase(self, path):
		self.db = Db()
		self.db.create(path)
		self.quality = QualityTab()
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

	def run(self):
		"""Run method that loads and starts the plugin"""
		if not self.pluginIsActive:
			self.pluginIsActive = True

			# dockwidget may not exist if:
			#    first run of plugin
			#    removed on close (see self.onClosePlugin method)
			if self.dockwidget == None:

				# Create the dockwidget (after translation) and keep reference
				self.dockwidget = QGYFDockWidget()

				# connect to provide cleanup on closing of dockwidget
				self.dockwidget.closingPlugin.connect(self.onClosePlugin)

				# show the dockwidget
				self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
				self.dockwidget.show()
