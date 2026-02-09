# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GMWColourLayersDialog
"""

from qgis.PyQt import QtCore, QtGui
from qgis.gui import QgsLayerTreeView
from qgis.core import QgsLayerTreeModel, QgsProject, QgsLayerTreeLayer, QgsPalettedRasterRenderer
import qgis.utils

from PyQt5.QtWidgets import QAbstractItemView
from PyQt5 import QtWidgets as QW
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

import json


def hex_to_rgb(hex_str: str) -> (int, int, int):
    """
    A function which converts an hexadecimal colour representation to RGB values
    between 0 and 255.

    For example: #b432be is equal to: 180, 50, 190

    :param hex_str: Input hex string which can be either 7 or 6 characters long.
                    If 7 characters then the first character will be a #.
    :return: R, G, B tuple

    .. code:: python

        import rsgislib.tools.utils
        r, g, b = rsgislib.tools.utils.hex_to_rgb("#b432be")

    """
    if hex_str[0] == "#":
        hex_str = hex_str[1:]
    if len(hex_str) != 6:
        raise rsgislib.RSGISPyException(
            "String must be of length 6 or 7 if starting with #"
        )

    r_hex = hex_str[0:2]
    g_hex = hex_str[2:4]
    b_hex = hex_str[4:6]
    return int(r_hex, 16), int(g_hex, 16), int(b_hex, 16)

class GMWColourLayersDialog(QW.QDialog):
    
    def __init__(self, parent=None):
        """Constructor."""
        QW.QWidget.__init__(self, parent)
        # Set window size. 
        self.resize(320, 240)

        # Set window title  
        self.setWindowTitle("Colour Layers") 
        
        # Create mainLayout
        self.mainLayout = QW.QVBoxLayout()
        
        self.guiLabelStep1 = QW.QLabel()
        self.guiLabelStep1.setText("1. Select a Vector Layers:")
        self.mainLayout.addWidget(self.guiLabelStep1)
        
        # Initialize the view
        self.layer_tree_view = QgsLayerTreeView(self)
        
        # Get the root of the actual QGIS layer tree
        self.root = QgsProject.instance().layerTreeRoot()
        
        # Create the model based on the root
        self.model = QgsLayerTreeModel(self.root)
        
        # Set the model to the view
        self.layer_tree_view.setModel(self.model)
        
        # Enable multi-selection
        self.layer_tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        self.mainLayout.addWidget(self.layer_tree_view)
        
        self.guiLabelStep2 = QW.QLabel()
        self.guiLabelStep2.setText("2. Select Colours Template File:")
        self.mainLayout.addWidget(self.guiLabelStep2)
        
        self.file_path_edit = QW.QLineEdit()
        self.file_path_edit.setPlaceholderText("No file selected...")
        self.browse_button = QW.QPushButton("Browse...")
        
        # 2. Create a horizontal layout for the input row
        # This keeps the text box and button side-by-side
        file_row_layout = QW.QHBoxLayout()
        file_row_layout.addWidget(self.file_path_edit)
        file_row_layout.addWidget(self.browse_button)
        
        # 3. Add them to your existing QVBoxLayout (self.mainLayout)
        self.mainLayout.addLayout(file_row_layout)
        
        # 4. Connect the button to the logic
        self.browse_button.clicked.connect(self.select_clrs_lut_file)
        
        
        self.guiLabelStep3 = QW.QLabel()
        self.guiLabelStep3.setText("3. Update Layer Colours:")
        self.mainLayout.addWidget(self.guiLabelStep3)
        
        
        self.run_button = QW.QPushButton("Run")
        self.close_button = QW.QPushButton("Close")
        button_layout = QW.QHBoxLayout()
        spacer = QW.QSpacerItem(40, 20, QW.QSizePolicy.Expanding, QW.QSizePolicy.Minimum)
        button_layout.addItem(spacer)
        
        button_layout.addWidget(self.close_button)
        button_layout.addWidget(self.run_button)
        
        self.mainLayout.addLayout(button_layout)
        self.run_button.clicked.connect(self.handle_run)
        self.close_button.clicked.connect(self.handle_close)
        
        # Make the Run button respond to the 'Enter' key
        self.run_button.setDefault(True)
        
        self.setLayout(self.mainLayout)
        
    
    def get_selected_layers(self):
        # Get all selected nodes (could be layers or groups)
        selected_nodes = self.layer_tree_view.selectedNodes()
        
        layers = []
        for node in selected_nodes:
            # Check if the node is a layer (not a group)
            if isinstance(node, QgsLayerTreeLayer):
                layers.append(node.layer())
                
        return layers
        
    def select_clrs_lut_file(self):
        # Open the file dialog
        # Parameters: parent, title, directory, filter
        filename, _ = QW.QFileDialog.getOpenFileName(
            None, 
            "Select Colours LUT File", 
            "", 
            "JSON (*.json)"
        )
        
        # If the user didn't click cancel, update the text box
        if filename:
            self.file_path_edit.setText(filename)
    
    def handle_run(self):
        # Access the layers and file path:
        layers = self.layer_tree_view.selectedLayers()
        clr_lut_path = self.file_path_edit.text()
        
        # Open the colours LUT file.
        with open(clr_lut_path) as f:
            clrs_lut = json.load(f)
            
            # Iterate the colours
            for clr_ref in clrs_lut:
                # Create the colour
                clr_r, clr_g, clr_b = hex_to_rgb(clrs_lut[clr_ref])
                clr_obj = QColor(clr_r, clr_g, clr_b)
                # Iterate the layers and find the any which have the clr_ref.
                for lyr in layers:
                    lyr_name = lyr.id()
                    if clr_ref in lyr_name:
                        if lyr.type() == lyr.VectorLayer:
                            lyr_renderer = lyr.renderer()
                            lyr_symbol = lyr_renderer.symbol()
                            
                            # Apply the colour to the symbol
                            if lyr_symbol:
                                lyr_symbol.setColor(clr_obj)
                                for i in range(lyr_symbol.symbolLayerCount()):
                                    lyr_symbol_layer = lyr_symbol.symbolLayer(i)
                                    # Set the stroke style to NoPen (Removes the line)
                                    lyr_symbol_layer.setStrokeStyle(Qt.NoPen)
                                
                        elif lyr.type() == lyr.RasterLayer:
                            lyr_provider = lyr.dataProvider()
                            band = 1
                            lyr_classes = [QgsPalettedRasterRenderer.Class(1, clr_obj, clr_ref)]
                            lyr_renderer = QgsPalettedRasterRenderer(provider, band, classes)
                            lyr.setRenderer(lyr_renderer)
                                
                        # Notify the layer and the canvas of the change
                        lyr.triggerRepaint()
            
                        # Refresh the legend/TOC to show the updated colour box
                        self.layer_tree_view.refreshLayerSymbology(lyr_name)
                        # Tell everything that the style has changed.
                        lyr.emitStyleChanged()
        
        
    
    def handle_close(self):
        # If this is a QDialog, you can simply call reject()
        self.close()