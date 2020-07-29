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

        sys.path.append(r'C:\Data\FSVeg_Sp_WT_AGOL_PhototDownload\NRGG')
        import FSVegAGOLPhotoDownloadTools as NRGG


        arcpy.env.overwriteOutput = True

        AGOLUsername = parameters[0].valueAsText
        AGOLPassword = parameters[1].valueAsText
        outputLocation = parameters[2].valueAsText
        areaofInterest = parameters[3].valueAsText
        AGOLFeatureServiceLayerNumber = 3

        AGOLFeatureServiceURL =  r'https://services1.arcgis.com/gGHDlz6USftL5Pau/arcgis/rest/services/survey123_a15e8159fac04b6f86e6cee04a785793_stakeholder/FeatureServer'

        AGOLToken = NRGG.generateAGOLToken(AGOLUsername, AGOLPassword)
        AGOLFeatureService = NRGG.AGOLFeatureServiceRESTEndPoints(AGOLFeatureServiceURL, AGOLToken, AGOLFeatureServiceLayerNumber)

        if AGOLFeatureService.layerHasPhotoAttachments():
            if areaofInterest:
                projectedFeatueclassPath = NRGG.projectFeatureClassToGCSWGS_84IntoDefaultWorkspace(areaofInterest)
                areaOfInterestVertices = NRGG.getVerticesFromProjectedFeatureClassAreaofInterest(projectedFeatueclassPath)
                dictionaryOfAreaOfInterestVerticesForEndPointURL = NRGG.makeAreaOfInterestDictionaryForURLEndPoint(areaOfInterestVertices)
                AGOLFeatureServiceObjectIDs = AGOLFeatureService.getFeatureServiceObjectIdsWithinAreaOfInterest(dictionaryOfAreaOfInterestVerticesForEndPointURL)
            else:
                AGOLFeatureServiceObjectIDs = AGOLFeatureService.getFeatureServiceObjectIds()
        else:
            raise Exception ('The AGOL Feature Service Layer that you want to download photos from does not have photos attached')

        AGOLFeatureServiceObjectIDsWithAttachments = AGOLFeatureService.queryFeatureServiceObjectIDsforAttachments(AGOLFeatureServiceObjectIDs)
        satusURLForReplicaOfFeaturesWithAttachments = NRGG.getStatusURLForFeatureServiceReplicaForPhotoAttachments(AGOLFeatureService.name(), AGOLFeatureService.url, AGOLFeatureService.token, AGOLFeatureService.layerNumber, AGOLFeatureServiceObjectIDsWithAttachments)
        arcpy.AddMessage(satusURLForReplicaOfFeaturesWithAttachments)
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
        






        # outGDB = ''
        # print 'Unzipping...'
        # with zipfile.ZipFile(outFile, 'r') as zipGDB:
        #   outGDB = zipGDB.namelist()[0].split(r'/')[0]
        #   zipGDB.extractall(outputLocation)
        #   arcpy.Rename_management(outputLocation + '/' + outGDB, 'FSVeg_Spatial_WT')
        # if areaofInterest:
        #     arcpy.MakeFeatureLayer_management(outputLocation + '/FSVeg_Spatial_WT.gdb/plots', 'inMemoryPlots')
        #     arcpy.MakeFeatureLayer_management(arcpy.env.workspace + '/projectedAreaofInterest', "projectedAreaofInterest")
        #     arcpy.SelectLayerByLocation_management('inMemoryPlots', 'INTERSECT', "projectedAreaofInterest", '#', 'NEW_SELECTION', 'NOT_INVERT')
        #     arcpy.arcpy.FeatureClassToFeatureClass_conversion('inMemoryPlots', outputLocation + '/FSVeg_Spatial_WT.gdb', 'FSVeg_Spatial_WT_Photos')
        #     inTable = 'FSVeg_Spatial_WT_Photos__ATTACH'
        #     arcpy.Delete_management(outputLocation + '/FSVeg_Spatial_WT.gdb/plots')
        #     arcpy.Delete_management(outputLocation + '/FSVeg_Spatial_WT.gdb/plots__ATTACH')
        #     arcpy.Delete_management(outputLocation + '/FSVeg_Spatial_WT.gdb/plots__ATTACHREL')
        # else:
        #     arcpy.env.workspace = outputLocation + '/FSVeg_Spatial_WT.gdb'
        #     arcpy.Rename_management('plots','FSVeg_Spatial_WT_Photos')
        #     arcpy.Rename_management('plots__ATTACH','FSVeg_Spatial_WT_Photos__ATTACH')
        #     arcpy.Rename_management('plots__ATTACHREL','FSVeg_Spatial_WT_Photos__ATTACHREL')
        # arcpy.env.workspace = outputLocation + '/FSVeg_Spatial_WT.gdb'
        # inTable = 'FSVeg_Spatial_WT_Photos__ATTACH'
        # cursor = arcpy.da.SearchCursor('FSVeg_Spatial_WT_Photos', ['GlobalID', 'pl_setting_id', 'plot_number_1'])
        #
        # valueDi = {}
        # for row in cursor:
        #      key = row[0]
        #      vals = row[1:]
        #      if key not in valueDi:
        #           valueDi[key] = []
        #           valueDi[key] = vals
        #      else:
        #           valueDi[key] = vals
        # del(cursor)
        #
        # photoNameDict = {}
        # os.mkdir(outputLocation + '//FSVeg_Spatial_WT_Photos')
        # with arcpy.da.SearchCursor(inTable, ['DATA', 'ATT_NAME', 'REL_GLOBALID']) as cursor:
        #   for item in cursor:
        #     if item[2] in valueDi:
        #         attachment = item[0]
        #         filenum = str(valueDi[item[2]][0]) + "_plot" + str(valueDi[item[2]][1])
        #         attachmentName = str(item[1])
        #         loc = attachmentName.find('photo_plot')
        #         if attachmentName[loc + 10: loc +11] == '-':
        #           filename = filenum  + "_1.jpg"
        #         else:
        #           filename = filenum  + '_' + attachmentName[loc + 11: loc +12] + '.jpg'
        #         open(outputLocation + '//FSVeg_Spatial_WT_Photos' + os.sep + filename, 'wb').write(attachment.tobytes())
        #         if item[2] not in photoNameDict:
        #           photoNameDict[item[2]] = [filename]
        #         else:
        #           photoNameDict[item[2]].append(filename)
        #         del item
        #         del filenum
        #         del filename
        #         del attachment
        #     else:
        #         pass
        #
        # arcpy.AddField_management('FSVeg_Spatial_WT_Photos', 'PhotoNames', 'TEXT', '#', '#', 250)
        # edit = arcpy.da.Editor(outputLocation + '/FSVeg_Spatial_WT.gdb') # dirname of the fc is the db name
        # edit.startEditing(False, False) # check these setting for your environment
        # edit.startOperation()
        # cursor = arcpy.da.UpdateCursor('FSVeg_Spatial_WT_Photos', ['GlobalID', 'PhotoNames'])
        # for row in cursor:
        #   if row[0] in photoNameDict:
        #     row[1] = ','.join(photoNameDict[row[0]])
        #   cursor.updateRow(row)
        # edit.stopOperation()
        # edit.stopEditing(True)
        #
        # arcpy.AlterField_management("FSVeg_Spatial_WT_Photos","pl_setting_id", "Setting_ID", "Setting_ID")
        # arcpy.Delete_management(outFile)
