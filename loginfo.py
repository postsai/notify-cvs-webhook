#!/usr/bin/python

'''
 -- webhook for CVS

@author:     nhnb
@license:    MIT
'''

import sys
import os

def escape(data):
    return data.replace("\\", "\\\\").replace("\"", "\\\"")

class CvsReader:
    def __init__(self):
        self.meta = {}
        self.commits = []

    ### TODO: implement me ###

class OutputGenerator:
    def __init__(self, meta, commits):
        self.meta = meta
        self.commits = commits
        self.ouptput = ""

    def write(self):
        self.write_header()
        self.write_commits()
        self.write_repository()
        self.write_footer()

    def write_header(self):
        self.output += "{\n"
        self.output += "\"ref\": \"refs/heads/" + escape(self.meta["tag"]) + "\"},\n"
        self.output += "\"after\": \"" + escape(self.meta["commitid"]) + "\"},\n"

    def write_user(self):
        self.output += "{\n"
        self.output += "\"name\": \"" + escape(self.meta["real_name"]) + "\"},\n"
        self.output += "\"email\": \"" + escape(self.meta["email"]) + "\"},\n"
        self.output += "\"username\": \"" + escape(self.meta["username"]) + "\"}\n"
        self.output += "},\n"

    def write_file_list(self, files):
        self.output += "["
        first = True
        for filename in files:
            if first:
                first = False
            else:
                self.output += ", "
            self.output += "\"" + escape(filename) + "\""
        self.output += "],"

    def write_revision_map(self, commit):
        self.output += "{"
        for filename, revision in commit.revisions:
            self.output += "\"" + escape(filename) + "\": \"" + escape(revision) + "\",\n"
        self.output += "},"

    def write_commit(self, commit):
        self.output += "{\n"
        self.output += "\"id\": \"" + escape(commit["commitid"]) + "\"},\n"
        self.output += "\"distinct\": \"true\"},\n"
        self.output += "\"message\": \"" + escape(commit["message"]) + "\"},\n"
        self.output += "\"timestamp\": \"" + escape(commit[""]) + "\"},\n" ## TODO "2016-03-06T13:12:42+02:00"
        self.output += "\"author\": " + self.write_user()
        self.output += "\"committer\": " + self.write_user()

        for changetype in ("added", "removed", "modified"):
            self.output += "\"" + changetype + "\": \"" + self.write_file_list(commit["files"][changetype])
        self.output += "\"revisions\": " + self.write_revision_map(commit)
        self.output += "},\n"

    def write_commits(self):
        self.output += "\"commits\": [\n"
        for commit in self.commits:
            self.write_commit(commit)
        self.output += "],\n"
        self.output += "\"head_commit\":\n"
        self.write_commit(self.commits[0])

    def write_repository(self):
        self.output += "\"repository\": {\n"
        self.output += "\"name\": \"" + escape(self.meta["module"]) + "\",\n"
        self.output += "\"full_name\": \"" + escape(self.meta["cvs_repo"] + "/" + self.meta["module"]) + "\",\n"
        self.output += "\"html_url\": \"" + escape(self.meta["html_url"]) + "\",\n"
        self.output += "\"url\": \"" + escape(self.meta["html_url"]) + "\"\n"
        self.output += "}\n"

    def write_footer(self):
        self.output += "}\n"


def main(argv=None):
    '''Command line options.'''

    ### TODO: implement command line argument parser

    with open("/tmp/out", "a") as out:
        out.write("------------------------\n")
        out.write(" ".join(sys.argv)+ "\n")
        for line in sys.stdin:
            out.write(line + "\n")
        out.write("---\n")
        for key in os.environ.keys():
            out.write("%30s %s \n" % (key,os.environ[key]))

if __name__ == "__main__":
    sys.exit(main())