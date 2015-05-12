# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CrossedSelection
                                 A QGIS plugin
 This plugin helps to select features in a layer according to values from a field of another layer
                              -------------------
        begin                : 2014-09-26
        git sha              : $Format:%H$
        copyright            : (C) 2014 by Harrissou SANT-ANNA
        email                : delazj@gmail.com
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon, QListWidgetItem, QMenu, QCursor, QMessageBox
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from crossed_selection_dialog import CrossedSelectionDialog
import os.path
from qgis.core import *
from qgis.gui import QgsMessageBar


class CrossedSelection:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CrossedSelection_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = CrossedSelectionDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Crossed Selection')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'CrossedSelection')
        self.toolbar.setObjectName(u'CrossedSelection')
        
        global myLayers

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CrossedSelection', message)


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
        """Add a toolbar icon to the InaSAFE toolbar.

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

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/CrossedSelection/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Select features with crossing values'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.dlg.valuesList.customContextMenuRequested.connect(self.context_menu)
        # fill comboboxes
        self.listLayers(self.dlg.srcLayer)
        self.listLayers(self.dlg.tgtLayer)
        self.updateFieldsBox(self.dlg.tgtLayer, self.dlg.tgtField)
        self.updateFieldsBox(self.dlg.srcLayer, self.dlg.srcField)
        self.updateFieldsBox(self.dlg.srcLayer, self.dlg.fltField)
        self.showAttributes()

        # connect the signal to list the fields 
        self.dlg.srcLayer.currentIndexChanged.connect(self.updatesrcField)
        self.dlg.srcLayer.currentIndexChanged.connect(self.updatefltField)
        self.dlg.tgtLayer.currentIndexChanged.connect(self.updatetgtField)
        # self.dlg.srcLayer.currentIndexChanged.connect(self.updateFieldsBox(self.dlg.srcLayer, self.dlg.fltField))
        
         # connect the signal to show the attribute values        
        self.dlg.fltField.currentIndexChanged.connect(self.showAttributes)
        
        # Connect to the OK button to do the real work
        self.dlg.button_box.accepted.connect(self.proceedSelection)
        

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Crossed Selection'),
                action)
            self.iface.removeToolBarIcon(action)

    def context_menu(self):
        """ Add context menu functions """
        menu = QMenu(self.dlg.valuesList)
        menu.addAction(self.tr(u"Check..."), self.actionCheckValues)
        menu.addAction(self.tr(u"Uncheck..."), self.actionUncheckValues)
        menu.exec_(QCursor.pos()) 

    def actionCheckValues(self):
        for item in self.dlg.valuesList.selectedItems():
            item.setCheckState(Qt.Checked)

    def actionUncheckValues(self):
        for item in self.dlg.valuesList.selectedItems():
            item.setCheckState(Qt.Unchecked)
    
    def listLayers(self, cBox):
        """identify and list all the available layers in the project"""
        cBox.clear()
        global myLayers
        myLayers = []
        myLayers = [lyr for lyr in self.iface.legendInterface().layers() if lyr.type() == QgsMapLayer.VectorLayer]
        # myLayers.sort()
        # return myLayers
        # myLayers[0:0]=[""]
        # for idx, nom in enumerate(vecteurs):
        
        
        # cBox.insertItem(0,"")
        for elt in myLayers:
            cBox.addItem(elt.name())
        """# if srcCombobox.currentText() is not None:
            # layername = srcCombobox.currentText()
        for name, selectlayer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
                if selectlayer.name() == layername:
                    # fields = layer.pendingFields()
                    # for field in fields:
                    for field in selectlayer.dataProvider().fields():
                        tgtCombobox.addItem(field.name())
        # self.blockSignals(False)
        """
    
            
    def listFields(self, layer):
        """ Retrieve all the fields in a layer """
        field_names = []
        # layer = QgsVectorLayer()
        field_names = [field.name() for field in layer.pendingFields() ]
        return field_names
    
    def updateFieldsBox(self, layerBox, fieldBox) :
        """ A generic function to retrieve fields list according to selected layer """
        # global myLayers
        fieldBox.clear()
        layerIdx = layerBox.currentIndex()
        # for lyr in myLayers:
            # if lyr.name() == layerBox.currentText() :
                # fieldBox.addItems(self.listFields(lyr))
        
        if myLayers == []:
            fieldBox.addItems(self.listFields(myLayers[layerIdx]))
        else :
            fieldBox.addItems(self.listFields(myLayers[layerIdx]))
        
    def updatetgtField(self):
        """ list all the fields according to the target layer selected """
        self.dlg.tgtField.clear()
        layerIdx = self.dlg.tgtLayer.currentIndex()
        self.dlg.tgtField.addItems(self.listFields(myLayers[layerIdx]))

    def updatesrcField(self):
        """ list all the fields according to the source layer selected """
        self.dlg.srcField.clear()
        layerIdx = self.dlg.srcLayer.currentIndex()
        self.dlg.srcField.addItems(self.listFields(myLayers[layerIdx]))
        
    def updatefltField(self):
        """ list all the fields according to the source layer selected"""
        self.dlg.fltField.clear()
        layerIdx = self.dlg.srcLayer.currentIndex()
        self.dlg.fltField.addItems(self.listFields(myLayers[layerIdx]))

    def showAttributes(self):
        """ List unique values of the selected field from source layer and show them in widget"""
        listAttr = []
        self.dlg.valuesList.clear()
        lyr = myLayers[self.dlg.srcLayer.currentIndex()]
        
        for feature in lyr.getFeatures():
            # attrs = feature.attributes()
            attr = feature.attributes()[self.dlg.fltField.currentIndex()]
            if attr not in listAttr:
                listAttr.append(attr)
        listAttr.sort()

        for value in listAttr:
            value = str(value)
            item = QListWidgetItem()
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setText(value)
            self.dlg.valuesList.addItem(item)
        
    def listCheckedAttributes(self): 
        """ Retrieve all the attribute values checked in the filtered field """
        global rowsChecked
        rowsChecked = []
        rowsChecked = [self.dlg.valuesList.item(rowList).text() for rowList in range(0, self.dlg.valuesList.count()) \
            if self.dlg.valuesList.item(rowList).checkState() == Qt.Checked
            ]
        return rowsChecked
                    
    def where(layer, exp):
        """ from qgis doc """
        exp = QgsExpression(exp)
        if exp.hasParserError():
            raise Expection(exp.parserErrorString())
        exp.prepare(layer.pendingFields())
        for feature in layer.getFeatures():
            value = exp.evaluate(feature)
            if exp.hasEvalError():
              raise ValueError(exp.evalErrorString())
            if bool(value):
              yield feature

    def proceedSelection(self):
        """ Function that do the selection of features according to values set"""
        srcLyr = myLayers[self.dlg.srcLayer.currentIndex()]
        tgtLyr = myLayers[self.dlg.tgtLayer.currentIndex()]
        source_attributes = [feat.attributes()[self.dlg.srcField.currentIndex()] \
            for feat in srcLyr.getFeatures() ]
        rowsChecked = [self.dlg.valuesList.item(rowList).text() for rowList in range(0, self.dlg.valuesList.count()) \
            if self.dlg.valuesList.item(rowList).checkState() == Qt.Checked ]
                    
        if self.dlg.advancedBox.isChecked() and rowsChecked:
            source_attributes = [feat.attributes()[self.dlg.srcField.currentIndex()] \
                for feat in srcLyr.getFeatures() if feat.attributes()[self.dlg.fltField.currentIndex()] in rowsChecked ]
            
        for feature in tgtLyr.getFeatures():
            if feature.attributes()[self.dlg.tgtField.currentIndex()] in source_attributes :
                tgtLyr.select(feature.id())
                    
            
    def checkvector(self):
        """ Check if there is a "no raster layer" in the project"""
        nb = 0
        for layer in self.iface.legendInterface().layers():
        # for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
            if not layer.type() == QgsMapLayer.RasterLayer :
                nb += 1
        return nb
    
    def run(self):
        """ Run method that performs all the real work"""
        # check if there is valid layer to show the dialog
        if self.checkvector()== 0 :
            self.iface.messageBar().pushMessage(self.tr(u'Crossed Selection : '),
                self.tr(u'There is no usable layer in the project. Please add at least one before running this plugin.'), level = QgsMessageBar.CRITICAL, duration = 5)
            return
        # else :
        # show the dialog
        self.dlg.show()
        # populate the layers combobox
        # self.listLayers(self.dlg.srcLayer)
        # self.listLayers(self.dlg.tgtLayer)
        

