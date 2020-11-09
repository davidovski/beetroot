from moviepy.editor import *
import sys
from moviepy.video.fx.all import *
import numpy
import cv2
from beatSync import BeatSyncer
from bass import low_pass
import time as clock

depth = 5


def scroll(get_frame, t):
    """
    This function returns a 'region' of the current frame.
    The position o f this region depends on the time.
    """
    frame = get_frame(t)
    frame_region = frame[int(t):int(t)+360,:]
    return frame_region


def rescale(frame, width, height):
    return cv2.resize(frame, dsize=(height, width), interpolation=cv2.INTER_CUBIC)


def rgb_shift_frame(frame, intensity):
    new_frame = numpy.zeros((len(frame), len(frame[0]), len(frame[0][0])))
    for x in range(len(frame)):
        for y in range(len(frame[x])):
            rgb = frame[x][y]
            blue_x = int(x-intensity*64)
            blue_x = 0 if blue_x < 0 else blue_x
            blue = (frame[blue_x][y][2] * rgb[2]) / 2

            red_x = int(x + intensity * 64)
            red_x = 0 if red_x > len(frame) - 1 else red_x
            red = (frame[red_x][y][0] * rgb[2]) / 2

            new_frame[x][y][0] = red
            new_frame[x][y][1] = rgb[1]
            new_frame[x][y][2] = blue

    # print(numpy.array(new_frame))
    return numpy.array(new_frame)


def calculate_zoom_factor(t, depth):
    a = ((t + 1) * 0.9) ** depth
    return 1 if a > 1 else a


def zoom_fx(get_frame, t, factor=5):
    intensity = calculate_zoom_factor(0, factor)
    # print(factor)
    frame = get_frame(t)
    width = len(frame)
    height = len(frame[0])
    #print(str(width) + ", " + str(height))

    nw = width * intensity
    nh = height * intensity

    startx, endx = int((width - nw) / 2), int((width - nw) / 2) + int(nw)
    starty, endy = int((height - nh) / 2), int((height - nh) / 2) + int(nh)

    sub_frame = [l for l in frame[startx:endx]]

    for i in range(len(sub_frame)):
        sub_frame[i] = sub_frame[i][starty:endy]
    o = rescale(numpy.array(sub_frame), width, height)

    return o


def vol_zoom_fx(get_frame, t, factor=5):
    try:
        f = 1 - abs(globals().get("sound").get_frame(t)[0])
    except Exception as e:
        f = 1
    print("#" * int(f * 10))
    intensity = (1 - (f * 0.2)) ** 2
    # intensity = f
    # print(factor)
    frame = get_frame(t)
    width = len(frame)
    height = len(frame[0])
    #print(str(width) + ", " + str(height))

    nw = width * intensity
    nh = height * intensity

    startx, endx = int((width - nw) / 2), int((width - nw) / 2) + int(nw)
    starty, endy = int((height - nh) / 2), int((height - nh) / 2) + int(nh)

    sub_frame = [l for l in frame[startx:endx]]

    for i in range(len(sub_frame)):
        sub_frame[i] = sub_frame[i][starty:endy]

    try:
        o = rescale(numpy.array(sub_frame), width, height)
    except Exception as e:
        o = frame
    return o


def bounce_fx(get_frame, t, factor=5):

    intensity = calculate_zoom_factor(t, factor)
    # print(factor)
    frame = get_frame(t)
    width = len(frame)
    height = len(frame[0])
    #print(str(width) + ", " + str(height))

    nw = width * intensity
    nh = height * intensity

    startx, endx = int((width - nw) / 2), int((width - nw) / 2) + int(nw)
    starty, endy = int((height - nh) / 2), int((height - nh) / 2) + int(nh)

    sub_frame = [l for l in frame[startx:endx]]

    for i in range(len(sub_frame)):
        sub_frame[i] = sub_frame[i][starty:endy]
    o = rescale(numpy.array(sub_frame), width, height)

    return o


def bounce_video(video, offset_ms, between_ms):

    time = between_ms / 1000

    print("Splitting beats... ", end="")

    clips = []
    t = offset_ms / 1000
    while t < video.duration - time:

        clips.append(video.subclip(t, t + time))
        t += time

    clips.pop(len(clips) - 1)

    print(" split " + str(len(clips)) + " beats")
    modified_clips = []
    print("Applying FX ", end="")

    lastMessage = "0/" + str(len(clips)) + " beats with unknown minutes remaining"
    print(lastMessage, end="")
    b = False
    i = 0
    last_time = clock.time()

    for clip in clips:
        try:
            time_left = ((clock.time() - last_time) * (len(clips) - i)) / 60
            print("\b" * len(lastMessage), end="")
            lastMessage = str(i + 1) + "/" + str(len(clips)) + " beats with " + str(int(time_left)) + " minutes remaining"
            print(lastMessage, end="")
            last_time = clock.time()

            globals().update(sound = clip.audio.to_soundarray())
            get_volume = lambda array: numpy.sqrt(((1.0 * array) ** 2).mean())
            volume = get_volume(sound)

            # print(volume)
            volume = volume ** 6
            # if volume < 0.1: volume = 0
            depth = volume * 5
            print(str(depth))
            modified_clips.append(clip.fl(bounce_fx, i=depth))
            depth = depth * 0.5
        except:
            modified_clips.append(clip)

        b = not b
        i += 1

    print("\nApplied all FX!")

    print("Concatenating Clips...")

    final_clip = concatenate_videoclips(modified_clips)

    return final_clip


def bounce_video_loudness(video):

    time = 10 / 1000

    print("\nApplied all FX!")

    globals().update(sound = video.audio)
    final_clip = video.fl(vol_zoom_fx)

    return final_clip


def set_video_length(clip, length):
    left = length - clip.duration
    number = int(left / clip.duration) + 1
    clips = [clip for i in range(number)]
    c = concatenate_videoclips(clips)
    return c


def bass_audio(audio_filename):
    return AudioFileClip(low_pass(audio_filename))


def music_bounce(audio_filename, video_filename, bounce_type="bpm"):

    if bounce_type == "bpm":
        data_file = audio_filename[:-3] + "data"

        if not os.path.exists(data_file):
            bs = BeatSyncer(audio_filename)
            sys.exit()

        bpm = 0
        offset = 0
        with open(data_file, "r") as f:
            lines = f.readlines()
            bpm = float(lines[0])
            offset = float(lines[1])

        beat_time = (1 / bpm) * 60 * 1000
    print("loading audio clips...")

    audioclip = AudioFileClip(audio_filename)
    print("detecting bass in audio...")

    bassaudioclip = bass_audio(audio_filename)

    print("loading video")

    if video_filename.endswith(".jpg") or video_filename.endswith(".png"):
        video = ImageClip(video_filename).set_fps(30).set_duration(2)
    else:
        video = VideoFileClip(video_filename)

    print("adjusting video length...")
    video2 = set_video_length(video, audioclip.duration)
    video3 = video2.set_audio(bassaudioclip)

    if bounce_type == "bpm":

        print("bouncing video: bpm" + str(bpm) + " offset:" + str(offset) + " beattime:" + str(beat_time))

        clip = bounce_video(video3, offset, beat_time)
    elif bounce_type == "loud":
        clip = bounce_video_loudness(video3)

    finalclip = clip.set_audio(audioclip)

    print("adding audio...")

    print("writing output")
    finalclip.write_videofile(audio_filename.split("/")[-1:][0][:-3] + "mp4")

    os.remove("tmp/BOOSTED-" + audio_filename.split("/")[-1])


music_bounce(input("Enter audio file: " , "Enter image / video file: ")
