#!/usr/bin/env python

import tornado.web
import os
import uuid

class UploadHandler(tornado.web.RequestHandler):
    
    @staticmethod
    def parse_request(files):
        name_body_dict = {}
        for k, v in files.iteritems():
            fileinfo = v[0]
            name_body_dict[k] = fileinfo['body']
        return name_body_dict

    """
    @api {post} /upload/ Upload Files
    @apiName UploadFiles
    @apiVersion 0.1.0
    @apiGroup Upload
    @apiDescription This route will upload files to a project (and create a new project if an old one is not specified). You may provide a project identifier if you would like to update the files from an old project. If you provide a project identifier for an old project, all of the parameters are optional. If you are creating a new project, all parameters are required. This route will always return a dictionary containing the project identifier.

    @apiParam {String} email The email to notify when analysis is done.
    @apiParam {String} [identifier] The identifier of the project to update the file of. If no identifier is provided, a new project will be created, and the identifier will be returned in the response.
    @apiParam {File} homography/aerialpng An aerial photo of the intersection.
    @apiParam {File} homography/camerapng A screenshot of the intersection from the video.
    @apiParam {File} homography/homographytxt The homography text file to use.
    @apiParam {File} project_namecfg The project name configuration file.
    @apiParam {File} trackingcfg The tracking configuration file.
    @apiParam {File} temp/test/test_object/object_trackingcfg The object tracking configuration file.
    @apiParam {File} temp/test/test_feature/feature_trackingcfg The feature tracking configuration file.
    @apiParam {File} video The video file to analyze. This can have any file extension.

    @apiSuccess {String} project_identifier The project identifier. This will be used to reference the project in all other requests.

    @apiError error_message The error message to display.
    """
    def post(self):
        # TODO: Check for an existing project, and update only the existing files if so.
        name_body_dict = self.parse_request(self.request.files)
        # TODO: Save email
        project_identifier = api.saveFiles(name_body_dict)

        d = {'project_identifier': project_identifier}
        self.write(d)

    def get(self):
        self.render("upload.html")
