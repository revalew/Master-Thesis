# Class to build an HTTP response
import json
import os
import gc

try:
    from typing import Union
except ImportError:
    pass


class ResponseBuilder:
    protocol = "HTTP/1.1"
    server = "Pi Pico MicroPython"

    def __init__(self) -> None:
        # set default values
        self.status = 200
        self.content_type = "text/html"
        self.body = ""
        self.response = ""
        gc.enable()

    def set_content_type(self, content_type: str) -> None:
        self.content_type = content_type

    def set_status(self, status: int) -> None:
        self.status = status

    def set_body(self, body: str) -> None:
        self.body = body

    def serve_static_file(
        self, req_filename: str, default_file: str = "./index.html"
    ) -> None:
        # make sure filename starts with /
        if req_filename.find("/") == -1:
            req_filename = "/" + req_filename
        # remove query string
        if req_filename.find("?") != -1:
            req_filename, _ = req_filename.split("?", 1)
        # remove bookmark
        if req_filename.find("#") != -1:
            req_filename, _ = req_filename.split("#", 1)
        # filter out default file
        if req_filename == "/":
            req_filename = default_file
        # break filename into path and filename
        gc.collect()
        path, filename = req_filename.rsplit("/", 1)
        # reinstate root path for listdir
        if len(path) == 0:
            path = "/"
        # print(path, filename)
        # make sure working from root directory
        os.chdir("/")
        # check if file exists
        if filename in os.listdir(path):
            # file found
            # get file type
            _, file_type = filename.rsplit(".", 1)
            if file_type == "htm" or file_type == "html":
                self.content_type = "text/html"
            elif file_type == "js":
                self.content_type = "text/javascript"
            elif file_type == "css":
                self.content_type = "text/css"
            else:
                # let browser work it out
                self.content_type = "text/html"
            gc.collect()
            # file = open("{}/{}".format(path, filename))
            # self.set_body(file.read())
            with open("{}/{}".format(path, filename)) as f:
                self.set_body(f.read())
            # self.set_body(open("{}/{}".format(path, filename)).read())
            gc.collect()
            self.set_status(200)
            gc.collect()
        else:
            # file not found
            self.set_status(404)

    def set_body_from_dict(self, dictionary: dict[str, Union[str, int, float]]) -> None:
        self.body = json.dumps(dictionary)
        self.set_content_type("application/json")

    def build_response(self) -> None:
        gc.collect()
        self.response = ""
        # status line
        self.response += (
            self.__class__.protocol
            + " "
            + str(self.status)
            + " "
            + self.get_status_message()
            + "\r\n"
        )
        # Headers
        self.response += "Server: " + self.server + "\r\n"
        self.response += "Content-Type: " + self.content_type + "\r\n"
        self.response += "Content-Length: " + str(len(self.body)) + "\r\n"
        self.response += "Connection: Closed\r\n"
        self.response += "\r\n"
        # body
        if len(self.body) > 0:
            self.response += self.body

    def get_status_message(self) -> str:
        status_messages = {
            200: "OK",
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
        }
        if self.status in status_messages:
            return status_messages[self.status]
        else:
            return "Invalid Status"
