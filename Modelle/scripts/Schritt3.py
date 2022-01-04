"""
Model exported as python.
Name : Schritt 3: Flaechen
Group : Wohnlage
With QGIS : 32002
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Schritt3Flaechen(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource('Gitter', 'Kacheln (KachelnUntersuchungsgebiet)', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSource('Gebudeflchen', 'OSM-Gebaeude (gis_osm_buildings_a_free_1)', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('Grnflchen', 'Gruenflaechen', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Kacheln_gebaeude_gruenflaechen', 'Kacheln_Gebaeude_Gruenflaechen', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='TEMPORARY_OUTPUT'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(8, model_feedback)
        results = {}
        outputs = {}

        # Verschneidung Gebaeude
        alg_params = {
            'INPUT': parameters['Gitter'],
            'INPUT_FIELDS': [''],
            'OVERLAY': parameters['Gebudeflchen'],
            'OVERLAY_FIELDS': [''],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['VerschneidungGebaeude'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Gebaeude Aufloesen
        alg_params = {
            'FIELD': ['id'],
            'INPUT': outputs['VerschneidungGebaeude']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['GebaeudeAufloesen'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Verschneidung Gruenflaechen
        alg_params = {
            'INPUT': parameters['Gitter'],
            'INPUT_FIELDS': [''],
            'OVERLAY': parameters['Grnflchen'],
            'OVERLAY_FIELDS': [''],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['VerschneidungGruenflaechen'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Gruenflaechen Aufloesen
        alg_params = {
            'FIELD': ['id'],
            'INPUT': outputs['VerschneidungGruenflaechen']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['GruenflaechenAufloesen'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Gebaeudeflaechen berechnen
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'gebaeudeFlaeche',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Fließkommazahl
            'FORMULA': ' $area ',
            'INPUT': outputs['GebaeudeAufloesen']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['GebaeudeflaechenBerechnen'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Gruenflaechen berechnen
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'gruenflaechen',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Fließkommazahl
            'FORMULA': ' $area ',
            'INPUT': outputs['GruenflaechenAufloesen']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['GruenflaechenBerechnen'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Verknuepfung Gebaeude
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'id',
            'FIELDS_TO_COPY': ['gebaeudeFlaeche'],
            'FIELD_2': 'id',
            'INPUT': parameters['Gitter'],
            'INPUT_2': outputs['GebaeudeflaechenBerechnen']['OUTPUT'],
            'METHOD': 1,  # Nur Attribute des ersten passenden Objekts verwenden (eins-zu-eins)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['VerknuepfungGebaeude'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Verknuepfung Gruenflaechen
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'id',
            'FIELDS_TO_COPY': ['gruenflaechen'],
            'FIELD_2': 'id',
            'INPUT': outputs['VerknuepfungGebaeude']['OUTPUT'],
            'INPUT_2': outputs['GruenflaechenBerechnen']['OUTPUT'],
            'METHOD': 1,  # Nur Attribute des ersten passenden Objekts verwenden (eins-zu-eins)
            'PREFIX': '',
            'OUTPUT': parameters['Kacheln_gebaeude_gruenflaechen']
        }
        outputs['VerknuepfungGruenflaechen'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Kacheln_gebaeude_gruenflaechen'] = outputs['VerknuepfungGruenflaechen']['OUTPUT']
        return results

    def name(self):
        return 'Schritt 3: Flaechen'

    def displayName(self):
        return 'Schritt 3: Flaechen'

    def group(self):
        return 'Wohnlage'

    def groupId(self):
        return 'Wohnlage'

    def createInstance(self):
        return Schritt3Flaechen()
