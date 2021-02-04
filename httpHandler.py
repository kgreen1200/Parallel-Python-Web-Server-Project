"""
Author:         Kevin Green
File:           httpHandler.py
Course:         COMP 177 - Computer Networking
Date:           November 14, 2020
Description:    Interprets incoming requests for the web server
                Creates new http headers as responses from the server
                Do not run this file, run server.py instead
"""

from datetime import datetime, timedelta


"""
Function:       interpret_incoming
Parameters:     message - string of http request
Description:    Takes in a http request and finds the HTTP command, a file that could be requested, or
                whether or not the keep connection
"""
def interpret_incoming(message):
    request = None
    file = None
    keep_connection = False

    if len(message) == 0:  # empty message
        return None, None, True

    # split messages into its separate lines
    split_message = message.split("\r\n")

    # read lines
    for line in split_message:
        if line.startswith("GET"):
            split_GET = line.split(" ")
            file = split_GET[1]
            if len(file) <= 2:
                file = "/index.html"
            request = "GET"
        elif line.startswith("HEAD"):
            split_HEAD = line.split(" ")
            file = split_HEAD[1]
            if len(file) <= 2:
                file = "/index.html"
            request = "HEAD"
        elif line.startswith("Connection"):
            line = line[len("Connection: "):]
            if line == "keep-alive":
                keep_connection = True
            else:
                keep_connection = False

    return request, file, keep_connection

"""
Function:       create_response
Parameters:     code - http code to respond to (200, 404, 501)
                data - data to attach to the end of the http header
                content_type - file type of the data
                content_length - total length of the entire file you are sending
                last_modified_time - last time that the file was modified
                keep_connection - specify whether to close or keep the current connection
Description:    Generates a http message
"""
def create_response(code, data, content_type, content_length, last_modified_time, keep_connection):
    # Response Code
    if code == 200:
        http_response = "HTTP/1.1 200 OK\r\n"
    elif code == 404:
        http_response = "HTTP/1.1 404 Not Found\r\n"
    else:
        http_response = "HTTP/1.1 501 Not Implemented\r\n"

    # Connection header
    http_response += "Connection: close\r\n"

    # Date header
    now, expiration_time = get_current_date()
    http_response += "Date: " + now + "\r\n"

    # Server header
    http_response += "Server: " + get_server_name() + "\r\n"

    # Connection header
    if keep_connection:
        http_response += "Connection: keep-alive\r\n"
    else:
        http_response += "Connection: close\r\n"

    if code == 200:
        # Content length
        http_response += "Content-Length: " + str(content_length) + "\r\n"
        # Content Type
        http_response += "Content-Type: " + content_type + "\r\n"
        # Last modified
        http_response += "Last-Modified: " + format_time_string(datetime.utcfromtimestamp(last_modified_time)) + "\r\n"
        # Expires
        http_response += "Expires: " + expiration_time + "\r\n"

    http_response += "\r\n"
    response_bytes = bytes(http_response, 'ascii')

    if code == 200:
        response_bytes += data

    return response_bytes


"""
Function:       get_current_date()
Description:    returns the current date and an expiration date 12 hours from now
"""
def get_current_date():
    now = datetime.utcnow()
    date_string = format_time_string(now)
    expiration_time_string = format_time_string(now + timedelta(hours=12))
    return date_string, expiration_time_string


"""
Function:       get_server_name()
Description:    returns the name of the server
"""
def get_server_name():
    return "Server/2.0.0 (Ubuntu)"


"""
Function:       format_time_string()
Parameter:      time - datetime object to convert
Description:    takes a datetime variable and converts it to a string
"""
def format_time_string(time):
    # Formats time to string as the following example format
    # Thu, 06 Au 1998 12:00:15 GMT
    time_string = time.strftime("%a, %d, %Y %H:%M%S GMT")
    return time_string
