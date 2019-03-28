"""
---------------------------------------------------------------------------
styles.py
Created on: 2019-03-27 16:20:53
---------------------------------------------------------------------------
"""
import os
import sys
from qgis.core import QgsProject, QgsVectorLayer, QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer
from qgis.utils import spatialite_connect, iface

class Style:
    
    def init(self, path):
        con = spatialite_connect(path + r'\qgyf.sqlite')
        cur = con.cursor()
        cur.execute('''SELECT grupp FROM gyf_qgroup''')
        items = [i[0] for i in cur.fetchall()][:6]
        cur.close()
        con.close()
        print(items)

        colors = [
            ['76,153,0,50', '0,102,0,50'], # green
            ['255,128,0,50', '204,102,0,50'], # orange
            ['51,153,255,50', '0,102,204,50'], # blue
            ['255,255,51,50', '204,204,0,50'], # yellow
            ['178,102,255,50', '76,0,153,50'], # violet
            ['255,0,127,50', '153,0,76,50'], # rose
        ]

        symbology = dict(zip(items, colors))
        categories1 = []
        categories2 = []
        categories3 = []
        for groups, (c1, c2) in symbology.items():
            symbol_point = QgsMarkerSymbol.createSimple({
                'color':c1,
                'color_border':c2,
                'width_border':'0.5'})
            symbol_line = QgsLineSymbol.createSimple({
                'color':c1,
                'width':'1.5'})
            symbol_poly = QgsFillSymbol.createSimple({
                'color':c1,
                'color_border':c2,
                'width_border':'0.5'})
            category1 = QgsRendererCategory(groups, symbol_point, groups)
            category2 = QgsRendererCategory(groups, symbol_line, groups)
            category3 = QgsRendererCategory(groups, symbol_poly, groups)
            categories1.append(category1)
            categories2.append(category2)
            categories3.append(category3)
        
        #def setCategories(symbology):
        #    for groups, (c1, c2) in symbology.items():

        views = ['point_class', 'line_class', 'polygon_class']
        symbols = dict(zip(views, [categories1, categories2, categories3]))
        print(symbols)
        for v, c in symbols.items():
            l = QgsProject.instance().mapLayersByName(v) #'polygon_class'
            if l:
                l = l[0]
                renderer = QgsCategorizedSymbolRenderer('grupp', c)
                l.setRenderer(renderer)
                l.triggerRepaint()
        
        # One color solution 
        ''' if l:
            l = l[0]
            r = l.renderer()
            bio_symbol = QgsFillSymbol.createSimple({
                'color':'255,0,0,50',
                'color_border':'#289e26',
                'width_border':'0.5'})
            r.setSymbol(bio_symbol)
            l.triggerRepaint()'''