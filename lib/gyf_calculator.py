from qgis.core import QgsProject, QgsVectorLayer, QgsApplication, QgsWkbTypes
from qgis.utils import iface
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QSettings
from ..ui.welcome import WelcomeDialog
import numpy as np

class GyfCalculator:
  def __init__(self, path):
    self.path = path

  def getFeatures(self):
    """
    Get features from given layers.
    @return {list} features
    """
    polygon_layer = QgsProject.instance().mapLayersByName("Ytkvalitet")[0]
    line_layer = QgsProject.instance().mapLayersByName("Linjekvalitet")[0]
    point_layer = QgsProject.instance().mapLayersByName("Punktkvalitet")[0]
    # Clear visualisation filters if they were set
    polygon_layer.setSubsetString('')
    line_layer.setSubsetString('')
    point_layer.setSubsetString('')

    return [
      *list(polygon_layer.getFeatures()),
      *list(line_layer.getFeatures()),
      *list(point_layer.getFeatures())
    ]

  def calculateIntersectionArea(self, feature, intersector):
    """
    Calculate the instersection of two features, and optionally scale with given factor.
    @param {QgsFeature} feature
    @param {QgsFeature} intersector
    @param {bool} with_factor
    @return {list} features
    """
    geometry_type = QgsWkbTypes.geometryDisplayString(feature.geometry().type())
    new_geom = None
    if geometry_type == "Point":
        new_geom = feature.geometry().buffer(3, 20)
    if geometry_type == "Line":
        new_geom = feature.geometry().buffer(0.5, 20)

    if new_geom:
      intersection = new_geom.intersection(intersector.geometry())
    else:
      intersection = feature.geometry().intersection(intersector.geometry())

    factor = feature["faktor"]
    group = feature["grupp"]
    feature_id = feature["gid"]

    return intersection.area() * factor, group, feature_id

  def calculateGroundAreaIntersection(self, intersector):
    "Calculate the intersection of ground areas and the research area"
    ground_layer = QgsProject.instance().mapLayersByName("Grundytor")
    if ground_layer:
      ground_layer = ground_layer[0]
    else:
      pathLayer = '{}\{}|layername={}'.format(QSettings().value("dataPath"), QSettings().value("activeDataBase"), 'ground_areas')
      ground_layer = QgsVectorLayer(pathLayer, 'Grundytor', "ogr")
    area = list(ground_layer.getFeatures())[0]
    intersection = area.geometry().intersection(intersector.geometry())
    return intersection.area()

  def calculate(self):
    """
    Calculate gyf factor.
    @return {number} gyf
    """
    research_area_layer = QgsProject.instance().mapLayersByName("Beräkningsområde")
    gyf = 0
    factor_areas = []
    groups = []
    feature_ids = []
    eco_area = 0
    selected_feature = None
    if research_area_layer:
      research_area_layer = research_area_layer[0]
      if research_area_layer.isEditable():
        iface.vectorLayerTools().stopEditing(research_area_layer)
      selected_features = list(research_area_layer.selectedFeatures())

      if list(selected_features):
        selected_feature = selected_features[0]
        features = self.getFeatures()

        calculation_area = selected_feature.geometry().area()
        feature_area_sum = 0
        feature_area_factor_sum = 0

        intersecting_features = []
        for feature in features:
          geom = feature.geometry()
          selected_geometry = selected_feature.geometry()
          # TODO: find a comparer to test intersection,
          # the intersection calculation is not necsessary if the feature is completely outside the calculation area.
          # if geom.overlaps(selected_geometry):
          intersecting_features.append(feature)

        for feature in intersecting_features:
          factor_area, group, feature_id = self.calculateIntersectionArea(feature, selected_feature)
          feature_area_factor_sum += factor_area
          factor_areas.append(factor_area)
          groups.append(group)
          feature_ids.append(feature_id)

        feature_area_sum = self.calculateGroundAreaIntersection(selected_feature)

        # Get rid of features which don't actually intersect the currently selected feature
        factor_areas = np.asarray(factor_areas)
        groups = np.asarray(groups)
        feature_ids = np.asarray(feature_ids)
        nonzero_indexes = np.where(factor_areas != 0.0)
        factor_areas = factor_areas[nonzero_indexes]
        groups = groups[nonzero_indexes]
        feature_ids = feature_ids[nonzero_indexes]

        eco_area = feature_area_sum + feature_area_factor_sum
        gyf = eco_area / calculation_area
      else:
        QMessageBox.warning(WelcomeDialog(), 'Inget beräkningsområde', 'Välj beräkningsområde för att beräkna GYF!')

    else:
      QMessageBox.warning(WelcomeDialog(), 'Inget beräkningsområde', 'Lägg till lager med beräkningsområde för att beräkna GYF!')

    if type(factor_areas) == list:
      factor_areas = np.array([])

    return gyf, factor_areas, groups, feature_ids, selected_feature, eco_area

