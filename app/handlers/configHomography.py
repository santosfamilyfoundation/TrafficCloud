#!/usr/bin/env python

import tornado.web
import os
from traffic_cloud_utils.app_config import get_project_path
from traffic_cloud_utils.statusHelper import StatusHelper, Status
import numpy as np
import cv2
from ast import literal_eval
from baseHandler import BaseHandler

class ConfigHomographyHandler(BaseHandler):
    """
    @api {post} /configHomography/ Config Homography
    @apiName ConfigHomography
    @apiVersion 0.2.0
    @apiGroup Configuration
    @apiDescription Use this route to upload homography data for a project.

    @apiParam {String} identifier The identifier of the project for which to configure the homography.
    @apiParam {Integer} unit_pixel_ratio The unit_pixel_ratio of the images (ie. 0.05 meters per pixel).
    @apiParam {JSON Array} aerial_pts A JSON array containing the coordinates of point clicks on the aerial image as arrays in the form [x_coord, y_coord]
    @apiParam {JSON Array} camera_pts A JSON array containing the coordinates of point clicks on the camera image as arrays in the form [x_coord, y_coord]

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """

    def prepare(self):
        self.identifier = self.get_body_argument("identifier")
        if StatusHelper.get_status(identifier)[Status.Type.CONFIG_HOMOGRAPHY] == Status.Flag.IN_PROGRESS:
            status_code = 423
            self.error_message = "Currently uploading homography. Please wait."
            raise tornado.web.HTTPError(status_code = status_code)
        StatusHelper.set_status(identifier, Status.Type.CONFIG_HOMOGRAPHY, Status.Flag.IN_PROGRESS)

    def post(self):
        self.up_ratio = float(self.get_body_argument('unit_pixel_ratio'))
        self.write_homography_files()
        StatusHelper.set_status(self.identifier, Status.Type.CONFIG_HOMOGRAPHY, Status.Flag.COMPLETE)
        self.finish("Upload Homography")

    def write_homography_files(self):
        project_dir = get_project_path(self.identifier)
        #TODO: Put literal_eval here and use try/catch
        aerial_pts = self.get_body_argument('aerial_pts')
        camera_pts = self.get_body_argument('camera_pts')

        homography, mask = cv2.findHomography(\
                            np.array(literal_eval(camera_pts)),\
                            self.up_ratio*np.array(literal_eval(aerial_pts)))
        np.savetxt(os.path.join(project_dir,'homography','homography.txt'),homography)
