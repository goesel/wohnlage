"""
Model exported as python.
Name : Schritt 4: Normierung/Wohnlage
Group : Wohnlage
With QGIS : 32002
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Schritt4Normierungwohnlage(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('Gitter', 'Kacheln Untersuchungsgebiet', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('Punkte (2)', 'Kacheln (Gebaeude/Gruenflaechen) (Kacheln_Gebaeude_Gruenflaechen)', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('GebaeudeGewichtung', 'GebaeudeGewichtung', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=0.25))
        self.addParameter(QgsProcessingParameterNumber('GruenflaechenGewichtung', 'GruenflaechenGewichtung', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=0.25))
        self.addParameter(QgsProcessingParameterVectorLayer('Punkte', 'Kacheln (Transport/POI) (Kacheln_Transport_POI)', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('TransportGewichtung', 'TransportGewichtung', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=0.25))
        self.addParameter(QgsProcessingParameterNumber('POIGewichtung', 'POIGewichtung', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=0.25))
        self.addParameter(QgsProcessingParameterFeatureSink('Wohnlage', 'Wohnlage', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(10, model_feedback)
        results = {}
        outputs = {}

        # Flaechen verknuepfen
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'id',
            'FIELDS_TO_COPY': [''],
            'FIELD_2': 'id',
            'INPUT': parameters['Gitter'],
            'INPUT_2': parameters['Punkte (2)'],
            'METHOD': 1,  # Nur Attribute des ersten passenden Objekts verwenden (eins-zu-eins)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FlaechenVerknuepfen'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Punkte verknuepfen
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'id',
            'FIELDS_TO_COPY': [''],
            'FIELD_2': 'id',
            'INPUT': outputs['FlaechenVerknuepfen']['OUTPUT'],
            'INPUT_2': parameters['Punkte'],
            'METHOD': 1,  # Nur Attribute des ersten passenden Objekts verwenden (eins-zu-eins)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PunkteVerknuepfen'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Unnoetige Felder loeschen
        alg_params = {
            'COLUMN': ['\'fid','fid_2','id_2','fid_3','id_3\''],
            'INPUT': outputs['PunkteVerknuepfen']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['UnnoetigeFelderLoeschen'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Normierung Gebaeude
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'GebaeudeNormiert',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Fließkommazahl
            'FORMULA': '(\"gebaeudeFlaeche\"-minimum(\"gebaeudeFlaeche\"))/(maximum(\"gebaeudeFlaeche\")-minimum(\"gebaeudeFlaeche\"))',
            'INPUT': outputs['UnnoetigeFelderLoeschen']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['NormierungGebaeude'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Normierung Gruenflaechen
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'GruenflaechenNormiert',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Fließkommazahl
            'FORMULA': '(\"gruenflaechen\"-minimum(\"gruenflaechen\"))/(maximum(\"gruenflaechen\")-minimum(\"gruenflaechen\"))',
            'INPUT': outputs['NormierungGebaeude']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['NormierungGruenflaechen'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Normierung Transport
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'TransportNormiert',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Fließkommazahl
            'FORMULA': '(\"transport\"-minimum(\"transport\"))/(maximum(\"transport\")-minimum(\"transport\"))',
            'INPUT': outputs['NormierungGruenflaechen']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['NormierungTransport'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Normierung POI
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'POINormiert',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Fließkommazahl
            'FORMULA': '(\"POI\"-minimum(\"POI\"))/(maximum(\"POI\")-minimum(\"POI\"))',
            'INPUT': outputs['NormierungTransport']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['NormierungPoi'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Summe und Gewichtung
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'SumWeight',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Fließkommazahl
            'FORMULA': 'coalesce(\"GebaeudeNormiert\" ,0) *  @GebaeudeGewichtung \r\n+ coalesce( \"GruenFlaechenNormiert\" ,0) * @GruenflaechenGewichtung \r\n+ coalesce( \"TransportNormiert\" ,0) *  @TransportGewichtung \r\n+ coalesce( \"POINormiert\" ,0) *  @POIGewichtung ',
            'INPUT': outputs['NormierungPoi']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SummeUndGewichtung'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Normiert
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'Wohnlage',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Fließkommazahl
            'FORMULA': '(\"SumWeight\" - minimum(\"SumWeight\")) / (maximum(\"SumWeight\")- minimum(\"SumWeight\"))',
            'INPUT': outputs['SummeUndGewichtung']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Normiert'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Unnoetige Felder loeschen
        alg_params = {
            'COLUMN': ['id_3'],
            'INPUT': outputs['Normiert']['OUTPUT'],
            'OUTPUT': parameters['Wohnlage']
        }
        outputs['UnnoetigeFelderLoeschen'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Wohnlage'] = outputs['UnnoetigeFelderLoeschen']['OUTPUT']
        return results

    def name(self):
        return 'Schritt 4: Normierung/Wohnlage'

    def displayName(self):
        return 'Schritt 4: Normierung/Wohnlage'

    def group(self):
        return 'Wohnlage'

    def groupId(self):
        return 'Wohnlage'

    def createInstance(self):
        return Schritt4Normierungwohnlage()
