#!/usr/bin/python

'''
 -- webhook for CVS

@author:     nhnb
@license:    MIT
'''

import base64
import datetime
import getopt
import httplib
import os
import subprocess
import sys
import time
import urlparse
import urllib

try:
    from subprocess import DEVNULL # py3k
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


class CvsReader:
    def __init__(self):
        self.meta = {}
        self.commits = []
        self.commits.append({})
        self.urls = []
        self.args = []

    def read_commandline_arguments(self):
        """parse command line arguments"""

        try:
            opts, args = getopt.getopt(sys.argv[1:], "", ["default-email-domain=", "url=", "repository=", "home-url=", "repository-url=", "commitid=", "folder="])
        except:
            print "Invalid command line arguments"
            sys.exit(2)

        self.meta["default_email_domain"] = "example.com"

        for o, a in opts:
            if o == "--default-email-domain":
                self.meta["default_email_domain"] = a
            elif o == "--url":
                self.urls.append(a)
            elif o == "--repository":
                self.meta["repository"] = a
            elif o == "--home-url":
                self.meta["home_url"] = a
            elif o == "--repository-url":
                self.meta["url"] = a
            elif o == "--commitid":
                self.meta["commitid"] = a
            elif o == "--folder":
                self.meta["folder"] = a
        self.args = args


    def read_commitid_legacy_support(self):
        """Very old versions of CVS do not support %I in loginfo.
           This workaround invokes cvs status to get access to the commitid"""
        cvs = subprocess.Popen(["/usr/bin/cvs", "status"], stderr=DEVNULL, stdout=subprocess.PIPE)
        stdout = cvs.communicate()[0];
        for row in stdout.splitlines():
            if "Commit Identifier:" in row:
                self.meta["commitid"] = row.rsplit(None, 1)[-1]
                return

        self.meta["commitid"] = "S" + str(time.time()) + os.urandom(4).encode("hex")


    def read_stdin(self):
        """read branch and commit message from stdin"""

        self.meta["branch"] = "HEAD"
        message = ""
        wait_for_start_of_message = True
        for line in sys.stdin:
            if wait_for_start_of_message:
                if line.find("Log Message:") == 0:
                    wait_for_start_of_message = False
                elif line.find("      Tag: ") == 0:
                    self.meta["branch"] = line[11:].strip(' \t\n\r')
            else:
                message += line
        self.meta["message"] = message.strip(' \t\n\r')


    def read_author(self):
        """ reads author from $CVS_USER or $USER"""

        if "CVS_USER" in os.environ:
            full_name = os.environ["CVS_USER"]
        else:
            full_name = os.environ["USER"]

        self.meta["username"] = full_name

        if full_name.find("@") < 0: 
            full_name = full_name.replace("#", "@")

        if full_name.find("@") < 0:
            full_name = full_name + "@" + self.meta["default_email_domain"]

        self.meta["email"] = full_name
        self.meta["real_name"] = full_name[0:full_name.find("@")]

    def build_file_lists(self):
        commit = self.commits[0]
        commit["added"] = []
        commit["removed"] = []
        commit["modified"] = []
        commit["revisions"] = {}

        while len(self.args) > 0:
            filename = self.meta["folder"] + "/" + self.args.pop(0)
            old = self.args.pop(0)
            new = self.args.pop(0)
            if old == new and new == "NONE":
                continue
            if old == "NONE":
                commit["added"].append(filename)
                commit["revisions"][filename] = new
            elif new == "NONE":
                commit["removed"].append(filename)
                commit["revisions"][filename] = "" # todo
            else:
                commit["modified"].append(filename)
                commit["revisions"][filename] = new

    def build_commit(self):
        self.commits[0]["commitid"] = self.meta["commitid"]
        self.commits[0]["message"] = self.meta["message"]
        self.commits[0]["timestamp"] = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


    def read(self):
        self.read_commandline_arguments()
        if not "commitid" in self.meta:
            self.read_commitid_legacy_support()
        self.read_stdin()
        self.read_author()
        self.build_file_lists()
        self.build_commit()


