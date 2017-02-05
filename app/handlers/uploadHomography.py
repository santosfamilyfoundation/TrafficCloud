#!/usr/bin/env python

import tornado.web
from tornado.escape import json_decode
import os
from traffic_cloud_utils.app_config import get_project_path
from traffic_cloud_utils.statusHelper import StatusHelper
import numpy as np
import cv2
from ast import literal_eval

class UploadHomographyHandler(tornado.web.RequestHandler):
    """
    @api {post} /uploadHomography/ Upload Homography
    @apiName UploadHomography
    @apiVersion 0.1.0
    @apiGroup Upload
    @apiDescription Use this route to upload homography files for a project.

    @apiParam {String} identifier The identifier of the project to upload files to.
    @apiParam {File} aerial An aerial photo of the intersection.
    @apiParam {File} camera A screenshot of the intersection from the video.
    @apiParam {Integer} unit_pixel_ratio The unit_pixel_ratio of the images (ie. 0.05 meters per pixel).
    @apiParam {JSON} aerial_pts A JSON array containing the coordinates of point clicks on the aerial image as arrays in the form [x_coord, y_coord]
    @apiParam {JSON} camera_pts A JSON array containing the coordinates of point clicks on the camera image as arrays in the form [x_coord, y_coord]

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """
    def initialize(self):
        self.identifier = None
        self.files = {}

    def post(self):
        self.files = self.request.files
        self.identifier = self.get_body_argument('identifier')
        self.up_ratio = float(self.get_body_argument('unit_pixel_ratio'))
        StatusHelper.set_status(self.identifier, "upload_homography", 1)
        self.write_homography_files()
        StatusHelper.set_status(self.identifier, "upload_homography", 2)
        self.finish("Upload Homography")
        
    def write_homography_files(self):
        project_dir = get_project_path(self.identifier)
        aerial_pts = self.get_body_argument('aerial_pts')
        camera_pts = self.get_body_argument('camera_pts')
        homography, mask = cv2.findHomography(\
                            np.array(literal_eval(camera_pts)),\
                            self.up_ratio*np.array(literal_eval(aerial_pts)))
        np.savetxt(os.path.join(project_dir,'homography','homography.txt'),homography)
        #TO-DO Write the unit_pixel_ratio to some config file
        for key,value in self.files.iteritems():
            if (key == 'aerial' or key == 'camera'):
                with open(os.path.join(project_dir,'homography',value[0]['filename']), 'wb') as f:
                    f.write(value[0]['body'])
        
        


