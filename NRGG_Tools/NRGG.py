# import arcpy
import os
import zipfile
import json
import time, datetime
import urllib
import arcpy
import requests


def listStringJoiner(inputList, joiner=","):
    '''listStringJoiner(sequence[list]) -> string
    Takes an input list and returns a string where each 
    element in the list is joined together to form a string
    returned string value. Default value to is to 
    join with a comma.
    Example: [1,2,3,4] -> '1,2,3,4'
    '''
    stringJoinedList =  joiner.join(str(itemFromList) for itemFromList in inputList)
    return stringJoinedList
    

def errorMessageGenerator(textForErrorMessage):
    '''errorMessageGenerator(string) -> string
    takes and input string and formats it to boiler-plate
    error message.
    '''

    errorText = '''There was an error {}.
    If you believe there was a mistake 
    entering parameters please try the tool again.
    This program will exit in ten seconds'''.format(textForErrorMessage)
    return errorText

def urlRequest(inputUrl, *urlParameters):
    try:
        urlurlResponse = urllib.urlopen(inputUrl, "".join(urlParameters)).read()
        return urlurlResponse
    except:
        arcpy.AddMessage(
            '''Unable to make URL request. Check your internet
        connection or input URL and try again, this program will exit in 10
        seconds.'''
        )
        time.sleep(10)
        exit()

def jsonObjectErrorHandling(urlResponse, keyValue, errorMessage):
    try:
        return json.loads(urlResponse)[keyValue]
    except:
        arcpy.AddMessage(errorMessage)
        time.sleep(10)
        exit()


def generateAGOLToken(AGOLUsername, AGOLPassword):
    """Generates a Token for use with the REST
    API for ArcGIS Online
    """
    errorText = '''generating an AGOL token.
      It is likely that you entered an incorrect
      username or password'''
      
    errorMessage =  errorMessageGenerator(errorText)
    parameters = urllib.urlencode(
        {
            "username": AGOLUsername,
            "password": AGOLPassword,
            "client": "referer",
            "referer": "https://www.arcgis.com",
            "expiration": 120,
            "f": "json",
        }
    )

    tokenURL = "https://www.arcgis.com/sharing/rest/generateToken?"
    tokenUrlResponse = urlRequest(tokenURL, parameters)
    AGOLToken = jsonObjectErrorHandling(tokenUrlResponse, "token", errorMessage)
    return AGOLToken