class OutputGenerator:
    """Generates the payload"""


    def __init__(self, meta, commits):
        self.meta = meta
        self.commits = commits
        self.output = ""

    def write(self):
        self.write_header()
        self.write_commits()
        self.write_repository()
        self.write_footer()

    def write_header(self):
        self.output += "{\n"
        self.output += "\"ref\": \"refs/heads/" + urllib.quote(self.meta["branch"]) + "\",\n"
        self.output += "\"after\": \"" + urllib.quote(self.meta["commitid"]) + "\",\n"

    def write_user(self):
        self.output += "{\n"
        self.output += "\"name\": \"" + urllib.quote(self.meta["real_name"]) + "\",\n"
        self.output += "\"email\": \"" + urllib.quote(self.meta["email"]) + "\",\n"
        self.output += "\"username\": \"" + urllib.quote(self.meta["username"]) + "\"\n"
        self.output += "},\n"

    def write_file_list(self, files):
        self.output += "["
        first = True
        for filename in files:
            if first:
                first = False
            else:
                self.output += ", "
            self.output += "\"" + urllib.quote(filename) + "\""
        self.output += "],"

    def write_revision_map(self, commit):
        self.output += "{"
        first = True
        for filename, revision in commit["revisions"].items():
            if first:
                first = False
            else:
                self.output += ","
            self.output += "\"" + urllib.quote(filename) + "\": \"" + urllib.quote(revision) + "\"\n"
        self.output += "}"

    def write_commit(self, commit):
        self.output += "{\n"
        self.output += "\"id\": \"" + urllib.quote(commit["commitid"]) + "\",\n"
        self.output += "\"distinct\": \"true\",\n"
        self.output += "\"message\": \"" + urllib.quote(commit["message"]) + "\",\n"
        self.output += "\"timestamp\": \"" + urllib.quote(commit["timestamp"]) + "\",\n"
        self.output += "\"author\": "
        self.write_user()
        self.output += "\"committer\": "
        self.write_user()

        for changetype in ("added", "removed", "modified"):
            self.output += "\"" + changetype + "\": "
            self.write_file_list(commit[changetype])
            self.output += "\n"
        self.output += "\"revisions\": "
        self.write_revision_map(commit)
        self.output += "\n"
        self.output += "}\n"

    def write_commits(self):
        self.output += "\"commits\": [\n"
        for commit in self.commits:
            self.write_commit(commit)
        self.output += "],\n"
        self.output += "\"head_commit\":\n"
        self.write_commit(self.commits[0])
        self.output += ",\n"

    def write_repository(self):
        self.output += "\"repository\": {\n"
        self.output += "\"name\": \"" + urllib.quote(self.meta["repository"]) + "\",\n"
        self.output += "\"full_name\": \"" + urllib.quote(self.meta["repository"]) + "\",\n"
        self.output += "\"home_url\": \"" + urllib.quote(self.meta["home_url"]) + "\",\n"
        self.output += "\"url\": \"" + urllib.quote(self.meta["url"]) + "\"\n"
        self.output += "}\n"

    def write_footer(self):
        self.output += "}\n"


def main(argv=None):
    '''Command line entry point'''

    reader = CvsReader()
    reader.read()
    
    output = OutputGenerator(reader.meta, reader.commits)
    output.write()

    for url in reader.urls:
        u = urlparse.urlparse(url)

        # Connect to server
        if u.scheme == "https":
            con = httplib.HTTPSConnection(u.hostname, u.port)
        else:
            con = httplib.HTTPConnection(u.hostname, u.port)

        # Send request
        headers = {"Content-Type": "application/json"}
        if not u.username == None and not u.password == None:
            headers["Authorization"] = "Basic " + base64.b64encode(u.username + ":" + u.password)
        url_prefix = u.scheme + "://" + u.hostname + u.path
        if u.query != "":
            url_prefix = url_prefix + "?" + u.query
        con.request("POST", url_prefix, output.output, headers)

        # Verify response
        response = con.getresponse()
        if response.status != 200:
            print(str(response.status) + " " + response.reason)
            sys.exit(1)



if __name__ == "__main__":
    sys.exit(main())
