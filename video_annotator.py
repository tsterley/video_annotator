import os, errno
import yaml
import cv2
import numpy as np


WIN_MAX_H = 1000
WIN_MAX_W = 1000

COL_WHITE = (255, 255, 255)
COL_LGRAY = (150, 150, 150)
COL_GRAY  = (50, 50, 50)
COL_DGRAY = (30, 30, 30)
COL_BLACK = (0, 0, 0)

# Control keys
PAUSE_KEY_C = 32    # Spacebar
QUIT_KEY_C  = 27    # Escape

FAST_KEY = ']'
SLOW_KEY = '['
BACK_KEY = ','
FORW_KEY = '.'
SAVE_KEY = 's'

MAX_SPEED_MULT = 5
JUMP_SIZE = 50

# Status bar
STAT_B_H = 100
TIME_H_OFF = 30
TIME_W_OFF = 180
MULT_OFF_W = 230

# Pause icon
P_HALF_H = 20
P_NEAR_W = 12
P_FAR_W  = 40
P_COLOUR = COL_WHITE

# Progress bar
CA_W = 50
CA_H = 50
CA_OFF_H = 10
PB_H = 20 # Progress bar height
PB_OFF_H = 30
PB_OFF_W = 10

# Pen up/down
LIFT_PEN = '/'
PEN_UP_COL = COL_BLACK
PEN_UP_KEY = ""

NONE_COL = COL_GRAY
NONE_KEY = 'z'
NONE_ACTION = "no_activity"


def get_key_pressed(wait_time):
    return cv2.waitKey(wait_time) & 0xFF

def extract_col(col_string):
    return [int(255*float(c)) for c in col_string.split(",")]

def fix_win_size(height, width):
    cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('frame', width, height)

def add_pause_button(img):
    ch, cw = [f/2 for f in img.shape[:2]]
    img[ch-P_HALF_H:ch+P_HALF_H, cw-P_FAR_W:cw-P_NEAR_W, :] = P_COLOUR
    img[ch-P_HALF_H:ch+P_HALF_H, cw+P_NEAR_W:cw+P_FAR_W, :] = P_COLOUR

    return img

def string_from_time(time_ms):
    s = (time_ms/1000) % 60
    m = (time_ms/(1000*60)) % 60
    h = (time_ms/(1000*60*60)) % 24
    return "%02d:%02d:%02d" % (h, m, s)

def show_legend_image(actions, vid_wid):
    actions = list(actions)

    # Other keys
    none_colour = ','.join(map(str, NONE_COL)) # lol
    actions.append({'colour': none_colour,   'name': "no activity",    'key': NONE_KEY})
    actions.append({'colour': '1.0,1.0,1.0', 'name': 'increase speed', 'key': FAST_KEY})
    actions.append({'colour': '1.0,1.0,1.0', 'name': 'decrease speed', 'key': SLOW_KEY})
    actions.append({'colour': '1.0,1.0,1.0', 'name': 'jump back',      'key': BACK_KEY})
    actions.append({'colour': '1.0,1.0,1.0', 'name': 'jump forward',   'key': FORW_KEY})

    legend = np.zeros((len(actions)*(50 + 2*5) + 120, 600, 3), np.uint8) + 255

    for i, a in enumerate(actions):
        ys = i*(50 + 2*5)
        legend[ys + 5:ys + 55, 5:55, :] = COL_BLACK
        legend[ys + 6:ys + 54, 6:54, :] = extract_col(a["colour"])

        descrip = a["key"] + "  " + a["name"]
        cv2.putText(legend, descrip, (18, ys+40), cv2.FONT_HERSHEY_PLAIN, 2, COL_BLACK, 2)

    cv2.putText(legend, "Press spacebar to toggle pause.", (5, ys + 100), cv2.FONT_HERSHEY_PLAIN, 2, COL_BLACK, 2)
    cv2.putText(legend, "Press escape to quit.", (5, ys + 150), cv2.FONT_HERSHEY_PLAIN, 2, COL_BLACK, 2)

    # return legend
    cv2.imshow('legend', legend)
    cv2.moveWindow('legend', int(vid_wid), 0)

