import os
import unittest
import arcpy
import sys

sys.path.append(r'C:\Data\FSVeg_Sp_WT_AGOL_PhototDownload\NRGG')
from FSVegAGOLPhotoDownloadTools import areaOfInterestHandlingForSpatialFilteringAGOLFeatureService 
from FSVegAGOLPhotoDownloadTools import errorMessageGenerator
from FSVegAGOLPhotoDownloadTools import listStringJoiner

projectedVerticesList = [
    [-110.74940200956502, 46.89382592506291], 
    [-110.75298764360036, 46.89351164692039],
    [-110.75751611406332, 46.894125919153566], 
    [-110.75807324408873, 46.89928294590163],
    [-110.75418761696278, 46.9030542896121],
    [-110.74911630152633, 46.898754385980055],
    [-110.74940200956502, 46.89382592506291]
]


projectedVerticesDictionary = {
    'rings': [
        [
            [-110.74940200956502, 46.89382592506291],
            [-110.75298764360036, 46.89351164692039], 
            [-110.75751611406332, 46.894125919153566], 
            [-110.75807324408873, 46.89928294590163], 
            [-110.75418761696278, 46.9030542896121], 
            [-110.74911630152633, 46.898754385980055], 
            [-110.74940200956502, 46.89382592506291]
        ]
    ]
}

AOIFilePath = r'C:\Data\FSVeg_Sp_WT_AGOL_PhototDownload\tests\test_data.gdb\testAOI'
projectedTestAOIFilePath = r'C:\Data\FSVeg_Sp_WT_AGOL_PhototDownload\tests\test_data.gdb\projectedTestAOI'

AOI = areaOfInterestHandlingForSpatialFilteringAGOLFeatureService(AOIFilePath)


class TestFSVegPhotoDowloadTools(unittest.TestCase):

    def test_listStringJoiner(self):
        stringJoinedListFromFunction = listStringJoiner([1, 2, 3, 4])
        self.assertEqual(stringJoinedListFromFunction, '1,2,3,4')

    def test_errorMessageGenerator(self):
        testErrorMessage = 'There was an error test text.\n    If you believe there was an mistake \n    entering parameters please try the tool again.\n    This program will exit in ten seconds'
        errorMessageFromFunction = errorMessageGenerator('test text')
        self.assertEqual(testErrorMessage, errorMessageFromFunction)

    def test_getVerticesFromProjectedFeatureClassAreaofInterest(self):
        verticesList = AOI.getVerticesFromProjectedFeatureClassAreaofInterest(projectedTestAOIFilePath)
        self.assertEqual(projectedVerticesList,  verticesList)
    
    def test_makeAreaOfInterestDictionaryForURLEndPoint(self):
        verticesDictionary = AOI.makeAreaOfInterestDictionaryForURLEndPoint(projectedVerticesList)
        self.assertEqual(projectedVerticesDictionary, verticesDictionary)
    