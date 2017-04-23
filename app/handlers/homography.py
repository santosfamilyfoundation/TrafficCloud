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

    @apiSuccess {Integer[]} homography The API will return an array containing the 3x3 matrix of homography points.

    @apiError error_message The error message to display.
    """

    def prepare(self):
        self.identifier = self.find_argument('identifier', str)
        self.project_exists(self.identifier)

        status_dict = StatusHelper.get_status(self.identifier)
        if status_dict[Status.Type.HOMOGRAPHY] == Status.Flag.IN_PROGRESS:
            status_code = 409
            self.error_message = "Currently uploading homography. Please wait."
            raise tornado.web.HTTPError(status_code = status_code)
        StatusHelper.set_status(self.identifier, Status.Type.HOMOGRAPHY, Status.Flag.IN_PROGRESS)

    def post(self):
        self.up_ratio = self.find_argument('unit_pixel_ratio', float)
        self.write_homography_files()
        StatusHelper.set_status(self.identifier, Status.Type.HOMOGRAPHY, Status.Flag.COMPLETE)
        self.finish()

    def get(self):
        h_path = os.path.join(\
                        get_project_path(self.identifier),\
                        'homography',\
                        'homography.txt')
        if not os.path.exists(h_path):
            self.error_message = "Homography file does not exist. Make sure that homography has been run successfully"
            raise tornado.web.HTTPError(status_code = 404)
        self.write({'homography': np.ndarray.tolist(np.loadtxt(h_path))})

        StatusHelper.set_status(\
                                self.identifier,\
                                Status.Type.HOMOGRAPHY,\
                                Status.Flag.COMPLETE)
        self.finish()

    def write_homography_files(self):
        project_dir = get_project_path(self.identifier)
        aerial_pts = self.find_argument('aerial_pts', list)
        camera_pts = self.find_argument('camera_pts', list)

        try:
            if isinstance(aerial_pts[0],basestring):
                aerial_pts = [[float(aerial_pts[i]),float(aerial_pts[i+1])] for i in xrange(0,len(aerial_pts), 2)]
            if isinstance(camera_pts[0],basestring):
                camera_pts = [[float(camera_pts[i]),float(camera_pts[i+1])] for i in xrange(0,len(camera_pts), 2)]
        except ValueError as v:
            self.error_message = "Could not interpret the points given as floats. Try again with different points"
            StatusHelper.set_status(\
                                    self.identifier,\
                                    Status.Type.HOMOGRAPHY,\
                                    Status.Flag.FAILURE,
                                    failure_message="Couldn't interpret uploaded points.")
            raise tornado.web.HTTPError(status_code = 400)
        except IndexError as i:
            self.error_message = "Malformed points. Try again with different points"
            StatusHelper.set_status(\
                            self.identifier,\
                            Status.Type.HOMOGRAPHY,\
                            Status.Flag.FAILURE,
                            failure_message="Couldn't interpret uploaded points.")
            raise tornado.web.HTTPError(status_code = 400)


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
            except Exception as e:
                self.error_message = "Could not find the homography, check your points and try again"
                StatusHelper.set_status(\
                                        self.identifier,\
                                        Status.Type.HOMOGRAPHY,\
                                        Status.Flag.FAILURE,
                                        failure_message='Failed to find homography: '+str(e))
                raise tornado.web.HTTPError(status_code = 400)

        else:
            self.error_message = "Could not interpret the points given. Try again with different points"
            StatusHelper.set_status(\
                                    self.identifier,\
                                    Status.Type.HOMOGRAPHY,\
                                    Status.Flag.FAILURE,
                                    failure_message="Couldn't interpret uploaded points.")
            raise tornado.web.HTTPError(status_code = 400)


    def check_points(self, points):
        for i in points:
            if not (isinstance(i, list) and len(i)==2):
                return False
            for j in i:
                if not isinstance(j, (int,float)):
                    return False
        return True