def add_act_feedback(img, current_col, current_key, progress_bar,
                        curr_progress_start, curr_progress_end):
    # Current activity
    img[-CA_OFF_H-CA_H:-CA_OFF_H, PB_OFF_W:PB_OFF_W+CA_W, :] = current_col
    cv2.putText(img, current_key, (PB_OFF_W+15, img.shape[0]-CA_OFF_H-CA_H+32),
                        cv2.FONT_HERSHEY_PLAIN, 2, COL_BLACK, 2)

    # Progress bar
    PB_top = -STAT_B_H+PB_OFF_H-PB_H
    PB_bot = -STAT_B_H+PB_OFF_H
    img[PB_top:PB_bot, PB_OFF_W:-PB_OFF_W, :] = progress_bar

    # Current location
    mark_col = COL_DGRAY if (current_key is PEN_UP_KEY) else COL_WHITE
    mark_start = curr_progress_start + PB_OFF_W
    mark_end   = max(curr_progress_end + PB_OFF_W, mark_start+1)
    img[PB_top-5:PB_top, mark_start:mark_end, :] = mark_col      # above
    img[PB_bot:PB_bot+5, mark_start:mark_end, :] = mark_col      # below

    return img

def analyse_video(video_location, mouse_actions):
    # Load video
    inp_video = cv2.VideoCapture(video_location)
    reset_image = True
    speed_mult = 1

    # Settings
    frame_t = (inp_video.get(cv2.CAP_PROP_FPS))   # Delay between frames
    frame_i = 0
    frame_i_to_t = lambda i: (1.0 / frame_t) * i

    vid_len = int(inp_video.get(cv2.CAP_PROP_FRAME_COUNT))
    vid_wid = inp_video.get(cv2.CAP_PROP_FRAME_WIDTH)
    vid_hgt = inp_video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    total_time_str = string_from_time(frame_i_to_t(vid_len)*1e3)

    paused  = True # Start paused
    pen_dwn = False # Start up
    curr_time = 0.0

    if vid_len == 0:
        print "Video didn't load"
        return

    # Display window
    if vid_wid > WIN_MAX_W:
        fix_win_size(int((WIN_MAX_W/vid_wid)*vid_hgt), WIN_MAX_W)
    elif vid_hgt > WIN_MAX_H:
        fix_win_size(WIN_MAX_H, int((WIN_MAX_H/vid_hgt)*vid_wid))
    else:
        fix_win_size(int(vid_hgt), int(vid_wid))

    cv2.startWindowThread()
    show_legend_image(mouse_actions, vid_wid)

    # Actions to dict
    mouse_keys = {act["key"]: act["name"] for act in mouse_actions}
    mouse_cols = {act["name"]: extract_col(act["colour"]) for act in mouse_actions}

    if NONE_KEY not in mouse_keys:
        mouse_keys[NONE_KEY] = NONE_ACTION
        mouse_cols[NONE_ACTION] = NONE_COL

    # State
    current_action = NONE_ACTION
    current_key = PEN_UP_KEY

    actions = [NONE_ACTION] * vid_len
    progress_bar = [NONE_COL] * int(vid_wid - (2*PB_OFF_W))
    idx_scalar  = float(len(progress_bar)) / vid_len # pre-calc scalar for index conversion
    idx_convert = lambda x: int(idx_scalar * x)

    # Play
    while (inp_video.isOpened()):
        # Get video frame
        if reset_image or not paused:
            reset_image = False
            _, frame_read = inp_video.read()
            curr_time = inp_video.get(cv2.CAP_PROP_POS_MSEC)
            frame_i = int(inp_video.get(cv2.CAP_PROP_POS_FRAMES))-1

        if (frame_read is None) or (frame_i >= vid_len):
            paused = True # Video reached the end
            frame_i = vid_len-1
        else:
            frame_orig = np.array(frame_read)

        # Add status bar
        frame = cv2.copyMakeBorder(frame_orig, top=0, bottom=STAT_B_H,
                                   left=0, right=0, borderType=cv2.BORDER_CONSTANT,
                                   value=COL_BLACK)
        frame[-STAT_B_H,:,:] = COL_WHITE

        # Progress bar
        pi_s, pi_e = idx_convert(frame_i), idx_convert(frame_i+1)
        if pen_dwn:
            current_col = mouse_cols[current_action]
            for pi in xrange(pi_s, pi_e):
                progress_bar[pi] = current_col

            actions[frame_i] = current_action
        else:
            current_col = PEN_UP_COL
            current_key = PEN_UP_KEY

        # Display frame
        frame = add_act_feedback(frame, current_col, current_key, progress_bar, pi_s, pi_e)
        cv2.putText(frame, "| x%i |" % speed_mult, (int(vid_wid)-MULT_OFF_W, int(vid_hgt)-TIME_H_OFF+STAT_B_H),
                            cv2.FONT_HERSHEY_PLAIN, 1, COL_WHITE, 1)
        time_str = string_from_time(curr_time) + " / " + total_time_str
        cv2.putText(frame, time_str, (int(vid_wid)-TIME_W_OFF, int(vid_hgt)-TIME_H_OFF+STAT_B_H),
                        cv2.FONT_HERSHEY_PLAIN, 1, COL_WHITE, 1)
        if paused: frame = add_pause_button(frame)

        cv2.imshow('frame', frame)

        # Wait for delay or user input
        inp_key_c = get_key_pressed(int((1000.0 / frame_t) / speed_mult))
        inp_key = chr(inp_key_c)

        if inp_key_c == QUIT_KEY_C:
            # User stopped video
            break

        elif inp_key in (SLOW_KEY, FAST_KEY):
            # User adjusting speed
            if inp_key == FAST_KEY:
                speed_mult = min(MAX_SPEED_MULT, speed_mult+1)
            else:
                speed_mult = max(1, speed_mult-1)

        elif inp_key in (BACK_KEY, FORW_KEY):
            # Jump back
            direc = 1 if (inp_key==FORW_KEY) else -1
            new_frame_i = np.clip(frame_i + direc*JUMP_SIZE, 0, vid_len-1)
            inp_video.set(cv2.CAP_PROP_POS_FRAMES, new_frame_i)
            reset_image = True

            # Edit mode
            pen_dwn = False
            paused  = True

        elif inp_key in mouse_keys.keys():
            # User is marking new action
            pen_dwn = True
            current_action = mouse_keys[inp_key]
            current_key = inp_key

        elif inp_key_c == PAUSE_KEY_C:
            paused = not paused

    # pop the question
    cv2.putText(frame, "Press '%s' to save and" % SAVE_KEY, (PB_OFF_W, int(vid_hgt/2) + 100), cv2.FONT_HERSHEY_PLAIN, 2, COL_WHITE, 2)
    cv2.putText(frame, "any other key to quit.", (PB_OFF_W, int(vid_hgt/2) + 150), cv2.FONT_HERSHEY_PLAIN, 2, COL_WHITE, 2)
    cv2.imshow('frame', frame)
    decision = chr(get_key_pressed(0))

    out_actions = None
    if decision == SAVE_KEY:
        print "Saving"

        # Save action changes
        out_actions = [(actions[0], frame_i_to_t(0))]
        for i in xrange(1, vid_len):
            if actions[i] != actions[i-1]:
                out_actions.append((actions[i], frame_i_to_t(i)))
        out_actions.append(("VIDEO_END", frame_i_to_t(vid_len)))

    inp_video.release()
    cv2.destroyAllWindows()

    return out_actions


if __name__ == "__main__":
    # file locations
    file_name = "example"

    root_location = os.path.dirname(os.path.realpath(__file__))
    video_location = os.path.join(root_location,  "videos", file_name + ".mp4")
    results_folder = os.path.join(root_location,  "results", file_name)
    save_location  = os.path.join(results_folder, "annotations.csv")
    conf_location  = os.path.join(root_location,  "config", "default_config.yaml")

    # run annotation
    with open(conf_location, 'r') as ymlfile:
        config = yaml.load(ymlfile)
        mouse_actions  = tuple([act for act in config["actions"]["selectable"]])

        recorded_actions = analyse_video(video_location, mouse_actions)

        # Save results
        if recorded_actions:
            # Create folder
            try: os.makedirs(results_folder)
            except OSError as e:
                if e.errno != errno.EEXIST: raise

            with open(save_location, 'w') as output_file:
                output_file.write("Behaviour, start_time(ms)\n")
                for action in recorded_actions:
                    output_file.write("%s,%.4f\n" % (action[0], action[1]))
