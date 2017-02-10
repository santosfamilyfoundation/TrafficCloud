
import os

from enum import Enum

from app_config import get_project_config_path, update_config_with_sections, get_config_section

class Status(object):
        
    class Flag(Enum):
        FAILURE = -1
        INCOMPLETE = 0
        IN_PROGRESS = 1
        COMPLETE = 2

    class Type(Enum):
        CONFIG_HOMOGRAPHY = "config_homography"
        FEATURE_TEST = "feature_test"
        OBJECT_TEST = "object_test"
        OBJECT_TRACKING = "object_tracking"
        SAFETY_ANALYSIS = "safety_analysis"
        HIGHLIGHT_VIDEO = "highlight_video"


    @classmethod
    def create_status_dict(cls):
        return {
            Status.Type.CONFIG_HOMOGRAPHY: Status.Flag.INCOMPLETE,
            Status.Type.FEATURE_TEST: Status.Flag.INCOMPLETE,
            Status.Type.OBJECT_TEST: Status.Flag.INCOMPLETE,
            Status.Type.OBJECT_TRACKING: Status.Flag.INCOMPLETE,
            Status.Type.SAFETY_ANALYSIS: Status.Flag.INCOMPLETE,
            Status.Type.HIGHLIGHT_VIDEO: Status.Flag.INCOMPLETE,
        }

class StatusHelper(object):
    @staticmethod
    def initalize_project(identifier):
        d = Status.create_status_dict()
        config_path = get_project_config_path(identifier)
        for (status_type, status) in d.iteritems():
            update_config_with_sections(config_path, "status", status_type.value, str(status.value))

    @staticmethod
    def set_status(identifier, status_type, val):
        config_path = get_project_config_path(identifier)
        status = str(val.value)
        update_config_with_sections(config_path, "status", status_type.value, status)

    @staticmethod
    def get_status(identifier):
        config_path = get_project_config_path(identifier)
        (success, value) = get_config_section(config_path, "status")
        if success:
            return {Status.Type(k):Status.Flag(int(v)) for (k,v) in value.iteritems()}
        else:
            return None


