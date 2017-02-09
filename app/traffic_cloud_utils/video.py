import os
import subprocess
import json
import matplotlib.pyplot as plt

tracking_filename = "tracking.mp4"
highlight_filename = "highlight.mp4"

def create_tracking_video(project_path, video_path):
    videos_folder = os.path.join(project_path, "final_videos")
    temp_video_prefix = "temp_tracking_video-"

    count = 0
    num_frames_per_vid = 60
    num_frames = get_number_of_frames(video_path)

    # Make the videos folder if it doesn't exists
    if not os.path.exists(videos_folder):
        os.makedirs(videos_folder)

    delete_files(videos_folder, excluded_files=[highlight_filename])

    # Create a bunch of short videos ("snippets")
    while num_frames_per_vid * count < num_frames:
        create_video_snippet(project_path, video_path, videos_folder, temp_video_prefix, count, count*num_frames_per_vid, (count + 1)*num_frames_per_vid - 1)
        count += 1

    combine_videos(videos_folder, temp_video_prefix, tracking_filename)
    delete_files(videos_folder, temp_video_prefix, ["mpg", "mp4"], excluded_files=[tracking_filename, highlight_filename])

def create_highlight_video(project_path, video_path, list_of_near_misses):
    videos_folder = os.path.join(project_path, "final_videos")
    temp_video_prefix = "temp_highlight_video-"

    upper_frame_limit = get_number_of_frames(video_path)

    # Make the videos folder if it doesn't exists
    if not os.path.exists(videos_folder):
        os.makedirs(videos_folder)

    delete_files(videos_folder, excluded_files=[tracking_filename])

    for i, near_miss in enumerate(list_of_near_misses):
        start_frame, end_frame, object_id1, object_id2 = near_miss

        # Create a short video snippet of the near miss interaction
        snippet_number = 2*i + 1
        pts_multiplier = 3.0 # > 1.0 = slower ; < 1.0 = faster than
        print [object_id1, object_id2]
        create_video_snippet(project_path, video_path, videos_folder, temp_video_prefix, snippet_number,
            max(0, start_frame-30), min(upper_frame_limit, end_frame+30), pts_multiplier, [object_id1, object_id2])

        # Get resolution of video
        snippet_path = os.path.join(videos_folder, temp_video_prefix + str(snippet_number) + ".mpg")
        width, height = get_resolution(snippet_path)

        # create title slide image
        slide_number = 2*i
        slide_name = temp_video_prefix + str(slide_number)
        slide_path = os.path.join(videos_folder, slide_name+'.png')
        create_title_slide(width, height, slide_path, object_id1, object_id2)

        # create title slide video
        create_video_from_image(videos_folder, slide_name+'.png', slide_name+'.mpg', 5)

    combine_videos(videos_folder, temp_video_prefix, highlight_filename)
    delete_files(videos_folder, temp_video_prefix, ["mpg", "mp4", "png"], excluded_files=[tracking_filename, highlight_filename])

## Helpers -- Internal use

def move_files_to_folder(from_folder, to_folder, prefix, extensions):
    if not os.path.exists(to_folder):
        os.makedirs(to_folder)
    for file in os.listdir(from_folder):
        if file.startswith(prefix):
            s = file.split('.')
            if len(s) == 2:
                e = s[1]
                # Then check extension is correct
                if e in extensions:
                    os.rename(os.path.join(from_folder, file), os.path.join(to_folder, file))

def delete_files(folder, prefix="", extensions=[], excluded_files=[]):
    if os.path.exists(folder):
        for file in os.listdir(folder):
            if file.startswith(prefix):
                s = file.split('.')
                has_extension = len(s) == 2
                extension_included = True

                # If it has an extension, don't delete it if it doesn't have an extension provided
                if has_extension:
                    e = s[1]
                    if len(extensions) > 0 and e not in extensions:
                        extension_included = False

                # If it has an extension that should be deleted (or extensions don't exist), and not in excluded files, delete it
                if extension_included:
                    if not file in excluded_files:
                        os.remove(os.path.join(folder, file))

def get_list_of_files(folder, prefix, extension):
    count = 0
    files = []

    while os.path.exists(os.path.join(folder, prefix+str(count)+"."+extension)):
        files.append(os.path.join(folder, prefix+str(count)+"."+extension))
        count += 1

    return files

### Video Helpers

#### Video Metadata

def get_number_of_frames(videopath):
    num = int(subprocess.check_output(["ffprobe",
        "-v", "error",
        "-count_frames",
        "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames",
        "-of", "default=nokey=1:noprint_wrappers=1",
        videopath]))
    return num

