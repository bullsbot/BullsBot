Bulls Bot
---------

Bulls Bot is a reddit bot that handles automatic creation of game schedules, game threads
and division standings for any given nba subreddit.


Game and Event Schedule
-----------------------

Requires an ics file with both a game schedule and an event schedule. The current settup uses
a team game schedule from espn.com (See 'Export Calendar' on a
`team schedule page <http://espn.go.com/nba/team/schedule/_/name/chi/chicago-bulls>`_)
imported to a google.com calendar with events manually entered. You then supply a link to
the 'Private Address' of the google calendar, more info can be found
`on the support page <https://support.google.com/calendar/answer/37106?hl=en&ref_topic=1672529>`_.
The link is queried at least once every day for updates.


Requirements
------------
* Python 2.7
* `PRAW <https://praw.readthedocs.org/en/v2.1.16/>`_ (Read the Docs)
* `VObject <https://pypi.python.org/pypi/vobject>`_ (PyPi)

