notify-cvs-webhook
-
Github style webhooks for CVS.

notify-cvs-webhook allows you to invoke webhook callbacks on CVS commits.

Setup
-
Checkout your CVSROOT module and add the following line at the end of `loginfo`:

``` bash
ALL /usr/local/notify-cvs-webhook/loginfo.py --url="https://example.com/webhook" 
    --home-url="https://cvs.example.com/cgi-bin/viewvc.cgi" --repository=myrepo 
    --repository-url=":pserver:username:password@cvs.example.com/repository"
    --default-email-domain=example.com --commitid=%I --folder=%p %{sVv}
``` 

|Parameter|Description|
|---|---|
|`url`| ULR of the destination to call|
|`home-url`|The web frontend for the CVS repository|
|`repository`|Name of the repository|
|`repository-url`|(optional) How the repository may be accessed via CVS, should be an readonly account
|`default-email-domain`|This domain is appended to all accounts which do not contain a # or @
|`commitid`|The commitid of the current commit, %I will be replaced by CVS when this script is called
|`folder`|The folder within the repository, %p will be replaced by CVS when this script is called
| | Information about revisions and files, %{sVv} will be replaced by CVS when this script is called


Sample output
-

``` json
{
    "ref": "refs/heads/HEAD",
    "after": "10056E40FB51177B8D0",
    "commits": [
        {
            "id": "10056E40FB51177B8D0",
            "distinct": "true",
            "message": "this is the commit message",
            "timestamp": "2016-03-12T13:46:45",
            "author": {
               "name": "myself",
                "email": "myself@example.com",
                "username": "myself"
            },
            "committer": {
                "name": "myself",
                "email": "myself@example.com",
                "username": "myself"
            },
            "added": [],
            "removed": [],
            "modified": ["mymodule/myfile"],
            "revisions": {
                "mymodule/myfile": "1.9"
            }
        }
    ],
    "head_commit": {
        "id": "10056E40FB51177B8D0",
        "distinct": "true",
        "message": "this is the commit message",
        "timestamp": "2016-03-12T13:46:45",
        "author": {
            "name": "myself",
            "email": "myself@example.com",
            "username": "myself"
        },
        "committer": {
            "name": "myself",
            "email": "myself@example.com",
            "username": "myself"
        },
        "added": [],
        "removed": [],
        "modified": ["mymodule/myfile"],
        "revisions": {
            "mymodule/myfile": "1.9"
        }
    },
    "repository": {
         "name": "local",
         "full_name": "local",
         "home_url": "https://cvs.example.com/viewvc/",
         "url": ":pserver:username:password@cvs.example.com/repository"
    }
}
```

Legal
-
(C) Copyright 2016 Postsai. notify-cvs-webhook is released as Free and Open Source Software under [MIT](https://raw.githubusercontent.com/postsai/postsai/master/LICENSE.txt) license.
