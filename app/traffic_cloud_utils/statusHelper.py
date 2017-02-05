
import os

from app_config import get_project_config_path, update_config_with_sections, get_config_section

class Status(object):
    class StatusType:
        UPLOAD_HOMOGRAPHY = "upload_homography"
        CONFIGURATION_TEST = "configuration_test"
        OBJECT_TRACKING = "object_tracking"
        SAFETY_ANALYSIS = "safety_analysis"
        HIGHLIGHT_VIDEO = "highlight_video"

    class Status:
        FAILURE = -1
        INCOMPLETE = 0
        IN_PROGRESS = 1
        COMPLETE = 2

    @staticmethod
    def create_status_dict():
        return {
            Status.StatusType.UPLOAD_HOMOGRAPHY: 0,
            Status.StatusType.CONFIGURATION_TEST: 0,
            Status.StatusType.OBJECT_TRACKING: 0,
            Status.StatusType.SAFETY_ANALYSIS: 0,
            Status.StatusType.HIGHLIGHT_VIDEO: 0,
        }

class StatusHelper(object):
    @staticmethod
    def initalize_project(identifier):
        d = Status.create_status_dict()
        config_path = get_project_config_path(identifier)
        for (status_type, status) in d.iteritems():
            update_config_with_sections(config_path, "status", status_type, str(status))

    @staticmethod
    def set_status(identifier, status_type, val):
        config_path = get_project_config_path(identifier)
        status = str(val)
        update_config_with_sections(config_path, "status", status_type, status)

    @staticmethod
    def get_status(identifier):
        config_path = get_project_config_path(identifier)
        (success, value) = get_config_section(config_path, "status")
        if success:
            return value
        else:
            return None


