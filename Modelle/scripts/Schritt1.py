"""
Model exported as python.
Name : Schritt 1: Kacheln erzeugen_Gruenflaechen extrahieren
Group : Wohnlage
With QGIS : 32002
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterExtent
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression
import processing


class Schritt1KachelnErzeugen_gruenflaechenExtrahieren(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterExtent('Ausdehnung', 'Ausdehnung', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('Breite', 'Kachelbreite', type=QgsProcessingParameterNumber.Double, minValue=-1.79769e+308, maxValue=1.79769e+308, defaultValue=200))
        self.addParameter(QgsProcessingParameterNumber('Hhe', 'Kachelhoehe', type=QgsProcessingParameterNumber.Double, minValue=-1.79769e+308, maxValue=1.79769e+308, defaultValue=200))
        self.addParameter(QgsProcessingParameterVectorLayer('OSMGebudelayer', 'OSM-Gebaeude (gis_osm_buildings_a_free_1)', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('OSMLanduse', 'OSM-Landnutzung (gis_osm_landuse_a_free_1)', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Kachelnuntersuchungsgebiet', 'KachelnUntersuchungsgebiet', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Gruenflaechen', 'Gruenflaechen', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(5, model_feedback)
        results = {}
        outputs = {}

        # Kacheln erzeugen
        alg_params = {
            'CRS': 'ProjectCrs',
            'EXTENT': parameters['Ausdehnung'],
            'HOVERLAY': 0,
            'HSPACING': parameters['Breite'],
            'TYPE': 2,  # Rechteck (Polygon)
            'VOVERLAY': 0,
            'VSPACING': parameters['Hhe'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['KachelnErzeugen'] = processing.run('native:creategrid', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Kacheln mit Gebaeuden extrahieren
        alg_params = {
            'INPUT': outputs['KachelnErzeugen']['OUTPUT'],
            'INTERSECT': parameters['OSMGebudelayer'],
            'PREDICATE': [0],  # schneidet
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['KachelnMitGebaeudenExtrahieren'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Loeschen unnoetiger Felder
        alg_params = {
            'COLUMN': QgsExpression('\'left;right;top;bottom\'').evaluate(),
            'INPUT': outputs['KachelnMitGebaeudenExtrahieren']['OUTPUT'],
            'OUTPUT': parameters['Kachelnuntersuchungsgebiet']
        }
        outputs['LoeschenUnnoetigerFelder'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Kachelnuntersuchungsgebiet'] = outputs['LoeschenUnnoetigerFelder']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Gruenflaechen auf Kacheln zuschneiden
        alg_params = {
            'INPUT': parameters['OSMLanduse'],
            'OVERLAY': outputs['LoeschenUnnoetigerFelder']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['GruenflaechenAufKachelnZuschneiden'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Gruenflaechen extrahieren
        alg_params = {
            'EXPRESSION': '\"fclass\" = \'forest\' OR \"fclass\" = \'farmland\' OR  \"fclass\" = \'grass\' OR  \"fclass\" = \'meadow\' OR  \"fclass\" = \'nature_reserve\' OR  \"fclass\" = \'orchard\' OR  \"fclass\" = \'park\' OR  \"fclass\" = \'scrub\' OR  \"fclass\" = \'vineyard\'\r\n',
            'INPUT': outputs['GruenflaechenAufKachelnZuschneiden']['OUTPUT'],
            'OUTPUT': parameters['Gruenflaechen']
        }
        outputs['GruenflaechenExtrahieren'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Gruenflaechen'] = outputs['GruenflaechenExtrahieren']['OUTPUT']
        return results

    def name(self):
        return 'Schritt 1: Kacheln erzeugen_Gruenflaechen extrahieren'

    def displayName(self):
        return 'Schritt 1: Kacheln erzeugen_Gruenflaechen extrahieren'

    def group(self):
        return 'Wohnlage'

    def groupId(self):
        return 'Wohnlage'

    def createInstance(self):
        return Schritt1KachelnErzeugen_gruenflaechenExtrahieren()
