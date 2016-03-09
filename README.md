Status: Early development
-

*not useable, yet*


notify-cvs-webhook
-
Github style webhooks for CVS.

notify-cvs-webhook allows you to invoke webhook callbacks on CVS commits.

Setup
-
Checkout your CVSROOT module and add the following line at the end of loginfo:

``` bash
ALL /usr/local/notify-cvs-webhook/loginfo.py --url="https://example.com/webhook" --repository=myrepo --default-email-domain=example.com --commitid=%I --folder=%p %{sVv}
``` 

