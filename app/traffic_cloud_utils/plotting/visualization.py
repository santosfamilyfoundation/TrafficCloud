#! /usr/bin/env python
# import storage
import sqlite3
import math
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import random
from thinkstats2 import Cdf
import thinkplot

from numpy.linalg.linalg import inv
from numpy import loadtxt

from moving import Point

from scipy.misc import imread

import matplotlib.patches as mpatches

# 2.23694 mph / (m/s) = (1 mi / 1609.34 m) * (3600 sec / 1 hr)
MPS_MPH_CONVERSION = 2.23694

"""
Test this file with: python visualization.py stmarc.sqlite 30 homography.txt
In the video_tracking/stmarc/stmarc-vis folder.
"""



def road_user_traj(fig, filename, fps, homographyFile, roadImageFile):
    """
    Plots all road-user trajectories.
    """

    homography = inv(loadtxt(homographyFile))

    # print(homography)

    connection = sqlite3.connect(filename)
    cursor = connection.cursor()

    queryStatement = 'SELECT * FROM objects ORDER BY object_id'
    cursor.execute(queryStatement)

    usertypes = []
    for row in cursor:
        usertypes.append(row[1])

    queryStatement = 'SELECT * FROM object_trajectories ORDER BY object_id, frame'
    cursor.execute(queryStatement)

    obj_id = 0
    obj_traj_x = []
    obj_traj_y = []

    # aplot = QTPLT()
    ax = fig.add_subplot(111)
    im = imread(roadImageFile)
    implot = ax.imshow(im)

    # colors = [(0,0,0), (0,0,1), (0,1,0), (1,0,1), (0,1,1), (1,1,0), (1,0,1)]
    userlist = ['unknown', 'car', 'pedestrian',
                'motorcycle', 'bicycle', 'bus', 'truck']
    colors = {'unknown': (0, 0, 0), 'car': (0, 0, 1), 'pedestrian': (0, 1, 0), 'motorcycle': (
        1, 0, 0), 'bicycle': (0, 1, 1), 'bus': (1, 1, 0), 'truck': (1, 0, 1)}

    for row in cursor:
        pos = Point(row[2], row[3])
        # xpos = row[2]
        # ypos = row[3]

        # usertype = usertypes[obj_id]

        # print pos.x, pos.y
        pos = pos.project(homography)
        # print pos.x, pos.y
        obj_traj_x.append(pos.x)
        obj_traj_y.append(pos.y)
        # print(obj_traj)

        if(row[0] != obj_id):
            # color = random.choice(colors)
            usertype = userlist[usertypes[obj_id]]

            ax.plot(obj_traj_x[:-1], obj_traj_y[:-1], ".-",
                    color=colors[usertype], label=usertype, linewidth=2, markersize=3)

            # print 'switching object to: ', row[0]
            obj_id = row[0]
            obj_traj_x = []
            obj_traj_y = []

    # Now add the legend with some customizations.

    # plot_handles = []
    # for user in userlist:
    #     handle = mpatches.Patch(color=colors[user], label=user)
    #     plt.legend(handles=handle, loc='upper right', shadow=True)

    colorlist = []
    recs = []
    for i in range(0, len(userlist)):
        colorlist.append(colors[userlist[i]])
        recs.append(mpatches.Rectangle((0, 0), 1, 1, fc=colorlist[i]))
    ax.set_position([0.1, 0.1, 0.85, 0.85])
    # ax.legend(recs,userlist, loc='center left', bbox_to_anchor=(1, 0.5))
    ax.legend(recs, userlist, loc=8, mode="expand",
              bbox_to_anchor=(-.5, -.5, .1, .1))

    box = ax.get_position()
    ax.set_position(
        [box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

    # Put a legend below current axis
    ax.legend(recs, userlist, loc='upper center', bbox_to_anchor=(
        0.5, -0.05), fancybox=True, shadow=True, ncol=4)
    # ax.legend(recs, userlist, bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=2, mode="expand", borderaxespad=0.)

    # legend = plt.legend(loc='upper right', shadow=True)

    ax.set_xlim([0, 1280])
    ax.set_ylim([0, 720])
    ax.set_ylim(ax.get_ylim()[::-1])

    # ax.set_xlabel('X-Coordinate')
    # ax.set_ylabel('Y-Coordinate')
    ax.set_title('Road User Trajectories')

    # plt.show()

    connection.commit()
    connection.close()

    # return aplot


def road_user_vels(fig, filename, fps):
    """
    Creates a histogram of road-user velocities, segregated by road user type.
    """
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()

    queryStatement = 'SELECT * FROM objects ORDER BY object_id'
    cursor.execute(queryStatement)

    usertypes = []
    for row in cursor:
        usertypes.append(row[1])

    queryStatement = 'SELECT * FROM object_trajectories ORDER BY object_id, frame'
    cursor.execute(queryStatement)

    obj_id = 0
    obj_vels = []

    xvels = []
    yvels = []

    userlist = ['unknown', 'car', 'pedestrian',
                'motorcycle', 'bicycle', 'bus', 'truck']
    roadusers = {'unknown': [], 'car': [], 'pedestrian': [],
                 'motorcycle': [], 'bicycle': [], 'bus': [], 'truck': []}

    for row in cursor:
        xvel = row[4]
        yvel = row[5]
        usertype = usertypes[obj_id]

        xvels.append(xvel * fps * MPS_MPH_CONVERSION)
        yvels.append(yvel * fps * MPS_MPH_CONVERSION)

        if(row[0] != obj_id):
            xvels = [abs(x) for x in xvels]
            yvels = [abs(y) for y in yvels]

            avg_xv = sum(xvels) / len(xvels)
            avg_yv = sum(yvels) / len(yvels)

            avg_vel = math.sqrt(avg_xv**2 + avg_yv**2)
            obj_vels.append(avg_vel)

            roadusers[userlist[usertype]].append(avg_vel)
            # print 'setting new avg velocity: ', avg_vel

            # print 'switching object to: ', row[0]
            obj_id = row[0]
            xvels = []
            yvels = []

    print roadusers

    index = np.arange(len(userlist))  # the x locations for the groups
    width = 0.1       # the width of the bars
    bins = np.linspace(0, 40, 20)

    # fig = plt.figure()
    ax = fig.add_subplot(111)

    colors = [(0, 0, 0), (0, 0, 1), (0, 1, 0), (1, 0, 0),
              (1, 0, 1), (0, 1, 1), (1, 1, 0), (1, 1, 1)]
    for user in userlist:
        if roadusers[user]:
            color = random.choice(colors)
            colors.remove(color)
            ax.hist(roadusers[user], bins, color=color,
                    alpha=.6, label=user, linewidth=2)

    # Now add the legend with some customizations.
    legend = ax.legend(loc='upper right', shadow=True)

    plt.xlabel('Velocity (mph)')
    plt.ylabel('Road Users')
    plt.title('Road User Velocity By Category')

    connection.commit()
    connection.close()


def vel_histograms(fig, filename, fps, vistype='overall'):
    """
    Obtains trajectory (position and velocity data) from object-trajectory table)
    Creates visualizations.
    """
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()

    queryStatement = 'SELECT * FROM object_trajectories ORDER BY object_id, frame'
    cursor.execute(queryStatement)

    obj_id = 0
    obj_vels = []

    xvels = []
    yvels = []
    for row in cursor:
        xvel = row[4]
        yvel = row[5]

        xvels.append(xvel * fps * MPS_MPH_CONVERSION)
        yvels.append(yvel * fps * MPS_MPH_CONVERSION)

        if(row[0] != obj_id):
            xvels = [abs(x) for x in xvels]
            yvels = [abs(y) for y in yvels]

            speeds = [math.sqrt(vels[0]**2 + vels[1]**2)
                      for vels in zip(xvels, yvels)]

            # Individual road user velocity histograms
            if(vistype == 'indiv'):
                fig = plt.figure()
                ax = fig.add_subplot(111)
                ax.hist(speeds, 25, facecolor='green', alpha=0.75)

                plt.xlabel('Velocity (mph)')
                plt.ylabel('Measurements')
                plt.title('Road User {}'.format(obj_id))
                plt.show()

            avg_xv = sum(xvels) / len(xvels)
            avg_yv = sum(yvels) / len(yvels)

            avg_vel = math.sqrt(avg_xv**2 + avg_yv**2)
            obj_vels.append(avg_vel)
            # print 'setting new avg velocity: ', avg_vel

            obj_id = row[0]
            xvels = []
            yvels = []

    # Histogram of all road user average velocities
    if(vistype == 'overall'):
        # fig = plt.figure()
        ax = fig.add_subplot(111)

        ax.hist(obj_vels, 25, normed=1, facecolor='green', alpha=0.75)

        plt.xlabel('Velocity (mph)')
        plt.ylabel('Road Users')
        plt.title('All Road User Velocities')

    connection.commit()
    connection.close()

def vel_cdf(filename, fps, speed_limit=25, dir=None, only_vehicle=True):
    """
    Arguments
    ---------
    filename: str, path to database
    fps: frame rate of the video, in frames per second
    speed_limit: speed limit of the intersection
    dir: directory to save image, if None don't automatically save
    only_vehicle: only show velocities of vehicles, default True
    """
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()

    if only_vehicle:
        queryStatement = '''SELECT object_trajectories.object_id AS object_id, frame, x, y, x_v, y_v
            FROM object_trajectories INNER JOIN objects ON object_trajectories.object_id = objects.object_id
            WHERE road_user_type = 1
            ORDER BY object_id, frame'''
    else:
        queryStatement = 'SELECT object_id, frame, x, y, x_v, y_v FROM object_trajectories ORDER BY object_id, frame'
    cursor.execute(queryStatement)

    obj_id = 0;
    obj_vels = [];

    xvels = []
    yvels = []
    for row in cursor:
        xvel = row[4]
        yvel = row[5]
        
        xvels.append(xvel*fps*MPS_MPH_CONVERSION)
        yvels.append(yvel*fps*MPS_MPH_CONVERSION)

        # reading new object
        if(row[0] != obj_id):
            # save velocity information for old object before moving onward
            xvels = [abs(x) for x in xvels]
            yvels = [abs(y) for y in yvels]

            speeds = [math.sqrt(vels[0]**2 + vels[1]**2) for vels in zip(xvels, yvels)]

            avg_xv = sum(xvels)/len(xvels)
            avg_yv = sum(yvels)/len(yvels)

            avg_vel = math.sqrt(avg_xv**2 + avg_yv**2)
            obj_vels.append(avg_vel)

            obj_id = row[0]
            xvels = []
            yvels = []

    cdf = Cdf(obj_vels)
    pr = cdf.PercentileRank(speed_limit)

    thinkplot.PrePlot(2)
    titlestring = "{:0.1f} % of {} are exceeding the {} mph limit".format(
        100 - pr,
        'vehicles' if only_vehicle else 'road users',
        speed_limit)
    thinkplot.Cdf(cdf)
    thinkplot.Vlines(speed_limit, 0, 1)
    thinkplot.Config(title=titlestring, xlabel='Velocity (mph)', ylabel='CDF')
    if dir is not None:
        thinkplot.Save(os.path.join(dir, 'velocityCDF'), formats=['jpg'], bbox_inches='tight')
    else:
        thinkplot.Show()

def road_user_counts(filename):
    """obtains road user count information

    Arguments
    ---------
    filename: sqlite database strings

    Returns
    -------
    roadusercounts: dictionary mapping user type strings to counts
    """
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()

    queryStatement = 'SELECT * FROM objects ORDER BY object_id'
    cursor.execute(queryStatement)

    userlist = ['unknown', 'car', 'pedestrian',
                'motorcycle', 'bicycle', 'bus', 'truck']
    roadusers = {'unknown': [], 'car': [], 'pedestrian': [],
                 'motorcycle': [], 'bicycle': [], 'bus': [], 'truck': []}

    for row in cursor:
        obj_id = row[0]
        usernum = row[1]

        usertype = userlist[usernum]
        roadusers[usertype].append(obj_id)

    # print roadusers

    roadusercounts = {}
    for user in userlist:
        roadusercounts[user] = len(roadusers[user])

    return roadusercounts
     
def road_user_chart(filename):
    """Creates a bar graph chart of road user counts"""
    roadusercounts = road_user_counts(filename)
    userlist, numusers = zip(*roadusercounts.items())

    fig = plt.figure()
    ax = fig.add_subplot(111)

    width = 0.5
    index = np.arange(len(userlist))
    ax.bar(index, numusers, width)

    ax.set_xticks(index + width / 2)
    ax.set_xticklabels(userlist)

    plt.xlabel('Road User Type')
    plt.ylabel('Number of Road Users')
    plt.title('Road User Type Counts')

    connection.commit()
    connection.close()

def road_user_icon_counts(title, car, bike, pedestrian, save_path, textcolor='#000000', facecolor='#FFFFFF', iconpath=None):
    """
    car, bike, pedestrian: str or int, the desired data to display under these different road users

    Example:
    road_user_icon_counts(title='Road User Counts', car=10, bike='bike', pedestrian=0, save_path='out.png')
    """
    dpi = 100.0
    mpl_width, mpl_height = (10, 8)

    # make figure without frame
    fig = plt.figure(frameon=False)
    fig.set_size_inches(mpl_width, mpl_height)
    ax = fig.add_subplot(111)

    # hide axis
    ax.set_axis_off()

    # set your axis size
    ax.axis([0, mpl_width, 0, mpl_height])

    fontsize = 30

    # Title
    title_y = 0.85
    ax.text(0.5*mpl_width, title_y*mpl_height, str(title), horizontalalignment='center', fontsize=fontsize, color=textcolor)

    car_loc = 0.15
    bike_loc = 0.5
    ped_loc = 0.85
    icon_y = 0.6
    text_y = 0.4

    if iconpath is None:
        # assumes that the icon image files are in the same directory as this file
        iconpath = os.path.dirname(os.path.abspath(__file__))

    # car icon
    fn = os.path.join(iconpath, 'car.png')
    arr_img = plt.imread(fn, format='png')
    im = OffsetImage(arr_img, zoom=0.7)
    ab = AnnotationBbox(im, (car_loc*mpl_width, icon_y*mpl_height), xycoords='data', frameon=False)
    ax.add_artist(ab)
    # car count
    ax.text(car_loc*mpl_width, text_y*mpl_height, str(car), horizontalalignment='center', fontsize=fontsize, color=textcolor)

    # bike icon
    fn = os.path.join(iconpath, 'bike.png')
    arr_img = plt.imread(fn, format='png')
    im = OffsetImage(arr_img, zoom=0.7)
    ab = AnnotationBbox(im, (bike_loc*mpl_width, icon_y*mpl_height), xycoords='data', frameon=False)
    ax.add_artist(ab)
    # bike count
    ax.text(bike_loc*mpl_width, text_y*mpl_height, str(bike), horizontalalignment='center', fontsize=fontsize, color=textcolor)

    # ped icon
    fn = os.path.join(iconpath, 'pedestrian.png')
    arr_img = plt.imread(fn, format='png')
    im = OffsetImage(arr_img, zoom=0.7)
    ab = AnnotationBbox(im, (ped_loc*mpl_width, icon_y*mpl_height), xycoords='data', frameon=False)
    ax.add_artist(ab)
    # bike count
    ax.text(ped_loc*mpl_width, text_y*mpl_height, str(pedestrian), horizontalalignment='center', fontsize=fontsize, color=textcolor)

    fig.savefig(save_path, dpi=dpi, bbox_inches=0, pad_inches=0, facecolor=facecolor, format='jpg')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('db', metavar='<.sqlite database file>',
                        help='A TrafficIntelligence generated .sqlite database.')
    parser.add_argument('fps', metavar='<frames per second>', type=int,
                        help='The frame rate of the video, in frames per second.')
    parser.add_argument(
        'homographyFile', nargs='?', metavar='<Homography>', help='The homography file name')
    parser.add_argument('roadImageFile', nargs='?', metavar='<Image>',
                        help='The name of the image file containing the video still')
    parser.add_argument('--vis-type', dest='vis_type', help='The visualization you wish to generate. ',
                        choices=['user-chart', 'vel-indiv', 'vel-overall', 'vel-user', 'trajectories', 'vel-overall-cdf'])

    args = parser.parse_args()

    if (args.vis_type == 'user-chart'):
        road_user_chart(args.db)
    elif (args.vis_type == 'vel-indiv'):
        vel_histograms(args.db, args.fps, 'indiv')
    elif (args.vis_type == 'vel-overall'):
        vel_histograms(args.db, args.fps, 'overall')
    elif (args.vis_type == 'vel-user'):
        road_user_vels(args.db, args.fps)
    elif (args.vis_type == 'vel-overall-cdf'):
        vel_cdf(args.db, args.fps)
    elif (args.vis_type == 'trajectories'):
        road_user_traj(
            args.db, args.fps, args.homographyFile, args.roadImageFile)
