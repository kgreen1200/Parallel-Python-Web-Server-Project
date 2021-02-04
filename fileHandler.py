"""
Author:         Kevin Green
File:           fileHandler.py
Date:           November 14, 2020
Course:         COMP 177 - Computer Networking
Description:    Python file to find content type, last modified time, and file size of a file
                Do not run this file, run server.py instead
"""

import os
import mimetypes


def get_file_info(base, file_name):
    content_type = None             # file type of the file
    last_modified_time = None       # time the file was last modified
    content_length = None           # size of the file

    if file_name is None:  # returns none if no file was requested
        return content_type, last_modified_time, content_length

    filepath = base + file_name
    if os.path.isfile(filepath) is False:  # returns none if the file doesn't exist
        return content_type, last_modified_time, content_length

    guess = mimetypes.guess_type(filepath)              # get content type
    content_type = guess[0]
    last_modified_time = os.path.getmtime(filepath)     # get the time it was last modified
    content_length = os.path.getsize(filepath)          # get file size

    return content_type, last_modified_time, content_length
