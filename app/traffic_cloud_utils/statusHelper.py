
import os

from enum import Enum

from app_config import get_project_config_path, update_config_with_sections, get_config_section, get_all_projects

class Status(object):

    class Flag(Enum):
        FAILURE = -1
        INCOMPLETE = 0
        IN_PROGRESS = 1
        COMPLETE = 2

    class Type(Enum):
        HOMOGRAPHY = "homography"
        FEATURE_TEST = "feature_test"
        OBJECT_TEST = "object_test"
        OBJECT_TRACKING = "object_tracking"
        SAFETY_ANALYSIS = "safety_analysis"
        HIGHLIGHT_VIDEO = "highlight_video"


    @classmethod
    def create_status_dict(cls):
        return {
            Status.Type.HOMOGRAPHY: Status.Flag.INCOMPLETE,
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
        # Prevent 'Section failure_message does not exist' errors
        update_config_with_sections(config_path, "failure_message", "None", "None")

    @staticmethod
    def set_status(identifier, status_type, val, failure_message=None):
        config_path = get_project_config_path(identifier)
        status = str(val.value)
        update_config_with_sections(config_path, "status", status_type.value, status)

        if failure_message is not None:
            update_config_with_sections(config_path, "failure_message", status_type.value, failure_message)

    @staticmethod
    def get_status(identifier):
        config_path = get_project_config_path(identifier)
        (success, value) = get_config_section(config_path, "status")
        if success:
            d = {}
            for (k,v) in value.iteritems():
                try:
                    d[Status.Type(k)] = Status.Flag(int(v))
                except Exception as e:
                    print('Failed to parse status: '+k+' with error: '+str(e))
            return d
        else:
            return None

    @staticmethod
    def get_status_raw(identifier):
        config_path = get_project_config_path(identifier)
        (success, statuses) = get_config_section(config_path, "status")
        if success:
            s, messages = get_config_section(config_path, "failure_message")
            d = {}
            for (k,v) in statuses.iteritems():
                d[k] = { 'status': v }
                if s and k in messages and int(v) == Status.Flag.FAILURE.value:
                    d[k]['failure_message'] = messages[k]
                elif v == Status.Flag.FAILURE.value:
                    d[k]['failure_message'] = "Operation failed: "+k
            return d
        else:
            return None

    @staticmethod
    def mark_all_failed():
        identifiers = get_all_projects()
        for identifier in identifiers:
            status = StatusHelper.get_status(identifier)
            if status:
                for (k, v) in status.iteritems():
                    if v == Status.Flag.IN_PROGRESS:
                        StatusHelper.set_status(identifier, k, Status.Flag.FAILURE, failure_message='Failed when server died')
            else:
                print "Error: Could not mark project status failure flags for project {}".format(identifier)




