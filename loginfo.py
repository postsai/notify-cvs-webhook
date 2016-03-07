#!/usr/bin/python

'''
 -- webhook for CVS

@author:     nhnb
@license:    MIT
'''

import sys
import os
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

def escape(data):
    return data.replace("\\", "\\\\").replace("\"", "\\\"")

class CvsReader:
    def __init__(self, args):
        self.meta = {}
        self.commits = []
        self.args = args

    def read_commandline_arguments(self):
        """parse command line arguments"""
        # self.args["default_email_domain"]
        parser = ArgumentParser(description="webhook for CVS commits", formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("--default-email-domain", dest="default_email_domain", action="store", default="example.com", help="email domain to append to account names without @ [default: %(default)s]")
        parser.add_argument("--url", dest="url", action="append", required=True, help="webhook url [default: %(default)s]")
        parser.add_argument("--repository", dest="repository", required=True, help="name of repository")
        parser.add_argument("--home-url", dest="repo_url", help="URL to ViewVC")
        parser.add_argument("--commitid", dest="commitid", required=True, help="commitid CVS variable %%I", metavar="%I")
        parser.add_argument("--folder", dest="folder", required=True, help="folder CVS variable %%p", metavar="%p")
        parser.add_argument(dest="cvsargs", help="file information CVS variable %%{sVv}", metavar="cvsargs", nargs='+')
        args = parser.parse_args()
        
        print(args.default_email_domain)
        print(args.url)
        print(args.repository)
        print(args.repo_url)
        print(args.cvsargs)

    def read_stdin(self):
        """read branch and commit message from stdin"""

        self.meta["branch"] = ""
        message = ""
        wait_for_start_of_message = True
        for line in sys.stdin:
            if wait_for_start_of_message:
                if line.find("Log Message:") == 0:
                    wait_for_start_of_message = False
                elif line.find("      Tag: ") == 0:
                    self.meta["branch"] = line[11:]
            else:
                message += line
        self.meta["message"] = message.strip(' \t\n\r')


    def read_author(self):
        """ reads author from $CVS_USER or $USER"""

        if "CVS_USER" in os.environ:
            full_name = os.environ["CVS_USER"]
        else:
            full_name = os.environ["USER"]

        self.username = full_name

        if full_name.find("@") < 0: 
            full_name = full_name.replace("#", "@")

        if full_name.find("@") < 0:
            full_name = full_name + "@" + self.args["default_email_domain"]

        self.email = full_name
        self.real_name = full_name[0:full_name.find("@")]


    def read(self):
        self.read_commandline_arguments()
        self.read_stdin()
        self.read_author()
        ### TODO: implement me ###

        #self.meta["commitid"]
        #self.meta["module"]
        #self.meta["cvs_repo"]
        #self.meta["html_url"]
        
        #commit["message"]
        #commit["timestamp"]
        # changetype in ("added", "removed", "modified"):
        #revision_map


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
        self.output += "\"timestamp\": \"" + escape(commit["timestamp"]) + "\"},\n" ## TODO "2016-03-06T13:12:42+02:00"
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
            out.write(line)
        out.write("---\n")
        for key in os.environ.keys():
            out.write("%30s %s \n" % (key,os.environ[key]))

if __name__ == "__main__":
    sys.exit(main())