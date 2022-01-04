"""
Model exported as python.
Name : Schritt 2: Punkte zaehlen
Group : Wohnlage
With QGIS : 32002
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Schritt2PunkteZaehlen(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('Gebudegrid', 'Kacheln (KachelnUntersuchungsgebiet)', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('POI', 'Points of Interest (gis_osm_pois_free_1)', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('Transport', 'Transport (gis_osm_transport_free_1)', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Kacheln_transport_poi', 'Kacheln_Transport_POI', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(6, model_feedback)
        results = {}
        outputs = {}

        # Transport auf Kacheln zuschneiden
        alg_params = {
            'EXTENT': parameters['Gebudegrid'],
            'INPUT': parameters['Transport'],
            'OPTIONS': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['TransportAufKachelnZuschneiden'] = processing.run('gdal:clipvectorbyextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # POI auf Kacheln zuschneiden
        alg_params = {
            'EXTENT': parameters['Gebudegrid'],
            'INPUT': parameters['POI'],
            'OPTIONS': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PoiAufKachelnZuschneiden'] = processing.run('gdal:clipvectorbyextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # POI zaehlen
        alg_params = {
            'CLASSFIELD': '',
            'FIELD': 'POI',
            'POINTS': outputs['PoiAufKachelnZuschneiden']['OUTPUT'],
            'POLYGONS': parameters['Gebudegrid'],
            'WEIGHT': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PoiZaehlen'] = processing.run('native:countpointsinpolygon', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Transport zaehlen
        alg_params = {
            'CLASSFIELD': '',
            'FIELD': 'transport',
            'POINTS': outputs['TransportAufKachelnZuschneiden']['OUTPUT'],
            'POLYGONS': parameters['Gebudegrid'],
            'WEIGHT': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['TransportZaehlen'] = processing.run('native:countpointsinpolygon', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # POI verknuepfen
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'id',
            'FIELDS_TO_COPY': ['POI'],
            'FIELD_2': 'id',
            'INPUT': parameters['Gebudegrid'],
            'INPUT_2': outputs['PoiZaehlen']['OUTPUT'],
            'METHOD': 1,  # Nur Attribute des ersten passenden Objekts verwenden (eins-zu-eins)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PoiVerknuepfen'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Transport verknuepfen
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'id',
            'FIELDS_TO_COPY': ['transport'],
            'FIELD_2': 'id',
            'INPUT': outputs['PoiVerknuepfen']['OUTPUT'],
            'INPUT_2': outputs['TransportZaehlen']['OUTPUT'],
            'METHOD': 1,  # Nur Attribute des ersten passenden Objekts verwenden (eins-zu-eins)
            'PREFIX': '',
            'OUTPUT': parameters['Kacheln_transport_poi']
        }
        outputs['TransportVerknuepfen'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Kacheln_transport_poi'] = outputs['TransportVerknuepfen']['OUTPUT']
        return results

    def name(self):
        return 'Schritt 2: Punkte zaehlen'

    def displayName(self):
        return 'Schritt 2: Punkte zaehlen'

    def group(self):
        return 'Wohnlage'

    def groupId(self):
        return 'Wohnlage'

    def createInstance(self):
        return Schritt2PunkteZaehlen()
