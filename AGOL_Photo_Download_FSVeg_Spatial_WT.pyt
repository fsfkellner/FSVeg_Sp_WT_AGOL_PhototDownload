######################################
# This toolbox was developed by Fred Kellner,
# RedCastle Resources Contract Remote Sensing Analsyst to the Region 1
# Geospatial Group. For Question regarding the code in this script please
# contact me at frederickkellner@usda.gov
######################################
import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "A toolbox to download photos attached to editable feature services in ArcGIS Online"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [DownloadAGOLPhotos]


class DownloadAGOLPhotos(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Photo Data from Survey123/ AGOL FSVeg Spatial WT Form "
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(displayName = 'AGOL Username',
        name = 'AGOL Username',
        datatype ='GPString',
        parameterType ="Required",
        direction ="Input")

        param1 = arcpy.Parameter(displayName = 'AGOL Password',
        name = 'AGOL Password',
        datatype ='GPStringHidden',
        parameterType ="Required",
        direction ="Input")

        param2 = arcpy.Parameter(displayName = 'Output Folder',
        name = 'Output folder location where a folder containing photos and filegeodatabase will be written',
        datatype ='DEFolder',
        parameterType ="Required",
        direction ="Input")

        param3 = arcpy.Parameter(displayName = 'Project Area Boundary',
        name = 'Provide a Feature Class of your Project Boundary',
        datatype ='GPFeatureLayer',
        parameterType ="Optional",
        direction ="Input")

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        import sys
        import arcpy

        sys.path.append(r'C:\Data\FSVeg_Sp_WT_AGOL_PhototDownload\NRGG_Tools')
        import NRGG
        from NRGG import (
            Python2RESTAPI,
            FeatureClassForAGOLFiltering
        )

        arcpy.env.overwriteOutput = True

        AGOLUsername = parameters[0].valueAsText
        AGOLPassword = parameters[1].valueAsText
        outputLocation = parameters[2].valueAsText
        areaofInterest = parameters[3].valueAsText
        AGOLFeatureServiceLayerNumber = 3

        AGOLFeatureServiceURL =  r'https://services1.arcgis.com/gGHDlz6USftL5Pau/arcgis/rest/services/survey123_a15e8159fac04b6f86e6cee04a785793_stakeholder/FeatureServer'

        AGOLToken = NRGG.generateAGOLToken(AGOLUsername, AGOLPassword)
        AGOLFeatureService = Python2RESTAPI(AGOLFeatureServiceURL, AGOLToken, AGOLFeatureServiceLayerNumber)

        if AGOLFeatureService.layerHasPhotoAttachments():
            if areaofInterest:
                areaofInterestForAGOL = FeatureClassForAGOLFiltering(areaofInterest)
                projectedFeatueclassPath = areaofInterestForAGOL.projectFeatureClassToGCSWGS84IntoDefaultWorkspace()
                areaOfInterestVertices = areaofInterestForAGOL.getVerticesFromProjectedFeatureClassAreaofInterest(projectedFeatueclassPath)
                dictionaryOfAreaOfInterestVerticesForEndPointURL = areaofInterestForAGOL.makeAreaOfInterestDictionaryForURLEndPoint(areaOfInterestVertices)
                AGOLFeatureServiceObjectIDs = AGOLFeatureService.getFeatureServiceObjectIdsWithinAreaOfInterest(dictionaryOfAreaOfInterestVerticesForEndPointURL)
            else:
                AGOLFeatureServiceObjectIDs = AGOLFeatureService.getFeatureServiceObjectIds()
        else:
            raise Exception ('The AGOL Feature Service Layer that you want to download photos from does not have photos attached')

        AGOLFeatureServiceObjectIDsWithAttachments = AGOLFeatureService.queryFeatureServiceObjectIDsforAttachments(AGOLFeatureServiceObjectIDs)
        
        satusURLForReplicaOfFeaturesWithAttachments = NRGG.getStatusURLForFeatureServiceReplicaForPhotoAttachments(AGOLFeatureService.name(), AGOLFeatureService.url, AGOLFeatureService.token, AGOLFeatureService.layerNumber, AGOLFeatureServiceObjectIDsWithAttachments)
        resutlURLForReplica = NRGG.waitForAGOLFeatureServiceReplica(satusURLForReplicaOfFeaturesWithAttachments, AGOLToken)
        pathOfZippedReplicaGDB = NRGG.downloadAGOLReplicaInFGDB(resutlURLForReplica, AGOLFeatureService.token, AGOLFeatureService.name(), outputLocation)

        NRGG.unzipAGOLReplicaGDBAndRenameToFSVeg(pathOfZippedReplicaGDB, outputLocation)

        NRGG.renamePlotsToFSVeg_Spatial_WT_PhotosInGDB(outputLocation)
        FSVegGlobalIDDictionary = NRGG.createDictionaryOfFSVegGlobadIDsPlotSettingAndPlotNumber(outputLocation)
        dictionaryOfFSVegPhotoNames = NRGG.writeAttachedPhotosAndMakeDictionaryOfFSVegPhotoNames(outputLocation, FSVegGlobalIDDictionary)
        NRGG.addPhotoNameFieldAndPopulateFinalFSVegFeatureClass(outputLocation, dictionaryOfFSVegPhotoNames)
        
        NRGG.DeleteUneededFiedsFromFinalFSVegFeatureclass(outputLocation)
        NRGG.deleteFeaturesWithIncorrectSettingIDValues(outputLocation)
        NRGG.alterPlotSettingIDFieldName(outputLocation)