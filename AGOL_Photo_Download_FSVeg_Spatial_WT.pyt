######################################
# This toolbox was developed by Fred Kellner, RedCastle Resources Contract Remote Sensing Analsyst to the Region 1 Geospatial Group. For Question regarding the code in this script please
# me at frederickkellner@fs.fed.us
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
        import arcpy
        import os
        import zipfile
        import json
        import  time,datetime
        import urllib,urllib2
        arcpy.env.overwriteOutput = True

        username = parameters[0].valueAsText
        password = parameters[1].valueAsText
        outputLocation = parameters[2].valueAsText
        ProjectArea = parameters[3].valueAsText

        arcpy.env.overwriteOutput = True

        AGOLGroupUrl =  r'https://services1.arcgis.com/gGHDlz6USftL5Pau/arcgis/rest/services/survey123_a15e8159fac04b6f86e6cee04a785793_stakeholder/FeatureServer'
        projection = '''GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]'''

        def urlRequest(request,*urlparams):
          try:
            urlresponse = urllib.urlopen(request, ''.join(urlparams)).read()
            return urlresponse
          except:
            import time
            arcpy.AddMessage('Unable to make URL request. Check your internet connection or input URL and try again, this program will exit in 10 seconds.')
            time.sleep(10)
            exit()

        start = AGOLGroupUrl.find('services/')
        start = start + 8
        end  = AGOLGroupUrl.find('/', start+1)
        name = AGOLGroupUrl[start:end]
        name = name.replace('/','')

        parameters = urllib.urlencode({
          'username': username,
          'password': password,
          'client': 'referer',
          'referer': 'https://www.arcgis.com',
          'expiration': 120,
          'f': 'json'
           })

        tokenURL = '{0}/sharing/rest/generateToken?'.format('https://www.arcgis.com')
        response = urlRequest(tokenURL, parameters)

        try:
          token = json.loads(response)['token']
        except:
          arcpy.AddMessage('There was a problem generating an AGOL token. It is likely that you entered an incorrect username or password. This program will exit in ten seconds')
          time.sleep(10)
          exit()

        GroupUrl = AGOLGroupUrl + "/3/query?where=1=1"
        if ProjectArea:
          arcpy.FeatureClassToFeatureClass_conversion(ProjectArea,  'in_memory', "ProjectArea")
          arcpy.Project_management('in_memory/ProjectArea', arcpy.env.workspace + '/ProprojectArea', projection)
          arcpy.MakeFeatureLayer_management(arcpy.env.workspace + '/ProprojectArea', "ProprojectArea")
          desc = arcpy.Describe("ProprojectArea")

          Xmin = desc.extent.XMin
          Ymin = desc.extent.YMin
          Xmax = desc.extent.XMax
          Ymax = desc.extent.YMax

          createReplicaURL = '''{0}&f=json&geometryType=esriGeometryEnvelope&geometry={1},{2},{3},{4}&token={5}'''.format(GroupUrl, Xmin, Ymin, Xmax, Ymax, token)
        else:
          createReplicaURL = '''{0}&f=json&token={1}'''.format(GroupUrl, token)

        ######################################################################################################################
        createReplReq = urlRequest(createReplicaURL)
        thisJob = json.loads(createReplReq)

        try:
          thisJob['features']
        except:
          arcpy.AddMessage('Given the parameters that you entered there are no plots which contain photos. Consider using a different project area and rerun this toolbox. This program will exit in 10 seconds.')
          time.sleep(10)
          exit()

        if not thisJob['features']:
          arcpy.AddMessage('Given the parameters that you entered there are no plots which contain photos. Consider using a different project area and rerun this toolbox. This program will exit in 10 seconds.')
          time.sleep(10)
          exit()

        else:
            objectids = []

            for i in range(len(thisJob['features'])):
                objectids.append(thisJob['features'][i]['attributes']['objectid'])

            objectids = ','.join(str(e) for e in objectids)

            replicaParameters = urllib.urlencode({
              'name': name,
              'layers':"3",
              "layerQueries": {"3":{"where":'OBJECTID IN (' + objectids + ')'}},
              "transportType":"esriTransportTypeUrl",
              "returnAttachments":True,
              "returnAttachmentsDatabyURL":True,
              "syncDirection":"bidirectional",
              "attachmentsSyncDirection":"bidirectional",
              "async":True,
              "syncModel":"none",
              "dataFormat":"filegdb",
            })

            createReplicaURL = '{0}/createReplica/?f=json&token={1}'.format(AGOLGroupUrl, token)
            createReplReq = urlRequest(createReplicaURL, replicaParameters)
            thisJob = json.loads(createReplReq)
            arcpy.AddMessage('Downloading Photo Attachments for feature Layer plots Group 1')

            if not "statusUrl" in thisJob:
              raise Exception("invalid job: {0}".format(thisJob))
            jobUrl = thisJob["statusUrl"]
            resultUrl = ""
            sanityCounter = 1000

            while resultUrl == "":
              checkReq = urllib2.urlopen("{0}?f=json&token={1}".format(jobUrl, token))
              statusText = checkReq.read()
              status = json.loads(statusText)
              if "resultUrl" in status.keys():
                resultUrl = status["resultUrl"]
              if sanityCounter < 0:
                raise Exception('took too long to make replica')
              if status["status"] == "Failed" or status["status"] == "CompletedWithErrors":
                raise Exception('Create Replica Issues: {0}'.format(status["status"]))
              sanityCounter = sanityCounter - 1
              time.sleep(10)
            resultReq = urllib2.urlopen("{0}?token={1}".format(resultUrl, token))

            outDB =  unicode(name + '_plots.zip')
            outFile = os.path.join(outputLocation, outDB)
            with open(outFile, 'wb') as output:
              output.write(resultReq.read())
              del(output)

            outGDB = ''
            print 'Unzipping...'
            with zipfile.ZipFile(outFile, 'r') as zipGDB:
              outGDB = zipGDB.namelist()[0].split(r'/')[0]
              zipGDB.extractall(outputLocation)
              arcpy.Rename_management(outputLocation + '/' + outGDB, 'FSVeg_Spatial_WT')
            if ProjectArea:
                arcpy.MakeFeatureLayer_management(outputLocation + '/FSVeg_Spatial_WT.gdb/plots', 'pts')
                arcpy.MakeFeatureLayer_management(arcpy.env.workspace + '/ProprojectArea', "ProprojectArea")
                arcpy.SelectLayerByLocation_management('pts', 'INTERSECT', "ProprojectArea", '#', 'NEW_SELECTION', 'NOT_INVERT')
                arcpy.arcpy.FeatureClassToFeatureClass_conversion('pts', outputLocation + '/FSVeg_Spatial_WT.gdb', 'FSVeg_Spatial_WT_Photos')
                inTable = 'FSVeg_Spatial_WT_Photos__ATTACH'
                arcpy.Delete_management(outputLocation + '/FSVeg_Spatial_WT.gdb/plots')
                arcpy.Delete_management(outputLocation + '/FSVeg_Spatial_WT.gdb/plots__ATTACH')
                arcpy.Delete_management(outputLocation + '/FSVeg_Spatial_WT.gdb/plots__ATTACHREL')
            else:
                arcpy.env.workspace = outputLocation + '/FSVeg_Spatial_WT.gdb'
                arcpy.Rename_management('plots','FSVeg_Spatial_WT_Photos')
                arcpy.Rename_management('plots__ATTACH','FSVeg_Spatial_WT_Photos__ATTACH')
                arcpy.Rename_management('plots__ATTACHREL','FSVeg_Spatial_WT_Photos__ATTACHREL')
            arcpy.env.workspace = outputLocation + '/FSVeg_Spatial_WT.gdb'
            inTable = 'FSVeg_Spatial_WT_Photos__ATTACH'
            cursor = arcpy.da.SearchCursor('FSVeg_Spatial_WT_Photos', ['GlobalID', 'pl_setting_id', 'plot_number_1'])

            valueDi = {}
            for row in cursor:
                 key = row[0]
                 vals = row[1:]
                 if key not in valueDi:
                      valueDi[key] = []
                      valueDi[key] = vals
                 else:
                      valueDi[key] = vals
            del(cursor)

            photonameDict = {}
            os.mkdir(outputLocation + '//FSVeg_Spatial_WT_Photos')
            with arcpy.da.SearchCursor(inTable, ['DATA', 'ATT_NAME', 'REL_GLOBALID']) as cursor:
              for item in cursor:
                if item[2] in valueDi:
                    attachment = item[0]
                    filenum = str(valueDi[item[2]][0]) + "_plot" + str(valueDi[item[2]][1])
                    attachmentName = str(item[1])
                    loc = attachmentName.find('photo_plot')
                    if attachmentName[loc + 10: loc +11] == '-':
                      filename = filenum  + "_1.jpg"
                    else:
                      filename = filenum  + '_' + attachmentName[loc + 11: loc +12] + '.jpg'
                    open(outputLocation + '//FSVeg_Spatial_WT_Photos' + os.sep + filename, 'wb').write(attachment.tobytes())
                    if item[2] not in photonameDict:
                      photonameDict[item[2]] = [filename]
                    else:
                      photonameDict[item[2]].append(filename)
                    del item
                    del filenum
                    del filename
                    del attachment
                else:
                    pass

            arcpy.AddField_management('FSVeg_Spatial_WT_Photos', 'PhotoNames', 'TEXT', '#', '#', 250)
            edit = arcpy.da.Editor(outputLocation + '/FSVeg_Spatial_WT.gdb') # dirname of the fc is the db name
            edit.startEditing(False, False) # check these setting for your environment
            edit.startOperation()
            cursor = arcpy.da.UpdateCursor('FSVeg_Spatial_WT_Photos', ['GlobalID', 'PhotoNames'])
            for row in cursor:
              if row[0] in photonameDict:
                row[1] = ','.join(photonameDict[row[0]])
              cursor.updateRow(row)
            edit.stopOperation()
            edit.stopEditing(True)
            arcpy.DeleteField_management('FSVeg_Spatial_WT_Photos', 'habitat_type_plot_1;ind_photo_2;ind_photo_3;ind_photo_4;tally_tree_note_1;species_1;abgr_dbh_cl;abgr_count_0_5;abgr_avg_ht_0_5_1;abgr_avg_age_0_5_1;abgr_count_5_10;abgr_avg_ht_5_10;abgr_avg_age_5_10;abgr_count_10_15;abgr_avg_ht_10_15;abgr_avg_age_10_15;abgr_count_15_20;abgr_avg_ht_15_20;abgr_avg_age_15_20;abgr_count_20_25;abgr_avg_ht_20_25;abgr_avg_age_20_25;abgr_count_25_p;abgr_avg_ht_25_p;abgr_avg_age_25_p;abgr_ave_dbh_25_p;d_abgr_count_0_5;d_abgr_sn_dec_0_5_1;d_abgr_count_5_10;d_abgr_sn_dec_5_10;d_abgr_count_10_15;d_abgr_sn_dec_10_15;d_abgr_count_15_20;d_abgr_sn_dec_15_20;d_abgr_count_20_25;d_abgr_sn_dec_20_25;d_abgr_count_25_p;d_abgr_sn_dec_25_p;d_abgr_ave_dbh_25_p;abla_dbh_cl;abla_count_0_5;abla_avg_ht_0_5_1;abla_avg_age_0_5_1;abla_count_5_10;abla_avg_ht_5_10;abla_avg_age_5_10;abla_count_10_15;abla_avg_ht_10_15;abla_avg_age_10_15;abla_count_15_20;abla_avg_ht_15_20;abla_avg_age_15_20;abla_count_20_25;abla_avg_ht_20_25;abla_avg_age_20_25;abla_count_25_p;abla_avg_ht_25_p;abla_avg_age_25_p;abla_ave_dbh_25_p;d_abla_count_0_5;d_abla_sn_dec_0_5_1;d_abla_count_5_10;d_abla_sn_dec_5_10;d_abla_count_10_15;d_abla_sn_dec_10_15;d_abla_count_15_20;d_abla_sn_dec_15_20;d_abla_count_20_25;d_abla_sn_dec_20_25;d_abla_count_25_p;d_abla_sn_dec_25_p;d_abla_ave_dbh_25_p;bepa_dbh_cl;bepa_count_0_5;bepa_avg_ht_0_5_1;bepa_avg_age_0_5_1;bepa_count_5_10;bepa_avg_ht_5_10;bepa_avg_age_5_10;bepa_count_10_15;bepa_avg_ht_10_15;bepa_avg_age_10_15;bepa_count_15_20;bepa_avg_ht_15_20;bepa_avg_age_15_20;bepa_count_20_25;bepa_avg_ht_20_25;bepa_avg_age_20_25;bepa_count_25_p;bepa_avg_ht_25_p;bepa_avg_age_25_p;bepa_ave_dbh_25_p;d_bepa_count_0_5;d_bepa_sn_dec_0_5_1;d_bepa_count_5_10;d_bepa_sn_dec_5_10;d_bepa_count_10_15;d_bepa_sn_dec_10_15;d_bepa_count_15_20;d_bepa_sn_dec_15_20;d_bepa_count_20_25;d_bepa_sn_dec_20_25;d_bepa_count_25_p;d_bepa_sn_dec_25_p;d_bepa_ave_dbh_25_p;laly_dbh_cl;laly_count_0_5;laly_avg_ht_0_5_1;laly_avg_age_0_5_1;laly_count_5_10;laly_avg_ht_5_10;laly_avg_age_5_10;laly_count_10_15;laly_avg_ht_10_15;laly_avg_age_10_15;laly_count_15_20;laly_avg_ht_15_20;laly_avg_age_15_20;laly_count_20_25;laly_avg_ht_20_25;laly_avg_age_20_25;laly_count_25_p;laly_avg_ht_25_p;laly_avg_age_25_p;laly_ave_dbh_25_p;d_laly_count_0_5;d_laly_sn_dec_0_5_1;d_laly_count_5_10;d_laly_sn_dec_5_10;d_laly_count_10_15;d_laly_sn_dec_10_15;d_laly_count_15_20;d_laly_sn_dec_15_20;d_laly_count_20_25;d_laly_sn_dec_20_25;d_laly_count_25_p;d_laly_sn_dec_25_p;d_laly_ave_dbh_25_p;laoc_dbh_cl;laoc_count_0_5;laoc_avg_ht_0_5_1;laoc_avg_age_0_5_1;laoc_count_5_10;laoc_avg_ht_5_10;laoc_avg_age_5_10;laoc_count_10_15;laoc_avg_ht_10_15;laoc_avg_age_10_15;laoc_count_15_20;laoc_avg_ht_15_20;laoc_avg_age_15_20;laoc_count_20_25;laoc_avg_ht_20_25;laoc_avg_age_20_25;laoc_count_25_p;laoc_avg_ht_25_p;laoc_avg_age_25_p;laoc_ave_dbh_25_p;d_laoc_count_0_5;d_laoc_sn_dec_0_5_1;d_laoc_count_5_10;d_laoc_sn_dec_5_10;d_laoc_count_10_15;d_laoc_sn_dec_10_15;d_laoc_count_15_20;d_laoc_sn_dec_15_20;d_laoc_count_20_25;d_laoc_sn_dec_20_25;d_laoc_count_25_p;d_laoc_sn_dec_25_p;d_laoc_ave_dbh_25_p;pial_dbh_cl;pial_count_0_5;pial_avg_ht_0_5_1;pial_avg_age_0_5_1;pial_count_5_10;pial_avg_ht_5_10;pial_avg_age_5_10;pial_count_10_15;pial_avg_ht_10_15;pial_avg_age_10_15;pial_count_15_20;pial_avg_ht_15_20;pial_avg_age_15_20;pial_count_20_25;pial_avg_ht_20_25;pial_avg_age_20_25;pial_count_25_p;pial_avg_ht_25_p;pial_avg_age_25_p;pial_ave_dbh_25_p;d_pial_count_0_5;d_pial_sn_dec_0_5_1;d_pial_count_5_10;d_pial_sn_dec_5_10;d_pial_count_10_15;d_pial_sn_dec_10_15;d_pial_count_15_20;d_pial_sn_dec_15_20;d_pial_count_20_25;d_pial_sn_dec_20_25;d_pial_count_25_p;d_pial_sn_dec_25_p;d_pial_ave_dbh_25_p;pico_dbh_cl;pico_count_0_5;pico_avg_ht_0_5_1;pico_avg_age_0_5_1;pico_count_5_10;pico_avg_ht_5_10;pico_avg_age_5_10;pico_count_10_15;pico_avg_ht_10_15;pico_avg_age_10_15;pico_count_15_20;pico_avg_ht_15_20;pico_avg_age_15_20;pico_count_20_25;pico_avg_ht_20_25;pico_avg_age_20_25;pico_count_25_p;pico_avg_ht_25_p;pico_avg_age_25_p;pico_ave_dbh_25_p;d_pico_count_0_5;d_pico_sn_dec_0_5_1;d_pico_count_5_10;d_pico_sn_dec_5_10;d_pico_count_10_15;d_pico_sn_dec_10_15;d_pico_count_15_20;d_pico_sn_dec_15_20;d_pico_count_20_25;d_pico_sn_dec_20_25;d_pico_count_25_p;d_pico_sn_dec_25_p;d_pico_ave_dbh_25_p;pien_dbh_cl;pien_count_0_5;pien_avg_ht_0_5_1;pien_avg_age_0_5_1;pien_count_5_10;pien_avg_ht_5_10;pien_avg_age_5_10;pien_count_10_15;pien_avg_ht_10_15;pien_avg_age_10_15;pien_count_15_20;pien_avg_ht_15_20;pien_avg_age_15_20;pien_count_20_25;pien_avg_ht_20_25;pien_avg_age_20_25;pien_count_25_p;pien_avg_ht_25_p;pien_avg_age_25_p;pien_ave_dbh_25_p;d_pien_count_0_5;d_pien_sn_dec_0_5_1;d_pien_count_5_10;d_pien_sn_dec_5_10;d_pien_count_10_15;d_pien_sn_dec_10_15;d_pien_count_15_20;d_pien_sn_dec_15_20;d_pien_count_20_25;d_pien_sn_dec_20_25;d_pien_count_25_p;d_pien_sn_dec_25_p;d_pien_ave_dbh_25_p;pifl2_dbh_cl;pifl2_count_0_5;pifl2_avg_ht_0_5_1;pifl2_avg_age_0_5_1;pifl2_count_5_10;pifl2_avg_ht_5_10;pifl2_avg_age_5_10;pifl2_count_10_15;pifl2_avg_ht_10_15;pifl2_avg_age_10_15;pifl2_count_15_20;pifl2_avg_ht_15_20;pifl2_avg_age_15_20;pifl2_count_20_25;pifl2_avg_ht_20_25;pifl2_avg_age_20_25;pifl2_count_25_p;pifl2_avg_ht_25_p;pifl2_avg_age_25_p;pifl2_ave_dbh_25_p;d_pifl2_count_0_5;d_pifl2_sn_dec_0_5_1;d_pifl2_count_5_10;d_pifl2_sn_dec_5_10;d_pifl2_count_10_15;d_pifl2_sn_dec_10_15;d_pifl2_count_15_20;d_pifl2_sn_dec_15_20;d_pifl2_count_20_25;d_pifl2_sn_dec_20_25;d_pifl2_count_25_p;d_pifl2_sn_dec_25_p;d_pifl2_ave_dbh_25_p;pimo3_dbh_cl;pimo3_count_0_5;pimo3_avg_ht_0_5_1;pimo3_avg_age_0_5_1;pimo3_count_5_10;pimo3_avg_ht_5_10;pimo3_avg_age_5_10;pimo3_count_10_15;pimo3_avg_ht_10_15;pimo3_avg_age_10_15;pimo3_count_15_20;pimo3_avg_ht_15_20;pimo3_avg_age_15_20;pimo3_count_20_25;pimo3_avg_ht_20_25;pimo3_avg_age_20_25;pimo3_count_25_p;pimo3_avg_ht_25_p;pimo3_avg_age_25_p;pimo3_ave_dbh_25_p;d_pimo3_count_0_5;d_pimo3_sn_dec_0_5_1;d_pimo3_count_5_10;d_pimo3_sn_dec_5_10;d_pimo3_count_10_15;d_pimo3_sn_dec_10_15;d_pimo3_count_15_20;d_pimo3_sn_dec_15_20;d_pimo3_count_20_25;d_pimo3_sn_dec_20_25;d_pimo3_count_25_p;d_pimo3_sn_dec_25_p;d_pimo3_ave_dbh_25_p;pipo_dbh_cl;pipo_count_0_5;pipo_avg_ht_0_5_1;pipo_avg_age_0_5_1;pipo_count_5_10;pipo_avg_ht_5_10;pipo_avg_age_5_10;pipo_count_10_15;pipo_avg_ht_10_15;pipo_avg_age_10_15;pipo_count_15_20;pipo_avg_ht_15_20;pipo_avg_age_15_20;pipo_count_20_25;pipo_avg_ht_20_25;pipo_avg_age_20_25;pipo_count_25_p;pipo_avg_ht_25_p;pipo_avg_age_25_p;pipo_ave_dbh_25_p;d_pipo_count_0_5;d_pipo_sn_dec_0_5_1;d_pipo_count_5_10;d_pipo_sn_dec_5_10;d_pipo_count_10_15;d_pipo_sn_dec_10_15;d_pipo_count_15_20;d_pipo_sn_dec_15_20;d_pipo_count_20_25;d_pipo_sn_dec_20_25;d_pipo_count_25_p;d_pipo_sn_dec_25_p;d_pipo_ave_dbh_25_p;poba2_dbh_cl;poba2_count_0_5;poba2_avg_ht_0_5_1;poba2_avg_age_0_5_1;poba2_count_5_10;poba2_avg_ht_5_10;poba2_avg_age_5_10;poba2_count_10_15;poba2_avg_ht_10_15;poba2_avg_age_10_15;poba2_count_15_20;poba2_avg_ht_15_20;poba2_avg_age_15_20;poba2_count_20_25;poba2_avg_ht_20_25;poba2_avg_age_20_25;poba2_count_25_p;poba2_avg_ht_25_p;poba2_avg_age_25_p;poba2_ave_dbh_25_p;d_poba2_count_0_5;d_poba2_sn_dec_0_5_1;d_poba2_count_5_10;d_poba2_sn_dec_5_10;d_poba2_count_10_15;d_poba2_sn_dec_10_15;d_poba2_count_15_20;d_poba2_sn_dec_15_20;d_poba2_count_20_25;d_poba2_sn_dec_20_25;d_poba2_count_25_p;d_poba2_sn_dec_25_p;d_poba2_ave_dbh_25_p;pobat_dbh_cl;pobat_count_0_5;pobat_avg_ht_0_5_1;pobat_avg_age_0_5_1;pobat_count_5_10;pobat_avg_ht_5_10;pobat_avg_age_5_10;pobat_count_10_15;pobat_avg_ht_10_15;pobat_avg_age_10_15;pobat_count_15_20;pobat_avg_ht_15_20;pobat_avg_age_15_20;pobat_count_20_25;pobat_avg_ht_20_25;pobat_avg_age_20_25;pobat_count_25_p;pobat_avg_ht_25_p;pobat_avg_age_25_p;pobat_ave_dbh_25_p;d_pobat_count_0_5;d_pobat_sn_dec_0_5_1;d_pobat_count_5_10;d_pobat_sn_dec_5_10;d_pobat_count_10_15;d_pobat_sn_dec_10_15;d_pobat_count_15_20;d_pobat_sn_dec_15_20;d_pobat_count_20_25;d_pobat_sn_dec_20_25;d_pobat_count_25_p;d_pobat_sn_dec_25_p;d_pobat_ave_dbh_25_p;potr5_dbh_cl;potr5_count_0_5;potr5_avg_ht_0_5_1;potr5_avg_age_0_5_1;potr5_count_5_10;potr5_avg_ht_5_10;potr5_avg_age_5_10;potr5_count_10_15;potr5_avg_ht_10_15;potr5_avg_age_10_15;potr5_count_15_20;potr5_avg_ht_15_20;potr5_avg_age_15_20;potr5_count_20_25;potr5_avg_ht_20_25;potr5_avg_age_20_25;potr5_count_25_p;potr5_avg_ht_25_p;potr5_avg_age_25_p;potr5_ave_dbh_25_p;d_potr5_count_0_5;d_potr5_sn_dec_0_5_1;d_potr5_count_5_10;d_potr5_sn_dec_5_10;d_potr5_count_10_15;d_potr5_sn_dec_10_15;d_potr5_count_15_20;d_potr5_sn_dec_15_20;d_potr5_count_20_25;d_potr5_sn_dec_20_25;d_potr5_count_25_p;d_potr5_sn_dec_25_p;d_potr5_ave_dbh_25_p;psme_dbh_cl;psme_count_0_5;psme_avg_ht_0_5_1;psme_avg_age_0_5_1;psme_count_5_10;psme_avg_ht_5_10;psme_avg_age_5_10;psme_count_10_15;psme_avg_ht_10_15;psme_avg_age_10_15;psme_count_15_20;psme_avg_ht_15_20;psme_avg_age_15_20;psme_count_20_25;psme_avg_ht_20_25;psme_avg_age_20_25;psme_count_25_p;psme_avg_ht_25_p;psme_avg_age_25_p;psme_ave_dbh_25_p;d_psme_count_0_5;d_psme_sn_dec_0_5_1;d_psme_count_5_10;d_psme_sn_dec_5_10;d_psme_count_10_15;d_psme_sn_dec_10_15;d_psme_count_15_20;d_psme_sn_dec_15_20;d_psme_count_20_25;d_psme_sn_dec_20_25;d_psme_count_25_p;d_psme_sn_dec_25_p;d_psme_ave_dbh_25_p;tabr2_dbh_cl;tabr2_count_0_5;tabr2_avg_ht_0_5_1;tabr2_avg_age_0_5_1;tabr2_count_5_10;tabr2_avg_ht_5_10;tabr2_avg_age_5_10;tabr2_count_10_15;tabr2_avg_ht_10_15;tabr2_avg_age_10_15;tabr2_count_15_20;tabr2_avg_ht_15_20;tabr2_avg_age_15_20;tabr2_count_20_25;tabr2_avg_ht_20_25;tabr2_avg_age_20_25;tabr2_count_25_p;tabr2_avg_ht_25_p;tabr2_avg_age_25_p;tabr2_ave_dbh_25_p;d_tabr2_count_0_5;d_tabr2_sn_dec_0_5_1;d_tabr2_count_5_10;d_tabr2_sn_dec_5_10;d_tabr2_count_10_15;d_tabr2_sn_dec_10_15;d_tabr2_count_15_20;d_tabr2_sn_dec_15_20;d_tabr2_count_20_25;d_tabr2_sn_dec_20_25;d_tabr2_count_25_p;d_tabr2_sn_dec_25_p;d_tabr2_ave_dbh_25_p;thpl_dbh_cl;thpl_count_0_5;thpl_avg_ht_0_5_1;thpl_avg_age_0_5_1;thpl_count_5_10;thpl_avg_ht_5_10;thpl_avg_age_5_10;thpl_count_10_15;thpl_avg_ht_10_15;thpl_avg_age_10_15;thpl_count_15_20;thpl_avg_ht_15_20;thpl_avg_age_15_20;thpl_count_20_25;thpl_avg_ht_20_25;thpl_avg_age_20_25;thpl_count_25_p;thpl_avg_ht_25_p;thpl_avg_age_25_p;thpl_ave_dbh_25_p;d_thpl_count_0_5;d_thpl_sn_dec_0_5_1;d_thpl_count_5_10;d_thpl_sn_dec_5_10;d_thpl_count_10_15;d_thpl_sn_dec_10_15;d_thpl_count_15_20;d_thpl_sn_dec_15_20;d_thpl_count_20_25;d_thpl_sn_dec_20_25;d_thpl_count_25_p;d_thpl_sn_dec_25_p;d_thpl_ave_dbh_25_p;tshe_dbh_cl;tshe_count_0_5;tshe_avg_ht_0_5_1;tshe_avg_age_0_5_1;tshe_count_5_10;tshe_avg_ht_5_10;tshe_avg_age_5_10;tshe_count_10_15;tshe_avg_ht_10_15;tshe_avg_age_10_15;tshe_count_15_20;tshe_avg_ht_15_20;tshe_avg_age_15_20;tshe_count_20_25;tshe_avg_ht_20_25;tshe_avg_age_20_25;tshe_count_25_p;tshe_avg_ht_25_p;tshe_avg_age_25_p;tshe_ave_dbh_25_p;d_tshe_count_0_5;d_tshe_sn_dec_0_5_1;d_tshe_count_5_10;d_tshe_sn_dec_5_10;d_tshe_count_10_15;d_tshe_sn_dec_10_15;d_tshe_count_15_20;d_tshe_sn_dec_15_20;d_tshe_count_20_25;d_tshe_sn_dec_20_25;d_tshe_count_25_p;d_tshe_sn_dec_25_p;d_tshe_ave_dbh_25_p;tsme_dbh_cl;tsme_count_0_5;tsme_avg_ht_0_5_1;tsme_avg_age_0_5_1;tsme_count_5_10;tsme_avg_ht_5_10;tsme_avg_age_5_10;tsme_count_10_15;tsme_avg_ht_10_15;tsme_avg_age_10_15;tsme_count_15_20;tsme_avg_ht_15_20;tsme_avg_age_15_20;tsme_count_20_25;tsme_avg_ht_20_25;tsme_avg_age_20_25;tsme_count_25_p;tsme_avg_ht_25_p;tsme_avg_age_25_p;tsme_ave_dbh_25_p;d_tsme_count_0_5;d_tsme_sn_dec_0_5_1;d_tsme_count_5_10;d_tsme_sn_dec_5_10;d_tsme_count_10_15;d_tsme_sn_dec_10_15;d_tsme_count_15_20;d_tsme_sn_dec_15_20;d_tsme_count_20_25;d_tsme_sn_dec_20_25;d_tsme_count_25_p;d_tsme_sn_dec_25_p;d_tsme_ave_dbh_25_p;snag_dbh_cl;snag_count_0_5;d_snag_dec_0_5;snag_count_5_10;d_snag_dec_5_10;snag_count_10_15;d_snag_dec_10_15;snag_count_15_20;d_snag_dec_15_20;snag_count_20_25;d_snag_dec_20_25;snag_count_25_p;d_snag_dec_25_p;snag_ave_dbh_25_p;three_six_10;seven_nine_10;ten_twelve_10;number_ten_twelve_10;thirteen_p_10;number_thirteen_p_10;soft_three_six_10;soft_seven_nine_10;soft_ten_twelve_10;number_s_ten_twelve_10;soft_thirteen_p_10;number_s_thirteen_p_10;remarks_plots;plotsgroupnote;parentglobalid;CreationDate;EditDate;Creator;Editor')
            arcpy.AlterField_management("FSVeg_Spatial_WT_Photos","pl_setting_id", "Setting_ID", "Setting_ID")
            arcpy.Delete_management(outFile)
