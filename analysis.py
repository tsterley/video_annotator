import csv, yaml
import os, errno, sys
import numpy as np
import cv2

if getattr(sys, 'frozen', False):
    ROOT_FOLDER = os.path.dirname(os.path.realpath(sys.executable))
elif __file__:
    ROOT_FOLDER = os.path.dirname(os.path.realpath(__file__))

CHART_HEIGHT = 500
CHART_WIDTH  = 5000
GRAY_LEVEL   = 25


def load_data(data_location):
    with open(data_location, 'r') as input_file:
        reader = csv.reader(input_file)
        next(reader) # skip header

        # Turn into list
        data = list(reader)

        # Add behaviour lengths
        data_clean = []
        for i in range(len(data)-1):
            start_time = float(data[i][1])
            end_time   = float(data[i+1][1])
            data_clean.append([data[i][0], start_time, end_time-start_time])

        return data_clean

def get_action_totals(behaviours):
    totals = {}
    for b in behaviours:
        b_name = b[0]
        b_length = b[2]
        totals[b_name] = totals.get(b_name, 0) + b_length

    return totals

def extract_col(col_string):
    return [int(255*float(c)) for c in col_string.split(",")]

def create_behaviour_chart(behaviours, save_folder, colour_map):
    # Get scaled times (for block widths)
    total_time   = sum([b[2] for b in behaviours])
    scaled_times = [int(b[2]*(CHART_WIDTH/total_time)) for b in behaviours]

    # Create blank image
    chart_width = sum(scaled_times)
    chart_image_all = np.zeros((CHART_HEIGHT, chart_width, 3)) # RGB image
    chart_image_ind = {b[0]: GRAY_LEVEL*np.ones((CHART_HEIGHT, chart_width, 3)) for b in behaviours}

    # Add colours
    chart_i = 0 # image index
    for i, b in enumerate(behaviours):
        colour = colour_map.get(b[0], (GRAY_LEVEL, GRAY_LEVEL, GRAY_LEVEL)) # default to gray
        chart_image_all[:, chart_i:chart_i+scaled_times[i], :] = colour # set block to appropriate colour
        chart_image_ind[b[0]][:, chart_i:chart_i+scaled_times[i], :] = colour
        chart_i += scaled_times[i] # update index

    # Save image
    cv2.imwrite(os.path.join(save_folder, "all.jpeg"), chart_image_all)
    for b in chart_image_ind:
        cv2.imwrite(os.path.join(save_folder, b + ".jpeg"), chart_image_ind[b])

def analyse_annotation(results_folder):
    # Load data
    data_location = os.path.join(results_folder, "annotations.csv")
    inp_data = load_data(data_location)

    # Stats
    totals = get_action_totals(inp_data)

    # Colour chart
    conf_location = os.path.join(ROOT_FOLDER, "config", "default_config.yaml")
    with open(conf_location, 'r') as ymlfile:
        config  = yaml.load(ymlfile)
        actions = [act for act in config["actions"]["selectable"]]
        colour_map = {act["name"]: extract_col(act["colour"]) for act in actions}

        create_behaviour_chart(inp_data, results_folder, colour_map)

    # Create summary document
    summary_location = os.path.join(results_folder, "summary.md")
    try:
        os.remove(summary_location)
    except OSError: pass

    with open(summary_location, 'a') as summary_file:
        # Heading
        summary_file.write("## %s\n" % os.path.split(results_folder)[-1])
        summary_file.write("\n")
        summary_file.write("---\n")
        summary_file.write("\n")

        # Stats
        summary_file.write("### Stats\n")
        summary_file.write("#### Total time(s)\n")
        for t in totals:
            summary_file.write("%s: %.2f\n" % (t, totals[t]))


if __name__ == "__main__":
    folder_name = os.path.join("results", "example")
    analyse_annotation(folder_name)