class AGOLFeatureServiceRESTEndPoints:
    """Leverages the ESRI Rest API to return information about feature services
    and REST URL endpoints for AGOL using Python 2.7 because the FS is still
    using ArcGIS Desktop at the Virtual Data Center
    """

    def __init__(self, AGOLFeatureServiceURL, AGOLToken, AGOLFeatureServiceLayerNumber):
        self.url = AGOLFeatureServiceURL
        self.token = AGOLToken
        self.layerNumber = AGOLFeatureServiceLayerNumber

    def layerHasPhotoAttachments(self):
        """Checks to see if an AGOL Feature Service has attachments
        """
        errorText = '''when trying to see if the input feature service 
            has attachments or the input feature service does not allow attachments.'''

        errorMessage =  errorMessageGenerator(errorText)
        areThereAttachmentsURL = urlRequest(
            "{0}/{1}?&f=json&token={2}".format(self.url, self.layerNumber, self.token)
        )
        if jsonObjectErrorHandling(areThereAttachmentsURL, "hasAttachments", errorMessage):
            return True

    def name(self):

        """Returns the name of the AGOL Feature
         Service from the input AGOL Feature Service URL
        """
        errorText = '''There was an error trying to retreive 
        the name of the input feature service'''
        errorMessage =  errorMessageGenerator(errorText)

        AGOLFeatureServiceNameURL = urlRequest(
            "{0}?&f=json&token={1}".format(self.url, self.token)
        )
        AGOLFeatureServiceName = jsonObjectErrorHandling(AGOLFeatureServiceNameURL, "layers", errorMessage)
        AGOLFeatureServiceName = AGOLFeatureServiceName[0]
        #AGOLFeatureServiceName = str(AGOLFeatureServiceName["name"])
        AGOLFeatureServiceName = AGOLFeatureServiceName["name"].encode('utf-8', 'ignore')
        return AGOLFeatureServiceName

    def getFeatureServiceObjectIds(self):
        """Returns the ObjectIDs for each item in the AGOL Feature Service.
        it is best to use this method as ObjectIDs may not be sequential.
        for example the ObjectIDs could number 1,2,3,5,6,12,13... this
        is a result of delete field collected data after syncing
        """
        errorText = '''when trying to retrieve the ObjectIds 
        for the input feature service''' 
        errorMessage =  errorMessageGenerator(errorText)

        featureServiceObjectIDsURL = urlRequest(
            "{0}/{1}/query?where=1=1&returnIdsOnly=true&f=json&token={2}".format(
                self.url, self.layerNumber, self.token
            )
        )
        featureServiceObjectIDs = jsonObjectErrorHandling(featureServiceObjectIDsURL ,"objectIds", errorMessage)
        featureServiceObjectIDs = featureServiceObjectIDs[:]
        featureServiceObjectIDs = listStringJoiner(featureServiceObjectIDs)
        return featureServiceObjectIDs

    def getFeatureServiceObjectIdsWithinAreaOfInterest(
        self, areaOfInterestVerticesDictionary
    ):
        """Returns the ObjectIDs for each item in the AGOL Feature Service that
        that fall within an end user provided area of interst.
        it is best to use this method as ObjectIDs may not be sequential.
        for example the ObjectIDs could number 1,2,3,5,6,12,13... this
        is a result of delete field collected data after syncing
        """
        errorText = '''when trying to find points
        that fall within the provided area of interest'''
        
        errorMessage =  errorMessageGenerator(errorText)

        urlEncodedParameters = urllib.urlencode(
            {"geometryType": "esriGeometryPolygon",
            "spatialRel": "esriSpatialRelContains",
            "inSR": 4326,
            "geometry": areaOfInterestVerticesDictionary
            }
        )
        urlRequestString = "{0}/{1}/query?where=1=1&returnIdsOnly=true&f=json&token={2}".format( self.url, self.layerNumber, self.token)
        featureServiceObjectIDs = urlRequest(urlRequestString, urlEncodedParameters)
        featureServiceObjectIDs = jsonObjectErrorHandling(featureServiceObjectIDs, "objectIds", errorMessage)
        featureServiceObjectIDs = featureServiceObjectIDs[:]
        featureServiceObjectIDs = listStringJoiner(featureServiceObjectIDs)
        return featureServiceObjectIDs

    def queryFeatureServiceObjectIDsforAttachments(self, AGOLfeatureServiceOjbectIDs):
        """Returns the ObjectIds for each feature in the AGOL Feature Service
        which has attachments.
        """
        errorText = '''when trying to retrieve objectIDs for 
        input feature service'''
        errorMessage =  errorMessageGenerator(errorText)

        urlEncodedParameters = urllib.urlencode(
            {"objectIds": AGOLfeatureServiceOjbectIDs}
        )
        urlRequestString = "{0}/{1}/queryAttachments?&f=json&token={2}".format(self.url, self.layerNumber, self.token)
        featureServiceObjectIDsThatHaveAttachmentsURL = urlRequest(urlRequestString, urlEncodedParameters)
        AGOLfeatureServiceObjectIDsThatHaveAttachments = jsonObjectErrorHandling(featureServiceObjectIDsThatHaveAttachmentsURL, "attachmentGroups", errorMessage)
        AGOLfeatureServiceObjectIDsThatHaveAttachments = [
            objectIDWithPhoto["parentObjectId"]
            for objectIDWithPhoto in AGOLfeatureServiceObjectIDsThatHaveAttachments
        ]
        AGOLfeatureServiceObjectIDsThatHaveAttachments = listStringJoiner(AGOLfeatureServiceObjectIDsThatHaveAttachments)
        return AGOLfeatureServiceObjectIDsThatHaveAttachments


def DeleteUneededFiedsFromFinalFeatureclass(finalFeatureClass):
    listOfFieldsToKeep = []
    fieldsToDelete = [
        field.name
        for field in arcpy.ListFields(finalFeatureClass)
        if field.name not in listOfFieldsToKeep
    ]
    arcpy.DeleteField_management("finalFeatureClass", fieldsToDelete)


