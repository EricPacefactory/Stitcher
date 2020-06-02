#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 10:00:48 2020

@author: eo
"""


# ---------------------------------------------------------------------------------------------------------------------
#%% Imports

import os
import json
import subprocess
import argparse

import datetime as dt

from platform import uname
from collections import Counter
from tempfile import TemporaryDirectory

from local.eolib.utils.files import get_file_list
from local.eolib.utils.cli_tools import cli_prompt_with_defaults
from local.eolib.utils.ranger_tools import ranger_multifile_select

# ---------------------------------------------------------------------------------------------------------------------
#%% Define functions

# .....................................................................................................................

def parse_args():
    
    # Set up argparser options
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--folder", default = None, type = str, help = "Folder containing videos to stitch")
    ap.add_argument("-n", "--outname", default = None, type = str, help = "Output video file name")
    ap.add_argument("-p", "--outpath", default = None, type = str, help = "Output video file path")
    
    # Convert argument inputs into a dictionary
    ap_result = vars(ap.parse_args())
    
    return ap_result

# .....................................................................................................................

def captured_subprocess(run_command_list):
    ''' Use subprocess with captured stdout and stderr '''
    return subprocess.run(run_command_list, stderr = subprocess.PIPE, stdout = subprocess.PIPE)

# .....................................................................................................................

def check_req_installs():
    
    # Make sure we use the right 'check for program' command
    system_type = uname().system
    system_is_windows = ("windows" in system_type.lower())
    check_cmd = "where" if system_is_windows else "which"
    
    ffmpeg_check = captured_subprocess([check_cmd, "ffmpeg"])
    ranger_check = captured_subprocess([check_cmd, "ranger"])
    
    if ffmpeg_check.returncode != 0:
        print("",
              "WARNING: Couldn't find ffmpeg! This script may fail...",
              "On Ubuntu, install with:",
              "",
              "  sudo apt install ffmpeg",
              "",
              sep = "\n")
    
    if ranger_check.returncode != 0:
        print("",
              "WARNING: Couldn't find ranger! This script may fail...",
              "On Ubuntu, install with:",
              "",
              "  sudo apt install ranger",
              "",
              sep = "\n")
    
    return

# .....................................................................................................................

def history_date_format():
    return "%Y/%m/%d"

# .....................................................................................................................

def history_save_data(search_directory, date_dt):
    
    # Some useful variables
    history_file = ".history.json"    
    date_str = date_dt.strftime(history_date_format())
    
    # Create a new history data
    date_str = date_dt.strftime(history_date_format())
    save_data = {"search_directory": search_directory, "last_used_date": date_str}
    
    return history_file, save_data

# .....................................................................................................................

def load_default_search_directory():
    
    # Get current date, since we'll use this to determine if the history is 'fresh' enough to use
    date_now_dt = dt.datetime.now()
    default_directory = "~/Desktop"
    
    # Save a new history file if one doesn't already exist
    history_file, default_history = history_save_data(default_directory, date_now_dt)
    if not os.path.exists(history_file):
        with open(history_file, "w") as out_file:
            json.dump(default_history, out_file, indent = 2)
    
    # Load history file and compare with current date to decide if we should use it
    with open(history_file, "r") as in_file:
        history_dict = json.load(in_file)
    
    # Pull out history data
    history_directory = history_dict.get("search_directory")
    history_date = history_dict.get("last_used_date")    
    
    # Check if the history data is fresh enough to use
    history_dt = dt.datetime.strptime(history_date, history_date_format())
    history_age_delta = (date_now_dt - history_dt)
    fresh_enough = (history_age_delta < dt.timedelta(days = 1))
    
    search_directory = history_directory if fresh_enough else default_directory
    
    return search_directory

# .....................................................................................................................

def save_search_directory(example_file_path):
    
    # Get data to save into history file
    date_now_dt = dt.datetime.now()
    parent_folder_path = os.path.dirname(example_file_path)
    
    # Remove user pathing for cleanliness
    user_path = os.path.expanduser("~")
    save_file_directory = parent_folder_path.replace(user_path, "~")
    
    # Construct saving dictionary and save the file!
    history_file, save_data = history_save_data(save_file_directory, date_now_dt)
    with open(history_file, "w") as out_file:
        json.dump(save_data, out_file, indent = 2)
    
    return parent_folder_path

# .....................................................................................................................

def get_save_extension(input_file_paths_list):
    
    # First split ext off every file
    file_exts_only = [os.path.splitext(each_path)[1].lower() for each_path in input_file_paths_list]
    
    # Count occurances of extensions (in case there is more than one) and pick the most common
    ext_counter = Counter(file_exts_only)
    ordered_exts_list = ext_counter.most_common()
    save_ext, num_occurances = ordered_exts_list[0]
    
    # Provide feedback if we got multiple extension types
    num_exts = len(ordered_exts_list)
    if num_exts > 1:
        print("", 
              "Got more than 1 file extension type!",
              "Will use: {}".format(save_ext),
              "However, different extensions may cause errors while stitching...",
              sep = "\n")
    
    return save_ext

# .....................................................................................................................

def build_ffmpeg_command(input_text_file_path, output_video_path):
    
    # Build command used to stitch files from terminal
    run_command_list = ["ffmpeg", 
                        "-f", "concat",
                        "-safe", "0",
                        "-i", input_text_file_path,
                        "-c", "copy",
                        output_video_path]
    
    # Also make a human reable version (by removing full pathing), in case the user needs to debug
    human_friendly_list = ["ffmpeg", 
                           "-f", "concat",
                           "-safe", "0",
                           "-i", "<file_list_txt>",
                           "-c", "copy",
                           "<output_path>"]
    human_readable_str = " ".join(human_friendly_list)
    
    return run_command_list, human_readable_str

# .....................................................................................................................

def process_feedback(subproc_return, output_save_path, human_readable_command_str):
    
    # Figure out what kind of feedback to give
    return_code = subproc_return.returncode
    no_errors = (return_code == 0)
    if no_errors:
        print("",
              "*** Done! No errors ***", 
              "",
              "Saved result:",
              "@ {}".format(output_save_path),
              "", 
              sep="\n")
    else:
        save_exists = os.path.exists(output_save_path)
        print("", 
              "!" * 48,
              "",
              "Possible error! Got return code: {}".format(return_code),
              "File {} saved...".format("was" if save_exists else "was not"),
              "",
              "Using command:",
              "  {}".format(human_readable_command_str),
              "",
              "!" * 48,
              sep="\n")
    
    return

# .....................................................................................................................
# .....................................................................................................................


# ---------------------------------------------------------------------------------------------------------------------
#%% Setup
        
# Try to make sure ffmpeg and ranger are installed
check_req_installs()

# Get script arguments
input_args = parse_args()
arg_input_folder = input_args.get("folder")
arg_output_name = input_args.get("outname")
arg_output_path = input_args.get("outpath")

# Get file search directory
video_search_directory = load_default_search_directory()


# ---------------------------------------------------------------------------------------------------------------------
#%% Select video to clip

# Get the user to select videos or use the script argument
if arg_input_folder is None:
    
    # Some feedback before suddenly jumping into ranger
    print("",
          "Please use ranger cli to select video files for stitching",
          "  --> Use spacebar to select multiple videos.",
          "  --> When finished, hit enter to complete selection.",
          "",
          sep="\n")
    input("  Press Enter key to continue...")
    
    input_file_paths_list = ranger_multifile_select(start_dir = video_search_directory, sort_output = True)
    
else:    
    # Make sure the provided folder is valid
    arg_input_folder = os.path.expanduser(arg_input_folder)
    valid_input_folder = os.path.exists(arg_input_folder)
    if not valid_input_folder:
        print("", 
              "Provided input folder path is not valid!",
              "@ {}".format(arg_input_folder),
              "",
              "Quitting...", 
              sep = "\n")
        quit()
    
    # Provide some feedback about the selected files
    print("", 
          "Using input files from provided folder path:",
          "@ {}".format(arg_input_folder),
          sep="\n")
    
    # List all files in provided folder
    input_file_paths_list = get_file_list(arg_input_folder,
                                          show_hidden_files = False,
                                          create_missing_folder = False,
                                          return_full_path = True,
                                          sort_list = True)
    
# Sanity check
num_videos_to_stitch = len(input_file_paths_list)
no_paths = (num_videos_to_stitch == 0)
if no_paths:
    print("", "No files found!", "  Nothing to stitch. Quitting...", sep = "\n")
    quit()

# Save the loading directory, for easier re-use
parent_folder_path = save_search_directory(input_file_paths_list[0])


# ---------------------------------------------------------------------------------------------------------------------
#%% Print out selected files for confirmation

# Print out files (in order) for stitching
file_names_only = [os.path.basename(each_file_path) for each_file_path in input_file_paths_list]
file_names_strs = ["  {}".format(each_name) for each_name in file_names_only]
print("",
      "Files to stitch:",
      "(in order)",
      "",
      *file_names_strs,
      sep = "\n")

# Another sanity check
not_enough_files = (num_videos_to_stitch < 2)
if not_enough_files:
    print("", "Not enough files to stitch! Quitting...", sep = "\n")
    quit()

# Check file extensions, for saving
save_ext = get_save_extension(input_file_paths_list)


# ---------------------------------------------------------------------------------------------------------------------
#%% Figure out saving

# Figure out a reasonable save name and then ask the user if they want to go with something different
default_save_name = "stitched_{}_files".format(num_videos_to_stitch)

# Ask the user for a file name or user the script argument
if arg_output_name is None:
    user_outname = cli_prompt_with_defaults("Enter output file name: ", 
                                            default_value = default_save_name, 
                                            return_type = str)
else:
    user_outname = arg_output_name
    print("", "Using input argument for output file name:", "  {}".format(user_outname), sep="\n")

# Overwrite the default output path if a script argument is available
save_folder_path = parent_folder_path
if arg_output_path is not None:
    save_folder_path = os.path.expanduser(arg_output_path)
    os.makedirs(save_folder_path, exist_ok = True)
    print("", "Using input argument for output folder path:", "  {}".format(save_folder_path), sep="\n")

# Add back extension (and remove any user-added ext)
save_name = "{}{}".format(user_outname, save_ext)
save_path = os.path.join(save_folder_path, save_name)


# ---------------------------------------------------------------------------------------------------------------------
#%% *** FFMPEG Call *** 

# Some feedback
print("", "Stitching videos...", sep = "\n")

# Create file text entries, used to tell ffmpeg what to stitch
stitch_entries_list = ["file '{}'".format(each_file_path) for each_file_path in input_file_paths_list]
writelines_str = "\n".join(stitch_entries_list)

# Create temporary file to hold videos for stitching
with TemporaryDirectory() as temp_dir:
    
    # Write file list into the temporary file
    file_listing_path = os.path.join(temp_dir, "stitchlist.txt")
    with open(file_listing_path, "w") as text_file:
        text_file.writelines(writelines_str)
    
    # Run ffmpeg command to stitch videos
    run_command_list, human_readable_str = build_ffmpeg_command(file_listing_path, save_path)
    proc_out = captured_subprocess(run_command_list)
    
    # Final feedback
    process_feedback(proc_out, save_path, human_readable_str)


# ---------------------------------------------------------------------------------------------------------------------
#%% Scrap


