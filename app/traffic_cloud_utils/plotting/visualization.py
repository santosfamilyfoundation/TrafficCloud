#! /usr/bin/env python
# import storage
import sqlite3
import math
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from thinkstats2 import Cdf
import seaborn as sns

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



def road_user_traj(filename, homographyFile, roadImageFile, save_path, objs_to_plot=None, plot_cars=False):
    """
    Plots all road-user trajectories.
    """
    homography = inv(loadtxt(homographyFile))

    connection = sqlite3.connect(filename)
    cursor = connection.cursor()

    queryStatement = 'SELECT * FROM objects ORDER BY object_id'
    cursor.execute(queryStatement)

    usertypes = {}
    for row in cursor:
        usertypes[row[0]] = row[1]

    queryStatement = 'SELECT * FROM object_trajectories ORDER BY object_id, frame'
    cursor.execute(queryStatement)

    obj_id = 0
    obj_traj_x = []
    obj_traj_y = []

    plt.figure(1)
    fig = plt.gcf()
    ax = fig.add_subplot(111)
    ax.set_axis_off()
    im = imread(roadImageFile)
    height, width, _ = im.shape
    implot = ax.imshow(im)

    userlist = ['unknown', 'car', 'pedestrian',
                'motorcycle', 'bicycle', 'bus', 'truck']
    alpha = 0.22
    colors = {'unknown': (0, 0, 0, alpha), 'car': (0, 0, 1, alpha), 'pedestrian': (0, 1, 0, alpha), 'motorcycle': (
        1, 0, 0, alpha), 'bicycle': (0, 1, 1, alpha), 'bus': (1, 1, 0, alpha), 'truck': (1, 0, 1, alpha)}

    for row in cursor:
        pos = Point(row[2], row[3])

        usertype = usertypes[obj_id]

        pos = pos.project(homography)
        obj_traj_x.append(pos.x)
        obj_traj_y.append(pos.y)

        if(row[0] != obj_id):
            usertype = userlist[usertype]

            if plot_cars or (usertype == 'pedestrian' or usertype == 'bicycle'):
                if objs_to_plot is None or obj_id in objs_to_plot:
                    ax.plot(obj_traj_x[:-1], obj_traj_y[:-1], ".-",
                        color=colors[usertype], label=usertype, linewidth=2, markersize=3)

            print 'switching object to: ', row[0]
            obj_id = row[0]
            obj_traj_x = []
            obj_traj_y = []

    if not plot_cars:
        colorlist = []
        recs = []
        # pedestrians and bike trajectory only
        for idx, i in enumerate([2, 4]):
            colorlist.append(colors[userlist[i]])
            recs.append(mpatches.Rectangle((0, 0), 1, 1, fc=colorlist[idx]))
        ax.set_position([0.1, 0.1, 0.85, 0.85])
        ax.legend(recs, userlist, loc=8, mode="expand",
              bbox_to_anchor=(-.5, -.5, .1, .1))

        box = ax.get_position()
        ax.set_position(
            [box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        ax.legend(recs, [userlist[i] for i in [2,4]], loc='upper center', bbox_to_anchor=(
        0.5, -0.05), fancybox=True, shadow=True, ncol=4)

    ax.set_xlim([0, width])
    ax.set_ylim([0, height])
    ax.set_ylim(ax.get_ylim()[::-1])

    ax.set_title('Road User Trajectories')

    fig.savefig(save_path, bbox_inches=0, pad_inches=0, format='jpg')
    plt.close()

    connection.commit()
    connection.close()

def vel_distribution(filename, fps, save_dir):
    """
    Arguments
    ---------
    filename: str, path to database
    fps: frame rate of the video, in frames per second
    save_dir: directory to save image
    """
    if not os.path.exists(save_dir):
        raise ValueError("Save directory does not exist. Should be the final_images folder")

    connection = sqlite3.connect(filename)
    cursor = connection.cursor()

    # Query for trajectories of only cars
    queryStatement = '''SELECT object_trajectories.object_id AS object_id, frame, x, y, x_v, y_v
        FROM object_trajectories INNER JOIN objects ON object_trajectories.object_id = objects.object_id
        WHERE road_user_type = 1
        ORDER BY object_id, frame'''
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

    # calculate 85th percentile speed
    cdf = Cdf(obj_vels)
    speed_85 = cdf.Percentile(85)

    titlestring = "85th percentile speed of cars is {} mph".format(int(speed_85))

    sns_plot = sns.distplot(obj_vels, kde=False)
    ylim = plt.gca().axes.get_ylim()
    plt.plot(len(ylim) * [speed_85], ylim)
    fig = sns_plot.get_figure()
    fig.suptitle(titlestring)
    sns_plot.set_xlabel('Velocity (mph)')
    sns_plot.set_ylabel('Counts')
    fig.savefig(os.path.join(save_dir, 'velocityPDF.jpg'), format='jpg', bbox_inches='tight')

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
    plt.close()

def turn_icon_counts(turn_dict, save_path, textcolor='#000000', facecolor='#FFFFFF', iconpath=None):
    """
    Takes a dictionary like {'up':{'right':2,'left'3','straight':4},'down':{...},...}, and produces
    a visualization showing the amount of cars that turned each way for every direction.
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

    text_margin = 0.075

    if iconpath is None:
        # assumes that the icon image files are in the same directory as this file
        iconpath = os.path.dirname(os.path.abspath(__file__))

    num_cars = 0
    for (direction, d) in turn_dict.iteritems():
        for (turn, num) in d.iteritems():
            num_cars += num

    # car icon
    fn = os.path.join(iconpath, 'turns.png')
    arr_img = plt.imread(fn, format='png')
    zoom = (dpi * mpl_height - 100) / arr_img.shape[1]
    im = OffsetImage(arr_img, zoom=zoom)
    ab = AnnotationBbox(im, (.5*mpl_width, .5*mpl_height), xycoords='data', frameon=False)
    ax.add_artist(ab)
    # car count
    ax.text(.5*mpl_width, .35*mpl_height, str(num_cars), horizontalalignment='center', fontsize=fontsize, color=textcolor)

    for direction in ['right', 'down', 'left', 'up']:
        t = None
        if direction == 'right':
            x = -1
            t = 'x'
        elif direction == 'left':
            x = 1
            t = 'x'
        elif direction == 'up':
            y = -1
            t = 'y'
        elif direction == 'down':
            y = 1
            t = 'y'

        for turn in ['left', 'straight', 'right']:
            proportion = .33
            if turn == 'left':
                if t == 'y':
                    x = -proportion * y
                elif t == 'x':
                    y = -proportion * x

            elif turn == 'straight':
                if t == 'y':
                    x = 0
                elif t == 'x':
                    y = 0
                 
            elif turn == 'right':
                if t == 'y':
                    x = proportion * y
                elif t == 'x':
                    y = proportion * x

            x1 = .075 + (1 - 2*0.075)*(1+x)/2.0
            y1 = .02 + (1 - 0.075)*(1+y)/2.0
            ax.text(x1*mpl_width, y1*mpl_height, str(turn_dict[direction][turn]), horizontalalignment='center', fontsize=fontsize, color=textcolor)

    fig.savefig(save_path, dpi=dpi, bbox_inches=0, pad_inches=0, facecolor=facecolor, format='jpg')
    plt.close()


