#!/usr/bin/env python3
"""
Author:                     Kevin Green
File:                       server.py
Course:                     COMP 177 - Computer Networking
Date:                       November 14, 2020
Description:                Main .py file for a parallel web server
"""

import argparse             # Used to parsing arguments given on commandline
import os                   # Used for file verification
import sys                  # Used to exit program
import socket               # Used for creating and using TCP connections
import threading            # Used for threads to make server parallel
import httpHandler          # Used to interpret requests and generate replies
import fileHandler          # Used to get information about a given file

current_version = "2.0.0"   # Current version of the webserver


"""
Class:          ConnectionThread
Description:    Thread that handles data transfer between the server and an incoming client. Allows for 
                multiple connections to be handled at once, making the server parallel.
"""


class ConnectionThread(threading.Thread):
    # Thread constructor
    def __init__(self, client_s, client_addr, max_recv, base, verbose):
        threading.Thread.__init__(self)     # Required
        self.client_socket = client_s       # Socket on which thread will communicate with client
        self.client_addr = client_addr      # Client address and port
        self.max_recv_size = max_recv       # Maximum amount of bytes that can be read from recv()
        self.base = base                    # Base directory for the website
        self.keep_connection = True         # Becomes false when it is time to close the connection
        self.verbose = verbose              # True if debugging output is enabled, False otherwise

    # The run() method of a Thread class in run when
    # thread.start() is called. Do real work here
    def run(self):
        self.client_socket.settimeout(30.0)  # Set timeout time to 30 seconds on the socket
        while self.keep_connection is True:  # keep running so long as the client gives keep_connection as true
            """ STEP 5: RECEIVE DATA """
            raw_bytes = b''
            timed_out = False
            while True:
                try:
                    chunk = self.client_socket.recv(self.max_recv_size)
                except socket.timeout:
                    timed_out = True
                    break
                except socket.error as msg:
                    print("ERROR: Unable to recv()")
                    print("Description: " + str(msg))
                    sys.exit()
                raw_bytes += chunk
                if len(chunk) < self.max_recv_size:
                    break

            if timed_out:  # close connection if no message in 30 seconds
                if self.verbose:
                    print("Connection timed out, closing connection.\n")
                break

            if len(raw_bytes) == 0:  # Client received an empty message, meaning client closed connection
                if self.verbose:
                    print("The client has closed the connection.\n")
                break

            string_unicode = raw_bytes.decode('ascii')                              # make human-readable

            if self.verbose:                                                        # print request if verbose
                print("Received %d bytes from client" % len(raw_bytes))
                print("Message Contents:\n%s" % string_unicode)

            """ STEP 6: HANDLE REQUEST """
            request, file, self.keep_connection = httpHandler.interpret_incoming(string_unicode)  # parse request
            if file is not None:
                # get content type, last time file was modified, and the file size in bytes
                content_type, last_modified_time, content_length = fileHandler.get_file_info(self.base, file)

                if last_modified_time is not None:  # this means the file has to exist
                    code = 200  # ok code
                    if request == "HEAD":
                        # if request if HEAD, then only send the HTTP Header
                        response = httpHandler.create_response(code, None, content_type, content_length,
                                                               last_modified_time, self.keep_connection)
                        send(self.client_socket, response)
                    else:  # Get requested, send the actual file
                        max_bytes_read = 1024  # the thread will only read a maximum of 1 kilobyte at a time
                        filepath = self.base + file

                        # open the file to read bytes
                        file = open(filepath, "rb")

                        data = file.read(max_bytes_read)
                        response = httpHandler.create_response(code, data, content_type, content_length,
                                                               last_modified_time, self.keep_connection)
                        send(self.client_socket, response)
                        while len(data) >= max_bytes_read:  # continue to read and send data until end of file
                            data = file.read(max_bytes_read)
                            send(self.client_socket, data)

                else:  # The file was not found
                    code = 404  # file not found
                    response = httpHandler.create_response(code, None, None, None, None, self.keep_connection)
                    send(self.client_socket, response)

            elif len(raw_bytes) != 0:  # File was not requested but message had some other content
                code = 501  # Not implemented
                response = httpHandler.create_response(code, None, None, None, None, self.keep_connection)
                send(self.client_socket, response)

            if self.verbose:
                print("Response to client has been sent.\n")

        """ STEP 7: CLOSE SOCKETS """
        try:
            self.client_socket.close()
        except socket.error as msg:
            print("ERROR: unable to close() socket")
            print("Description: " + str(msg))
            sys.exit()
        if self.verbose:
            print("Closing socket with Client IP, port %s\n" % str(self.client_addr))

        # to exit the thread, just return from the run() method


