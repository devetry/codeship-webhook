codeship-webhook
================

We would like to add a webhook to all projects we have on Codeship. But, there's no way to do that in bulk via codeship's UI. This script uses their API.

### Caveats

If you have any disabled notifications (see screenshot) this script will turn them back on. Codeship does not expose the `enabled: true/false` attribute of a notification rule, so there's no way to set it back the way it is.

![](https://trello-attachments.s3.amazonaws.com/58d428743111af1d0a20cf28/5b3ff7f5a1c075faacf408a0/4fb1ec123ddc2b2e06280506d02922ec/capture.png)

Also, because Codeship only has PUT and not PATCH, we must put back all attributes we use. What's _more_, they won't let me just echo back the object they gave me&mdash;I must select out specifically the fields that are listed in the API docs. This means if they change their object structure this script will become out of date, and could potentially lose data.

### rocketchat-script.js

I've also included the script I'm using to display notifications in Rocketchat when a webhook arrives. It ends up looking like this:

![](https://trello-attachments.s3.amazonaws.com/58d428743111af1d0a20cf28/5b3ff9fa52a70ed1cd5900d8/c6eb90de31304cdef3ed2413f7a589d5/capture.png)