def getStatusURLForFeatureServiceReplicaForPhotoAttachments(
    AGOLFeatureServiceName,
    AGOLFeatureServiceURL,
    AGOLToken,
    AGOLFeatureServiceLayerNumber,
    AGOLFeatureServiceObjectIDs,
):
    errorText = '''trying to retrieve the status URL for the replica
    of the AGOL Feature Service'''
    errorMessage = errorMessageGenerator(errorText)
    replicaParameters = urllib.urlencode(
        {
            "name": AGOLFeatureServiceName,
            "layers": AGOLFeatureServiceLayerNumber,
            "layerQueries": {
                AGOLFeatureServiceLayerNumber: {
                    "where": "OBJECTID IN (" + AGOLFeatureServiceObjectIDs + ")"
                }
            },
            "transportType": "esriTransportTypeUrl",
            "returnAttachments": True,
            "returnAttachmentsDatabyURL": True,
            "syncDirection": "bidirectional",
            "attachmentsSyncDirection": "bidirectional",
            "async": True,
            "syncModel": "none",
            "dataFormat": "filegdb",
        }
    )

    AGOLCreateFeatureServieReplicaURL = "{0}/createReplica/?f=json&token={1}".format(
        AGOLFeatureServiceURL, AGOLToken
    )
    AGOLCreateFeatureServieReplicaURLRequest = urlRequest(
        AGOLCreateFeatureServieReplicaURL, replicaParameters
    )
    #AGOLFeatureServiceReplicaStatusURL = json.loads(AGOLCreateFeatureServieReplicaURLRequest)["statusUrl"]
    AGOLFeatureServiceReplicaStatusURL = jsonObjectErrorHandling(AGOLCreateFeatureServieReplicaURLRequest, "statusUrl", errorMessage)
    return AGOLFeatureServiceReplicaStatusURL


def waitForAGOLFeatureServiceReplica(AGOLFeatureServiceReplicaStatusURL, AGOLToken):
    timer = 0
    status = json.loads(
        urllib.urlopen(
            "{0}?f=json&token={1}".format(AGOLFeatureServiceReplicaStatusURL, AGOLToken)
        ).read()
    )
    while status["resultUrl"] == "":
        time.sleep(10)
        timer += 10
        status = json.loads(
            urllib.urlopen(
                "{0}?f=json&token={1}".format(
                    AGOLFeatureServiceReplicaStatusURL, AGOLToken
                )
            ).read()
        )
        if timer > 1000:
            raise Exception(
                "It took too long to make the AGOL Repica. Try again at a different time"
            )
        if status["status"] in ("Failed", "CompletedWithErrors"):
            raise Exception(
                "There was an error creating the AGOL Replica. Check your inputs and try again"
            )
    else:
        AGOLFeatureServiceReplicaResultURL = status["resultUrl"]
        return AGOLFeatureServiceReplicaResultURL


def downloadAGOLReplicaInFGDB(
    AGOLReplicaResultURL, AGOLToken, AGOLFeatureServiceName, outputLocation
):
    urlResponse = requests.get(
        "{0}?token={1}".format(AGOLReplicaResultURL, AGOLToken), stream=True
    )
    nameOfAGOLReplicaZipFile = unicode("{}.zip".format(AGOLFeatureServiceName))
    fullPathAGOLReplicaOfZipFile = os.path.join(
        outputLocation, nameOfAGOLReplicaZipFile
    )
    with open(fullPathAGOLReplicaOfZipFile, "wb") as AGOLReplicaOfZipFile:
        sizeOfFile = urlResponse.headers.get("content-length")
        if sizeOfFile is None:
            AGOLReplicaOfZipFile.write(urlResponse.content)
        else:
            sizeOfFile = int(sizeOfFile)
        chunk = 1
        for data in urlResponse.iter_content(chunk_size=sizeOfFile / 10):
            arcpy.AddMessage(
                str(int((float(chunk) / float(sizeOfFile)) * 100))
                + "% of the file has downloaded"
            )
            AGOLReplicaOfZipFile.write(data)
            chunk += sizeOfFile / 10
    return fullPathAGOLReplicaOfZipFile