def get_framerate(videopath):
    list_o = str(subprocess.check_output(["ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=avg_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        videopath]))
    return str(int(list_o.strip().split('/')[0])/float(list_o.strip().split('/')[1]))

def get_resolution(videopath):
    """
    Returns
    -------

    (width, height) in number of pixels
    """
    out = subprocess.check_output(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', videopath])
    out = json.loads(out)
    return out['streams'][0]['width'], out['streams'][0]['height']

#### Video Creation

def create_video_from_images(images_dir, prefix, video_dir, video_filename, framerate, extension="png"):
    '''
    Creates a video for images that are of the form prefix+number+.extension
    '''
    if not os.path.exists(video_dir):
        os.mkdir(video_dir)
    renumber_frames(images_dir, 0, prefix, extension)
    convert_frames_to_video(framerate, images_dir, video_dir, prefix, video_filename, 1.0)

def create_video_snippet(project_path, video_path, videos_folder, file_prefix, video_number, start_frame, end_frame, pts_multiplier=1.0, interacting_objects=None):
    images_folder = os.path.join(project_path, "temp_images")
    db_path = os.path.join(project_path, "run", "results.sqlite")
    temp_image_prefix = "image-"

    # Make the images folder if it doesn't exists
    if not os.path.exists(images_folder):
        os.makedirs(images_folder)

    # Delete old images, and recreate them in the right place
    delete_files(images_folder, temp_image_prefix, ["png"], excluded_files=[tracking_filename, highlight_filename])

    # Call display trajectories
    display_trajectories_call = ["display-trajectories.py",
        "-i", video_path,
        "-d", db_path,
        "-o", os.path.join(project_path, "homography", "homography.txt"),
        "-t", "object",
        "--save-images",
        "-f", str(start_frame),
        "--last-frame", str(end_frame),
        "--output-directory", images_folder,
        ]
    if interacting_objects is not None:
        display_trajectories_call.extend(['--interacting-objects', str(interacting_objects[0]), str(interacting_objects[1])])
    subprocess.call(display_trajectories_call)

    # Get the frames, and create a short video out of them
    renumber_frames(images_folder, start_frame, temp_image_prefix, "png")
    convert_frames_to_video(get_framerate(video_path), images_folder, videos_folder, temp_image_prefix, file_prefix + str(video_number) + ".mpg", pts_multiplier)

def create_video_from_image(folder, image_filename, video_filename, duration):
    subprocess.call(["ffmpeg",
        "-loop", "1",
        "-i", os.path.join(folder, image_filename),
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        os.path.join(folder, video_filename)])

def combine_videos(videos_folder, temp_video_prefix, filename):
    # The only way I could find to join videos was to convert the videos to .mpg format, and then join them.
    # This seems to be the only way to keep ffmpeg happy.

    # Using Popen seems to be necessary in order to pipe the output of one into the other
    p1 = subprocess.Popen(['cat']+get_list_of_files(videos_folder, temp_video_prefix, "mpg"), stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['ffmpeg',
        '-f', 'mpeg',
        '-i', '-',
        '-qscale', '0',
        '-vcodec', 'mpeg4',
        os.path.join(videos_folder, filename)], stdin=p1.stdout, stdout=subprocess.PIPE)

    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    p2.wait()

### Images Helpers

def renumber_frames(folder, start_frame, prefix, extension):
    temp_folder = os.path.join(folder, "temp")
    # Make the temp folder if it doesn't exists
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    # Rename them all to 'new-image-x' in order to not interfere with the current 'image-x'
    for file in os.listdir(folder):
        if file.startswith(prefix):
            rest = file[len(prefix):]
            s = rest.split('.')
            if len(s) == 2:
                e = s[1]
                if e == extension:
                    number = rest.split('.')[0]
                    try:
                        num = int(number) - start_frame
                    except:
                        print("Couldn't parse to int: "+file+" from prefix: "+prefix)
                    if num < 0:
                        raise Exception()
                    new_file = prefix+str(num)+'.'+extension
                    os.rename(os.path.join(folder, file), os.path.join(temp_folder, new_file))

    # Rename the 'new-image-x' to 'image-x'
    for file in os.listdir(temp_folder):
        os.rename(os.path.join(temp_folder, file), os.path.join(folder, file))

    os.removedirs(temp_folder)

def convert_frames_to_video(framerate, images_folder, videos_folder, images_prefix, filename, pts_multiplier):
    subprocess.call(["ffmpeg",
        "-framerate", framerate,
        "-i", os.path.join(images_folder, images_prefix+"%d.png"),
        "-filter:v", "setpts={:0.1f}*PTS".format(pts_multiplier),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        os.path.join(videos_folder, filename)])

def create_title_slide(width, height, save_path, object_id1, object_id2, fontsize=None, textcolor='#FFFFFF', facecolor='#000000'):
    """
    width: int, width in pixels of desired output
    height: int, pixel height of desired output

    Note: fontsize varies with the resolution of the video in a very dumb manner right now.
    If you want to control fontsize, provide it as a parameter
    """
    # heights and widths in matplotlib are units of inches, not pixels
    dpi = 100.0
    mpl_width = width / dpi
    mpl_height = height / dpi

    # make figure without frame
    fig = plt.figure(frameon=False)
    fig.set_size_inches(mpl_width, mpl_height)
    ax = fig.add_subplot(111)

    # hide axis
    ax.set_axis_off()

    # set your axis size
    ax.axis([0, mpl_width, 0, mpl_height])

    # 20 is a good font size for a 400 height image...
    # 40 is a good font size for a 800 height image
    if not fontsize:
        fontsize = height / 20

    ax.text(0.2*mpl_width, 0.75*mpl_height, 'Near Miss between', style='italic', fontsize=fontsize, color=textcolor)
    ax.text(0.2*mpl_width, 0.6*mpl_height, 'Object {}'.format(object_id1), fontsize=fontsize, color=textcolor)
    ax.text(0.2*mpl_width, 0.4*mpl_height, 'Object {}'.format(object_id2), fontsize=fontsize, color=textcolor)

    fig.savefig(save_path, dpi=dpi, bbox_inches=0, pad_inches=0, facecolor=facecolor)
