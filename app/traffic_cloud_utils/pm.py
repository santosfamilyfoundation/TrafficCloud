"""
Project management classes and functions
"""

import os
from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError
import time
import datetime
from shutil import copy
try:
    from PIL import Image
except:
    import Image
import cvutils
import numpy as np
import subprocess
import uuid

from app_config import get_project_path, get_project_config_path, config_section_exists, update_config_without_sections
from video import get_framerate
from statusHelper import StatusHelper

def create_project(identifier, video_dict):
    config_dict = {}

    _update_config_dict_with_defaults(config_dict)
    _translate_config_dict(config_dict)
    _create_project_dir(identifier, config_dict, video_dict)
    StatusHelper.initalize_project(identifier) # This must be called after the config path has been created

def update_homography(identifier, homography_path, unitpixelratio):
    pass

def update_project_config(identifier, config_dict):
    _update_config_dict_with_defaults(config_dict)
    _translate_config_dict(config_dict) 

    project_path = get_project_path(identifier)
    tracking_path = os.path.join(project_path, "tracking.cfg")
    update_config_without_sections(tracking_path, config_dict)

def default_config_dict():
    return {
        'max_features_per_frame': 1000,
        'num_displacement_frames': 10,
        'min_feature_displacement': 0.0001,
        'max_iterations_to_persist': 200,
        'min_feature_frames': 15,
        'max_connection_distance': 1.0,
        'max_segmentation_distance': 0.7,
    }
def _translate_config_dict(config_dict):
    translate_dict = \
    {   'max_features_per_frame': "max-nfeatures",
        'num_displacement_frames': "ndisplacements",
        'min_feature_displacement': "min-feature-displacement",
        'max_iterations_to_persist': "max-number-iterations",
        'min_feature_frames': "min-feature-time",
        'max_connection_distance': "mm-connection-distance",
        'max_segmentation_distance': "mm-segmentation-distance"}

    for (key, val) in config_dict.iteritems():
        if key in translate_dict:
            config_dict[translate_dict[key]] = val
            del config_dict[key]
        
def _update_config_dict_with_defaults(config_dict):
    default_dict = default_config_dict()

    # Remove things that we don't want the user to be able to configure
    for key in config_dict.keys():
        if key not in default_dict.keys():
            del config_dict[key]

    # Add defaults for things that don't exist
    for (key, value) in default_dict.iteritems():
        if key not in config_dict.keys():
            config_dict[key] = value

def _create_project_dir(identifier, config_dict, video_dict):
    test_object_dir = os.path.join(".temp", "test", "test_object")
    test_feature_dir = os.path.join(".temp", "test", "test_feature")

    directory_names = ["homography", test_object_dir, test_feature_dir, "run", "results"]
    project_path = get_project_path(identifier)

    if not os.path.exists(project_path):
        # Create proj dirs
        for new_dir in directory_names:
            os.makedirs(os.path.join(project_path, new_dir))

        with open(os.path.join(project_path,video_dict['filename']), 'wb') as v:
            v.write(video_dict['body'])

        # TODO: unitpixelratio
        _write_to_project_config(identifier, video_dict['filename'])

        default_files_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "default")

        tracking_path = os.path.join(project_path, "tracking.cfg")
        classifier_path = os.path.join(project_path, "classifier.cfg")

        copy(os.path.join(default_files_dir, "tracking.cfg"), tracking_path)
        copy(os.path.join(default_files_dir, "classifier.cfg"), classifier_path)

        # Add classifier path along with configuration
        config_dict['classifier-filename'] = classifier_path
        update_config_without_sections(tracking_path, config_dict)

        update_dict = {
            'pbv-svm-filename': os.path.join(default_files_dir, 'modelPBV.xml'),
            'bv-svm-filename': os.path.join(default_files_dir, 'modelBV.xml')
        }
        update_config_without_sections(classifier_path, update_dict)
        update_config_without_sections(tracking_path,update_dict)
    else:
        print("Project exists. No new project created.")
                
def _write_to_project_config(identifier, video_filename, unitpixelratio='0.05'):
    ts = time.time()
    vid_ts = datetime.datetime.now()
    #This line needs to be updated to no longer need the ui class. Load video and pull time.
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y %H:%M:%S %Z')
    video_timestamp = vid_ts.strftime('%d-%m-%Y %H:%M:%S %Z')
    config_parser = SafeConfigParser()
    config_parser.add_section("info")
    config_parser.set("info", "project_name", identifier)
    config_parser.set("info", "creation_date", timestamp)
    config_parser.add_section("video")
    config_parser.set("video", "name", video_filename)
    config_parser.set("video", "source", video_filename)
    config_parser.set("video", "framerate", get_framerate(os.path.join(get_project_path(identifier), video_filename)))
    config_parser.set("video", "start", video_timestamp)
    if unitpixelratio:
        config_parser.add_section("homography")
        config_parser.set("homography", "unitpixelratio", unitpixelratio)

    with open(get_project_config_path(identifier), 'wb') as configfile:
        config_parser.write(configfile)