class areaOfInterestHandlingForSpatialFilteringAGOLFeatureService:
    """A class to handle an area of interest for spatial filtering
    an AGOL feature service
    """
    
    def __init__(self, areaOfInterestFeatureClassPath):
        self.pathToAOI = areaOfInterestFeatureClassPath
        
    def projectFeatureClassToGCSWGS84IntoDefaultWorkspace(self):
        """Takes and area of interest and projects the 
        data to a Geographic Coordinate System of
        WGS_84
        """
        projection = """GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"""
        arcpy.Project_management(
            self.pathToAOI, arcpy.env.workspace + "/projectedAreaofInterest", projection
        )
        return arcpy.env.workspace + "/projectedAreaofInterest"

    def getVerticesFromProjectedFeatureClassAreaofInterest(self, projectedAreaOfInterestFeatureClass):
        arcpy.MakeFeatureLayer_management(projectedAreaOfInterestFeatureClass, "projectedAreaofInterest")
        areaOfInterestVertices = []
        cursor = arcpy.da.SearchCursor("projectedAreaofInterest", ["OID@", "SHAPE@"])
        locationOfShapeFieldInReturnedCursorRow = 1
        for row in cursor:
            for points in row[locationOfShapeFieldInReturnedCursorRow]:
                for point in points:
                    if point:
                        areaOfInterestVertices.append([point.X, point.Y])
        return areaOfInterestVertices

    def makeAreaOfInterestDictionaryForURLEndPoint(self, areaOfInterestVertices):
        areaOfInterestVerticesDictionary = {}
        areaOfInterestVerticesDictionary["rings"] = [areaOfInterestVertices]
        #areaOfInterestVerticesDictionary["spatialReference"] = {"wkid": 4326}
        return areaOfInterestVerticesDictionary

def unzipAGOLReplicaGDBAndRenameToFSVeg(pathOfZippedReplicaGDB, outputLocation):
    with zipfile.ZipFile(pathOfZippedReplicaGDB, "r") as zipGDB:
        zipGDB = zipfile.ZipFile(pathOfZippedReplicaGDB, "r")
        uniqueAGOLGenerateReplicaGDBName = zipGDB.namelist()[0].split(r"/")[0]
        zipGDB.extractall(outputLocation)
        arcpy.Rename_management(
            outputLocation + "/" + uniqueAGOLGenerateReplicaGDBName, "FSVeg_Spatial_WT"
        )

def renamePlotsToFSVeg_Spatial_WT_PhotosInGDB(outputLocation):
    arcpy.env.workspace = outputLocation + "/FSVeg_Spatial_WT.gdb"
    # I use FC to FC here rather than rename as it allows for all the attachment
    # files inthe GDB to be called FSVeg_Spatial_WT_Photos and allows for
    # delteting of fields that Natalie and Renate did now want the end user to see
    arcpy.arcpy.FeatureClassToFeatureClass_conversion(
        "plots", outputLocation + "/FSVeg_Spatial_WT.gdb", "FSVeg_Spatial_WT_Photos"
    )
    
    arcpy.Delete_management(outputLocation + "/FSVeg_Spatial_WT.gdb/plots")
    arcpy.Delete_management(outputLocation + "/FSVeg_Spatial_WT.gdb/plots__ATTACH")
    arcpy.Delete_management(outputLocation + "/FSVeg_Spatial_WT.gdb/plots__ATTACHREL")

def createDictionaryOfFSVegGlobadIDsPlotSettingAndPlotNumber(outputLocation):
    arcpy.env.workspace = outputLocation + "/FSVeg_Spatial_WT.gdb"
    cursor = arcpy.da.SearchCursor(
        "FSVeg_Spatial_WT_Photos", ["GlobalID", "pl_setting_id", "plot_number_1"]
    )
    FSVegGlobalIDDictionary = {}
    for row in cursor:
        if row[1] is not None and row[1].isdigit():
            key = row[0]
            vals = row[1:]
            FSVegGlobalIDDictionary[key] = vals
    del cursor
    del row
    return FSVegGlobalIDDictionary


