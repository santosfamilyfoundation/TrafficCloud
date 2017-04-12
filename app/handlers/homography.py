#!/usr/bin/env python

import tornado.web
import os
from traffic_cloud_utils.app_config import get_project_path
from traffic_cloud_utils.statusHelper import StatusHelper, Status
import numpy as np
import cv2
from ast import literal_eval
from baseHandler import BaseHandler

class HomographyHandler(BaseHandler):
    """
    @api {post} /homography/ Post Homography
    @apiName PostHomography
    @apiVersion 0.2.0
    @apiGroup Configuration
    @apiDescription Use this route to upload homography data for a project.

    @apiParam {String} identifier The identifier of the project for which to configure the homography.
    @apiParam {Integer} unit_pixel_ratio The unit_pixel_ratio of the images (ie. 0.05 meters per pixel).
    @apiParam {JSON} aerial_pts A JSON array containing the coordinates of point clicks on the aerial image as arrays in the form [x_coord, y_coord], where x_coord and y_coord are floats
    @apiParam {JSON} camera_pts A JSON array containing the coordinates of point clicks on the camera image as arrays in the form [x_coord, y_coord], where x_coord and y_coord are floats

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """
    
    """
    @api {get} /homography/ Get Homography
    @apiName GetHomography
    @apiVersion 0.1.0
    @apiGroup Configuration
    @apiDescription Use this route to get the homography calculated during configuration.
    @apiParam {String} identifier The identifier of the project for which to configure the homography.
    
    @apiSuccess {Integer[][]} The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """

    def prepare(self):
        self.identifier = self.find_argument('identifier')

        #TODO: Make sure that the project actually exists, ie. project_exists(id)

        #Handle the status correctly
        if StatusHelper.get_status(self.identifier)[Status.Type.HOMOGRAPHY] == Status.Flag.IN_PROGRESS:
            status_code = 423
            self.error_message = "Currently uploading homography. Please wait."
            raise tornado.web.HTTPError(status_code = status_code)
        StatusHelper.set_status(self.identifier, Status.Type.HOMOGRAPHY, Status.Flag.IN_PROGRESS)

    def post(self):
        self.up_ratio = float(self.find_argument('unit_pixel_ratio'))
        self.write_homography_files()
        StatusHelper.set_status(self.identifier, Status.Type.HOMOGRAPHY, Status.Flag.COMPLETE)
        self.finish()

    def get(self):
        h_path = os.path.join(\
                        get_project_path(self.identifier),\
                        'homography',\
                        'homography.txt')
        self.write({'homography': np.ndarray.tolist(np.loadtxt(h_path))})

        StatusHelper.set_status(\
                                self.identifier,\
                                Status.Type.HOMOGRAPHY,\
                                Status.Flag.COMPLETE)
        self.finish()

    def write_homography_files(self):
        project_dir = get_project_path(self.identifier)
        aerial_pts = literal_eval(self.find_argument('aerial_pts'))
        camera_pts = literal_eval(self.find_argument('camera_pts'))

        if  ((aerial_pts is not None) and (camera_pts is not None)) and\
            (isinstance(aerial_pts, list) and isinstance(camera_pts, list)) and\
            (len(aerial_pts) == len(camera_pts)) and\
            (self.check_points(aerial_pts) and self.check_points(camera_pts)) and\
            (len(aerial_pts) >= 4):

            try:
                homography, mask = cv2.findHomography(\
                            np.array(camera_pts),\
                            self.up_ratio*np.array(aerial_pts))
                np.savetxt(\
                    os.path.join(project_dir,'homography','homography.txt'),\
                    homography)
            except:
                self.error_messag = "Could not find the homography, check your points and try again"
                StatusHelper.set_status(\
                                        self.identifier,\
                                        Status.Type.HOMOGRAPHY,\
                                        Status.Flag.FAILURE)
                raise tornado.web.HTTPError(status_code = 500)

        else:
            self.error_message = "Could not interpret the points given. Try again with different points"
            StatusHelper.set_status(\
                                    self.identifier,\
                                    Status.Type.HOMOGRAPHY,\
                                    Status.Flag.FAILURE)
            raise tornado.web.HTTPError(status_code = 500)


    def check_points(self, points):
        for i in points:
            if not (isinstance(i, list) and len(i)==2):
                return False
            for j in i:
                if not isinstance(j, float):
                    return False
        return True
