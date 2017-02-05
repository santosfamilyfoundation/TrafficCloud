"""test_video.py"""
import os
from video import create_highlight_video
from storage import alterInteractionsWithRoadUserType, getNearMissFrames

def test_create_highlight_video(dbpath, projectpath, videoname):
	"""
	dbpath: the database should already have interactions and ttc indicators computed
		from running trafficintelligence/scripts/safety-analysis.py
	projectpath: i.e. '/home/user/Documents/SantosCloud/project_dir/{uuid}'
	videoname: source video name, i.e. 'video.avi'
	
	If no errors occur, check the generated highlight video in {projectpath}/final_videos
	"""
	# Uncomment line if interactions table does not have road user type columns
	# alterInteractionsWithRoadUserType(dbpath)
	
	near_misses = getNearMissFrames(dbpath, 60, True)
	print near_misses
	create_highlight_video(projectpath, os.path.join(projectpath, videoname), near_misses)