def writeAttachedPhotosAndMakeDictionaryOfFSVegPhotoNames(
    outputLocation, FSVegGlobalIDDictionary
):
    if os.path.exists(outputLocation + "//FSVeg_Spatial_WT_Photos"):
        pass
    else:
        os.mkdir(outputLocation + "//FSVeg_Spatial_WT_Photos")
    arcpy.env.workspace = outputLocation + "/FSVeg_Spatial_WT.gdb"
    photoNameDictionary = {}
    with arcpy.da.SearchCursor(
        "FSVeg_Spatial_WT_Photos__ATTACH", ["DATA", "ATT_NAME", "REL_GLOBALID"]
    ) as cursor:
        for row in cursor:
            if row[2] in FSVegGlobalIDDictionary:
                attachment = row[0]
                fileNumber = (
                    str(FSVegGlobalIDDictionary[row[2]][0])
                    + "_plot"
                    + str(FSVegGlobalIDDictionary[row[2]][1])
                )
                attachmentName = row[1].encode('utf-8', 'ignore')
                stringStartLocation = attachmentName.find("photo_plot")
                if (
                    attachmentName[stringStartLocation + 10 : stringStartLocation + 11]
                    == "-"
                ):
                    filename = fileNumber + "_1.jpg"
                else:
                    filename = (
                        fileNumber
                        + "_"
                        + attachmentName[
                            stringStartLocation + 11 : stringStartLocation + 12
                        ]
                        + ".jpg"
                    )
                open(
                    outputLocation + "//FSVeg_Spatial_WT_Photos" + os.sep + filename,
                    "wb",
                ).write(attachment.tobytes())
                if row[2] not in photoNameDictionary:
                    photoNameDictionary[row[2]] = [filename]
                else:
                    photoNameDictionary[row[2]].append(filename)
                del row
                del fileNumber
                del filename
                del attachment
            else:
                pass
    return photoNameDictionary



def addPhotoNameFieldAndPopulateFinalFSVegFeatureClass(
    outputLocation, photoNameDictionary
):
    arcpy.env.workspace = outputLocation + "/FSVeg_Spatial_WT.gdb"
    arcpy.AddField_management(
        "FSVeg_Spatial_WT_Photos", "PhotoNames", "TEXT", "#", "#", 250
    )
    edit = arcpy.da.Editor(
        outputLocation + "/FSVeg_Spatial_WT.gdb"
    )  # dirname of the fc is the db name
    edit.startEditing(False, False)  # check these setting for your environment
    edit.startOperation()
    cursor = arcpy.da.UpdateCursor(
        "FSVeg_Spatial_WT_Photos", ["GlobalID", "PhotoNames"]
    )
    for row in cursor:
        if row[0] in photoNameDictionary:
            row[1] = ",".join(photoNameDictionary[row[0]])
        cursor.updateRow(row)
    edit.stopOperation()
    edit.stopEditing(True)


def DeleteUneededFiedsFromFinalFSVegFeatureclass(outputLocation):
    arcpy.env.workspace = outputLocation + "/FSVeg_Spatial_WT.gdb"
    listOfFieldsToKeep = [
        "globalid",
        "pl_setting_id",
        "plot_number_1",
        "photo_1_text",
        "PhotoNames",
    ]
    fieldsToDelete = [
        field.name
        for field in arcpy.ListFields("FSVeg_Spatial_WT_Photos")
        if field.name not in listOfFieldsToKeep and not field.required
    ]
    arcpy.DeleteField_management("FSVeg_Spatial_WT_Photos", fieldsToDelete)

def deleteFeaturesWithIncorrectSettingIDValues(outputLocation):
    arcpy.MakeFeatureLayer_management(outputLocation + os.sep + "FSVeg_Spatial_WT.gdb" + os.sep + "FSVeg_Spatial_WT_Photos", "FSVeg_Spatial_WT_Photos")
    arcpy.SelectLayerByAttribute_management('FSVeg_Spatial_WT_Photos', "NEW_SELECTION", 'PhotoNames IS NULL')
    arcpy.DeleteFeatures_management("FSVeg_Spatial_WT_Photos")

def alterPlotSettingIDFieldName(outputLocation):
    arcpy.MakeTableView_management(outputLocation + os.sep + "FSVeg_Spatial_WT.gdb" + os.sep + "FSVeg_Spatial_WT_Photos", "FSVeg_Spatial_WT_PhotosTable")
    arcpy.AlterField_management("FSVeg_Spatial_WT_PhotosTable", "pl_setting_id", "Setting_ID", "Setting_ID")