"""
Function:       main()
Description:    Main web server function, listens for incoming connections, creates threads, handles Ctrl+C
                and parses arguments
"""
def main():
    listening_socket = None     # socket that is going to be used for listening to incoming connections
    all_thread = None           # list of all threads that have been created, to ensure that they close before exiting

    try:  # runs the following code until a keyboard interrupt comes in, so that it can properly exit the program

        """ STEP 0: PARSE ARGUMENTS """
        parser = argparse.ArgumentParser(description="Parallel Web Server for COMP 177 - Computer Networking")
        # add arguments
        parser.add_argument("--version", action="store_true", help="Show program's version number and exit")
        parser.add_argument("--verbose", action="store_true", help="Enable debugging output for server")
        parser.add_argument("--base", action="store", help="Base directory containing website")
        parser.add_argument("--port", action="store", type=int, help="Port number to listen on")
        parser.add_argument("--recv", action="store", type=int, help="Maximum number of bytes to receive at a time")

        args = parser.parse_args() # parse the argurments and turn into a dictionary
        args = vars(args)

        """ STEP 1: ANALYZE ARGUMENTS """
        if args["version"]:
            print("\nServer.py version " + current_version + "\n")
            sys.exit()
        if args["port"] is None:
            args["port"] = 8080
        if args["base"] is None:
            print("Base directory for the website needs to be specified. (Use --help for more information)")
            sys.exit()
        if os.path.isdir(args["base"]) is False:
            print("Base directory " + args["base"] + " does not exist.")
            sys.exit()
        if args["recv"] is None:
            max_recv_bytes = 64 * 1024
        else:
            max_recv_bytes = args["recv"]

        print("\nThe web server has been started.")

        """ STEP 2: CREATE LISTENING PORT """
        # create TCP socket
        try:
            listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error as msg:
            print("ERROR: could not create socket")
            print("Description: " + str(msg))
            sys.exit()

        # bind to listening port
        try:
            host = ""
            listening_socket.bind((host, args["port"]))
        except socket.error as msg:
            print("ERROR: unable to bind for port %d" % args["port"])
            print("Description: " + str(msg))
            sys.exit()

        """ STEP 3: LISTEN FOR CONNECTIONS """
        try:
            backlog = 10
            listening_socket.listen(backlog)
        except socket.error as msg:
            print("ERROR: unable to listen()")
            print("Description: " + str(msg))
            sys.exit()
        # print("Listening to socket bound to port %d" % args["port"])
        listening = True

        """ STEP 4: ACCEPT INCOMING REQUEST AND CREATE NEW THREAD """
        all_thread = []  # list of all threads that have been created

        while listening:
            try:  # accept an incoming request
                (client_s, client_addr) = listening_socket.accept()
            except socket.error as msg:
                print("ERROR: unable to accept()")
                print("Description: " + str(msg))
                sys.exit()

            if args["verbose"]:
                print("Accepted incoming connection from client.")
                print("Client IP, port = %s" % str(client_addr))

            # Create new thread to handle this client connection
            connection_thread = ConnectionThread(client_s, client_addr, max_recv_bytes, args["base"], args["verbose"])
            connection_thread.start()
            all_thread.append(connection_thread)

    except KeyboardInterrupt:  # Capture Ctrl+C Signal
        print("\n\nKeyboard Interrupt Detected:\n\tFinishing all threads and closing web server...")

        # Close listening server
        if listening_socket is not None:
            try:
                listening_socket.close()
            except socket.error as msg:
                print("ERROR: unable to close() listening socket")
                print("Description: " + str(msg))
                sys.exit()

        # allow currently running threads to finish their process
        if all_thread is not None:
            # print("Waiting for all threads to finish...")
            for one_thread in all_thread:
                one_thread.join()
            print("\n\tAll threads have finished and have closed.")
        print("\nThe web server is now closed.\n")

"""
Function:       send()
Parameters:     sock - socket to send data over
                data - data to send through socket
Description:    Sends data over socket, handles if the sendall() function fails
"""
def send(sock, data):
    try:
        bytes_sent = sock.sendall(data)
    except socket.error as msg:
        print("ERROR: sendall() failed")
        print("Description: " + str(msg))
        sys.exit()
    return bytes_sent


if __name__ == "__main__":
    sys.exit(main())
