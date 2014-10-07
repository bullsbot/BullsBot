__version__ = '0.0.1'

from datetime import datetime
import time
import vobject
import pytz
import urllib2
import praw
from random import randrange
import nba_game_scraper


class game_thread_links(object):
    """ Object containing links to game thread links
    """
    def __init__(self, pre=None, pre_id=None, game=None, game_id=None, post=None, post_id=None):
        self.pre = pre              # link to pregame thread
        self.pre_id = pre_id        # reddit id of pregame thread
        self.game = game            # link to game thread
        self.game_id = game_id      # reddit id of game thread
        self.post = post            # link to postgame thread
        self.post_id = post_id      # reddit id of postgame thread


class bulls_bot(object):
    """ Reddit bot that handles updating the sidebar and game-threads periodically
    """

    def __init__(self, username=None, password=None, subreddit=None):
        # username
        if username is None:
            self.username = raw_input('Reddit Username: ')
        else:
            self.username = username
        # password
        if password is None:
            self.password = raw_input('Reddit Password: ')
        else:
            self.password = password
        # sub
        if subreddit is None:
            self.subreddit = raw_input('Subreddit (e.g. chicagobulls, not /r/chicagobulls): ')
        else:
            self.subreddit = subreddit

        self.reddit = None
        self.userAgent = 'NBA_Sub_Bot/v0.0.1 by ' + self.username
        # calendar link(s)
        self.calendarURL = raw_input('Calendar URL (leave empty to use default): ')
        if self.calendarURL is None or self.calendarURL.strip() == '':
            print 'using default calendar url'
            self.calendarURL = "https://www.google.com/calendar/ical/chicagobullsbot%40gmail.com/private-48b0043bc03da315706a2ca595c0e63b/basic.ics"
        self.no_date_flag = "#NODATE"
        # team data
        self.teamName = "Chicago Bulls"
        self.teamInfoFilePath = "data/teams.csv"
        # load team data
        self.load_teams()
        # gameday info
        self.game_day_info = None
        self.last_game_day_check = datetime.min
        # game thread links (key is date, value is game_thread_links object)
        self.game_thread_links = {}
        # update frequencies
        self.non_game_day_upate_freq = 60 * 60 * 10    # every 10 hours on non-game days
        self.game_day_upate_freq = 60 * 60             # every hour on game days
        self.near_game_upate_freq = 60 * 5             # every 5 minutes as we approach game time
        self.game_time_upate_freq = 60 * 1.5           # every 1.5 minutes once the game has started
        self.game_thread_create_time = 60 * 60         # how many seconds before tip-off should game threads be created
        # schedule template
        self.sidebar_schedule_start_string = "* **Schedule**"
        self.sidebar_schedule_end_string = "\n\n"
        # schedule markdown formats
        self.event_fmt = "[{event_title}]({event_hashtag}) [{month_day}](#DESC)\n"
        self.past_game_fmt =    "[{game_status}](#STATUS) [{away_team_short}](#TEAM) [{away_score}](#SCORE) [{home_team_short}](#TEAM2) [{home_score}](#SCORE2) [{month_day}](#DATE)\n"
        self.current_game_fmt = "[{game_status}](#STATUS) [{away_team_short}](#TEAM) [{away_score}](#SCORE) [{home_team_short}](#TEAM2) [{home_score}](#SCORE2) [{month_day}](#DATE)\n"
        self.future_game_fmt =  "[{game_time_local}](#STATUS) [{away_team_short}](#TEAM) [](#SCORE) [{home_team_short}](#TEAM2) [](#SCORE2) [{month_day}](#DATE)\n"
        self.game_thread_link_fmt = "[]({link})"
        self.event_markdown_pre = " - "  # goes before each game/event
        self.event_markdown_post = ""    # goes after each game/event
        # thread markdown formats
        self.post_game_thread_fmt = "HOME TEAM|FINAL SCORE|AWAY TEAM\n:--:|:--:|:--:\n[](#{home_team_short}){home_team_name}*{home_team_win_loss}*|**{home_score}-{away_score}** *{full_date}* *[BOX SCORE](http://www.nba.com/games/{link_date}/{away_team_short}{home_team_short}/gameinfo.html#nbaGIboxscore)*|[](#{away_team_short}){away_team_name}*{away_team_win_loss}*\n"
        self.post_game_thread_title_fmt = "POST GAME: {sub_team_name} ({sub_team_win_loss}) {beat_or_lose} {non_sub_team_name} ({non_sub_team_win_loss}) ({final_score})"
        self.pre_game_thread_fmt = "HOME TEAM|INFORMATION|AWAY TEAM\n:--:|:--:|:--:\n[](#{home_team_short}){home_team_name}*{home_team_win_loss}*|*{full_date}*|[](#{away_team_short}){away_team_name}*{away_team_win_loss}*\n\n[](#empty)|DETAILED OVERVIEW|[](#empty)\n:--|:--|:--\n[](#empty)|*BROADCAST* {broadcast}|[](#empty)\n[](#empty)|*GAME TIMES* [Eastern: {eastern_time}](#TIME) / [Central: {central_time}](#TIME) / [Mountain: {mountain_time}](#TIME) / [Pacific:  {pacific_time}](#TIME)|[](#empty)\n[](#empty)|*MISC/NOTES* [Game Story](#http://www.nba.com/games/{link_date}/{away_team_short}{home_team_short}/gameinfo.html)|[](#empty)\n[](#empty)|*SUBREDDITS* /r/{home_subreddit} / /r/{away_subreddit}|[](#empty)\n"
        self.pre_game_thread_title_fmt = "PRE GAME: {home_team_name} ({home_team_win_loss}) vs. {away_team_name} ({away_team_win_loss}) ({month_day_year})"
        self.current_game_thread_fmt = "HOME TEAM|GAME THREAD|AWAY TEAM\n:--:|:--:|:--:\n[](#{home_team_short}){home_team_name}*{home_team_win_loss}*|**{home_score}-{away_score}** *VERSUS* *[BOX SCORE](http://www.nba.com/games/{link_date}/{away_team_short}{home_team_short}/gameinfo.html#nbaGIboxscore)*|[](#{away_team_short}){away_team_name}*{away_team_win_loss}*\n[](#empty)|*Eastern* **{game_time_eastern}**|[](#empty)\nSubreddit|*Central* **{game_time_central}**|Subreddit\n/r/{home_subreddit}|*Mountain* **{game_time_mountain}**|/r/{away_subreddit}\n[](#empty)|*Pacific* **{game_time_pacific}**|[](#empty)\n\n"
        self.current_game_thread_split_text = "[](#empty)|INFORMATION"
        self.current_game_thread_post_text = "[](#empty)|INFORMATION|[](#empty)\n:--|:--|:--\n[](#empty)|*BROADCAST* |[](#empty)\n[](#empty)|*STREAMS* |[](#empty)\n[](#empty)|*DISCUSS* [Reddit Steam](http://reddit-stream.com/)|[](#empty)\n"
        self.game_thread_title_fmt = "GAME THREAD: {home_team_name} ({home_team_win_loss}) vs. {away_team_name} ({away_team_win_loss}) ({month_day_year})"
        self.game_thread_title_date_fmt = "%b %d, %Y"
        self.game_thread_flair = 'gamethread'
        self.pregame_thread_flair = 'pregame'
        self.postgame_thread_flair = 'postgame'
        # check that the username and password work, if not die now!
        if not self.authenticate_reddit():
            print "Could not login to reddit with " + self.username
            raise praw.errors.LoginRequired("bulls_bot")

    def authenticate_reddit(self):
        """
        checks if logged in and if not, logs in for us. returns false if we couldn't log in
        """
        authenticated = False
        try:
            if self.reddit is None:
                #Initiate PRAW
                self.reddit = praw.Reddit(user_agent=self.userAgent)
                self.reddit.config.decode_html_entities = True

            if not self.reddit.is_logged_in():
                #Log in to Reddit
                self.reddit.login(self.username, self.password)

            authenticated = True
        except:
            authenticated = False
        return authenticated

    def get_cal(self):
        """ get calendar from url
        """
        calendarContent = urllib2.urlopen(self.calendarURL).read()
        cal = vobject.readOne(calendarContent)
        return cal

    def load_teams(self):
        # load team info
        self.team_dict = {}
        self.team_dict_short_key = {}
        with open(self.teamInfoFilePath, "r") as teamInfoFile:
            for teamInfoRow in teamInfoFile.read().split("\n"):
                teamInfo = teamInfoRow.split(',')
                self.team_dict[teamInfo[0]] = {
                    'long_name': teamInfo[0],
                    'short_name': teamInfo[1].upper(),
                    'sub': teamInfo[2],
                    'timezone': teamInfo[3]
                }
                self.team_dict_short_key[teamInfo[1].upper()] = {
                    'long_name': teamInfo[0],
                    'short_name': teamInfo[1].upper(),
                    'sub': teamInfo[2],
                    'timezone': teamInfo[3]
                }

    def is_game_vevent(self, vevent):
        # simple and stupid for now
        # return vevent.summary.valueRepr().find(self.event_flag) == -1
        return vevent.summary.valueRepr().find('#') == -1

    def load_gameday_info(self):
        # todo: create gameday_info class
        local_timezone = pytz.timezone(self.team_dict[self.teamName]['timezone'])
        current_local_datetime = datetime.now(local_timezone)
        current_local_date = current_local_datetime.date()
        cal = self.get_cal()
        is_game_day = False
        for event in cal.vevent_list:
            if self.is_game_vevent(event):
                local_game_time = event.dtstart.value.astimezone(local_timezone)
                if local_game_time.date() == current_local_date:
                    is_game_day = True
                    self.game_day_info = {
                        "local_game_time": local_game_time,
                        "game_vevent": event
                    }
                    break
        # reset to none if it's not a gameday
        if not is_game_day:
            self.game_day_info = None
        # log that we just checked
        self.last_game_day_check = current_local_datetime

    def get_seconds_till_game(self):
        local_timezone = pytz.timezone(self.team_dict[self.teamName]['timezone'])
        current_local_datetime = datetime.now(local_timezone)
        if self.is_today_a_game_day():
            return (self.game_day_info['local_game_time'] - current_local_datetime).total_seconds()
        # todo return actual secs till game even if it's not a game-day
        return 10000000000

    def is_the_game_on_now(self):
        local_timezone = pytz.timezone(self.team_dict[self.teamName]['timezone'])
        current_local_datetime = datetime.now(local_timezone)
        is_game_live = False
        if self.is_today_a_game_day():
            minutes_till_tipoff = (self.game_day_info['local_game_time'] - current_local_datetime).total_seconds() / 60
            # if we're checking in the first half hour or so, assume it's on
            if -30 < minutes_till_tipoff <= 0:
                is_game_live = True
            else:
                games = nba_game_scraper.get_games(current_local_datetime, 30)   # thirty second cache
                live_game_on = False
                # key is like CHI_SAS, value is a dict with game data
                for key, value in games.iteritems():
                    if key.find(self.team_dict[self.teamName]['short_name']) is not -1 and value['current_status'] == 'LIVE':
                        live_game_on = True
                        break
                if live_game_on:
                    is_game_live = True

        return is_game_live

    def is_it_near_game_time(self):
        local_timezone = pytz.timezone(self.team_dict[self.teamName]['timezone'])
        current_local_datetime = datetime.now(local_timezone)
        is_near_game_time = False
        if self.is_today_a_game_day():
            minutes_till_tipoff = (self.game_day_info['local_game_time'] - current_local_datetime).total_seconds() / 60
            if 0 < minutes_till_tipoff < 20:
                is_near_game_time = True

        return is_near_game_time

    def is_today_a_game_day(self):
        is_game_day = False
        local_timezone = pytz.timezone(self.team_dict[self.teamName]['timezone'])
        current_local_date = datetime.now(local_timezone).date()
        if self.game_day_info is not None:
            if self.last_game_day_check.date() == current_local_date:
                is_game_day = True
            else:
                self.load_gameday_info()
                is_game_day = self.game_day_info is not None
        elif self.last_game_day_check.date() != current_local_date:
            self.load_gameday_info()
            is_game_day = self.game_day_info is not None

        return is_game_day

    def all_schedule_maker(self):
        return self.schedule_maker()

    def schedule_maker(self, startDate=datetime(2013, 1, 1), endDate=datetime(2025, 1, 1), max_events=100):
        """
        make schedule for a date range and max number of events
        :param startDate: earliest possible event date (defaults to Jan 1 2013)
        :param endDate: latest possible event date (defaults to Jan 1 2025)
        :param max_events: maximum number of events to display
        """
        if startDate is None:
            startDate = datetime(2013, 1, 1)

        # load game schedule
        cal = self.get_cal()
        cal_timezone = pytz.timezone(cal.contents['x-wr-timezone'][0].value)
        # sort games
        # todo: double check that this works properly if each event/game is in a different timezone
        events = sorted(cal.vevent_list, key=lambda vevent: vevent.dtstart.value if (type(vevent.dtstart.value) is datetime) else datetime(vevent.dtstart.value.year, vevent.dtstart.value.month, vevent.dtstart.value.day, tzinfo=cal_timezone))
        # events = sorted(cal.vevent_list, key=attrgetter('dtstart.value'))

        # localize times
        local_timezone = pytz.timezone(self.team_dict[self.teamName]['timezone'])
        if startDate.tzinfo is None:
            local_start_date = local_timezone.localize(startDate, is_dst=None)
        else:
            local_start_date = startDate.astimezone(local_timezone)

        if endDate.tzinfo is None:
            local_end_date = local_timezone.localize(endDate, is_dst=None)
        else:
            local_end_date = startDate.astimezone(local_timezone)
        # loop through events
        events_added_to_schedule = 0
        schedule_as_string = ''
        for event in events:
            if type(event.dtstart.value) is datetime:
                localGameTime = event.dtstart.value.astimezone(local_timezone)
            else:
                # create new datetime with the date and give it the local timezone
                # (if we were to use the calendars timezone and then convert it to local time, we could potentially change the date)
                localGameTime = datetime(event.dtstart.value.year, event.dtstart.value.month, event.dtstart.value.day, tzinfo=local_timezone)
            if local_start_date < localGameTime < local_end_date:
                if self.is_game_vevent(event):
                    # get game formatted to proper markdown
                    game_as_formatted_schedule_str = self.format_game(event, local_timezone)
                    if game_as_formatted_schedule_str != '':
                        schedule_as_string += \
                            self.event_markdown_pre + \
                            self.get_game_thread_link_as_formatted_string(localGameTime) + \
                            game_as_formatted_schedule_str + \
                            self.event_markdown_post
                        events_added_to_schedule += 1
                else:
                    # get nba event formatted to proper markdown
                    event_as_formatted_schedule_str = self.format_event(event, local_timezone)
                    if event_as_formatted_schedule_str != '':
                        schedule_as_string += \
                            self.event_markdown_pre + \
                            event_as_formatted_schedule_str + \
                            self.event_markdown_post
                    events_added_to_schedule += 1
                # stop adding events once we reach the max
                if events_added_to_schedule >= max_events:
                    break
        return schedule_as_string

    def format_event(self, event, timezone):
        date_format = "%b %d"
        day_format = "%d"
        short_date_format = "%m/%d"
        summary = event.summary.valueRepr().upper()

        if type(event.dtstart.value) is datetime:
            local_date_time = event.dtstart.value.astimezone(timezone)
            local_end_date_time = event.dtend.value.astimezone(timezone)
        else:
            # create new datetime with the date and give it the local timezone
            # using the calendar's timezone converting to local time would potentially change the date
            local_date_time = datetime(event.dtstart.value.year, event.dtstart.value.month, event.dtstart.value.day,
                                       tzinfo=timezone)
            local_end_date_time = datetime(event.dtend.value.year, event.dtend.value.month, event.dtend.value.day,
                                           tzinfo=timezone)

        if local_date_time.year == local_end_date_time.year and local_date_time.month == local_end_date_time.month and \
                        local_date_time.day == local_end_date_time.day:
            # if start and end dates are on the same day
            month_day = local_date_time.strftime(date_format).upper()
        else:
            # if the start and end dates are on different days in same month
            if local_date_time.year == local_end_date_time.year and local_date_time.month == local_end_date_time.month:
                month_day = local_date_time.strftime(date_format).upper() + '-' + local_end_date_time.strftime(day_format)
            # if they are in two different months
            else:
                month_day = local_date_time.strftime(short_date_format) + '-' + local_end_date_time.strftime(short_date_format)
        title_and_hashtag = summary.replace(self.no_date_flag, '').split(' #')
        title = title_and_hashtag[0].strip()
        try:
            hashtag = "#" + title_and_hashtag[1].strip()
        except IndexError:
            hashtag = "#"

        if summary.find(self.no_date_flag) is not -1:
            month_day = '-'

        return self.event_fmt.format(event_title=title, event_hashtag=hashtag, month_day=month_day)

    def format_game(self, game, timezone):
        date_format = "%b %d"
        time_format = "%I:%M %p"
        # if startDate <= game.dtstart.value <= endDate:
        chiDateTime = game.dtstart.value.astimezone(timezone)
            # print game.summary.valueRepr()
        month_day = chiDateTime.strftime(date_format).upper().replace(" 0", " ")
        game_time_local = chiDateTime.strftime(time_format)
        # Get Summary
        print 'Summary: ', game.summary.valueRepr()
        print 'Location: ', game.location.valueRepr()
        home_and_away_teams = game.summary.valueRepr().split(" at ")
        away_team = home_and_away_teams[0]
        away_team_short = self.team_dict[away_team]['short_name']
        home_team = home_and_away_teams[1]
        home_team_short = self.team_dict[home_team]['short_name']
        # get real scores
        # scores = get_scores(chiDateTime)
        if chiDateTime.date() <= datetime.now(timezone).date():
            # if the game is today or has passed, get the game info
            games_data = nba_game_scraper.get_games(chiDateTime)
            try:
                game_data = games_data[away_team_short + '_' + home_team_short]
            except KeyError:
                # this happens when we have a game in the game calendar but nba.com doesn't have it listed
                # todo: log error or warn
                print 'WARNING: could not find game data for ' + away_team_short + '_' + home_team_short + ' on ' + month_day
                return ''
        else:
            # otherwise, skip scrapping the game info
            game_data = {
                'current_status': 'PRE'
            }

        has_scores = True
        try:
            home_score = game_data['home_score']
            away_score = game_data['away_score']
            #
            home_format = '**{0}**' if (int(home_score) > int(away_score)) else '{0}'
            away_format = '**{0}**' if (int(home_score) < int(away_score)) else '{0}'
        except KeyError:
            has_scores = False
        except TypeError:
            has_scores = False
        # todo: find a better place for this
        self.last_game_status = game_data['current_status']
        if has_scores and (game_data['current_status'] == "RECAP" or game_data['current_status'] == "RECAPOT"):

            return self.past_game_fmt.format(game_status=game_data['game_status'].upper(),
                                             game_time_local=game_time_local,
                                             home_team_short=home_format.format(home_team_short),
                                             away_team_short=away_format.format(away_team_short),
                                             home_score=home_format.format(home_score),
                                             away_score=away_format.format(away_score),
                                             month_day=month_day)
        elif game_data['current_status'] == "PPD":
            return self.past_game_fmt.format(game_status=game_data['current_status'].upper(),
                                             game_time_local=game_time_local,
                                             home_team_short=home_team_short,
                                             away_team_short=away_team_short,
                                             home_score="",
                                             away_score="",
                                             month_day=month_day)
        elif has_scores and game_data['current_status'] == "LIVE":
            return self.current_game_fmt.format(game_status=game_data['game_status'].upper(),
                                                game_time_local=game_time_local,
                                                home_team_short=home_format.format(home_team_short),
                                                away_team_short=away_format.format(away_team_short),
                                                home_score=home_format.format(home_score),
                                                away_score=away_format.format(away_score),
                                                month_day=month_day)
        elif game_data['current_status'].strip() == "PRE":
            return self.future_game_fmt.format(game_time_local=game_time_local,
                                               home_team_short=home_team_short,
                                               away_team_short=away_team_short,
                                               month_day=month_day)
        else:
            return self.future_game_fmt.format(game_time_local=game_data['current_status'],
                                               home_team_short=home_team_short,
                                               away_team_short=away_team_short,
                                               month_day=month_day)

    def get_current_update_freq(self):
        """
        returns the amount of time to sleep until updating again (in seconds)
        """
        current_update_freq = self.non_game_day_upate_freq
        if self.is_today_a_game_day():
            todays_game_thread_links = self.get_game_thread_links_for_date(datetime.now())
            if self.is_the_game_on_now():
                # if the game is on now, update at the game time update frequency
                current_update_freq = self.game_time_upate_freq
            # todo: add 'pre' and 'post' game threads
            elif (todays_game_thread_links is None or todays_game_thread_links.game is None) \
                    and self.get_seconds_till_game() > - 1:
                # if there's no game thread and the game hasn't started
                # update when the game thread is supposed to get created
                current_update_freq = self.get_seconds_till_game() - self.game_thread_create_time
            else:
                # there is a gamethread so update when the game is about to start
                current_update_freq = self.get_seconds_till_game()
                # if it already passed, and the game isn't on now, it must be over
                if current_update_freq < 0:
                    # go back to game day update frequency
                    current_update_freq = self.game_day_upate_freq

        return max(current_update_freq, 0)

    def generate_default_schedule(self):
        print "generating default schedule"
        self.max_events_to_display = 16
        self.prior_events_to_display = 3
        self.min_events_to_display = 10
        begin_date = None
        # find date to begin schedule with
        cal = self.get_cal()
        local_timezone = pytz.timezone(self.team_dict[self.teamName]['timezone'])
        cal_timezone = pytz.timezone(cal.contents['x-wr-timezone'][0].value)
        # for vevent in cal.vevent_list:
        #     print vevent.dtstart.value
        events = sorted(cal.vevent_list, key=lambda vevent: vevent.dtstart.value if (type(vevent.dtstart.value) is datetime) else datetime(vevent.dtstart.value.year, vevent.dtstart.value.month, vevent.dtstart.value.day, tzinfo=cal_timezone), reverse=True)
        # events = sorted(cal.vevent_list, key=attrgetter('dtstart.value'), reverse=True)
        current_local_date = datetime.now(local_timezone).date()
        prior_events = 0
        total_events = 0
        for event in events:
            total_events += 1
            if type(event.dtstart.value) is datetime:
                local_event_date = event.dtstart.value.astimezone(local_timezone).date()
            else:
                local_event_date = event.dtstart.value

            if local_event_date < current_local_date:
                prior_events += 1
                if prior_events >= self.prior_events_to_display and total_events >= self.min_events_to_display:
                    if type(event.dtstart.value) is datetime:
                        begin_date = event.dtstart.value.astimezone(local_timezone)
                    else:
                        # create new datetime with the date and give it the local timezone
                        # (if we were to use the calendars timezone and then convert it to local time, we could potentially change the date)
                        begin_date = datetime(event.dtstart.value.year, event.dtstart.value.month, event.dtstart.value.day, tzinfo=local_timezone)
                    break

        return self.schedule_maker(startDate=begin_date, max_events=self.max_events_to_display)

    def update_schedule(self, schedule=None):
        print "begin updating schedule ... "
        if schedule is None:
            schedule = self.generate_default_schedule()
        # make sure we're logged in (and if not, log in)
        if self.authenticate_reddit():
            #Get the sidebar
            # settings=r.get_settings(self.team_dict[self.teamName]['sub'])
            print "fetching subreddit settings"
            settings = self.reddit.get_settings(self.subreddit)
            description_markup = settings['description']
            print "updating subreddit settings with schedule"
            before_sched_start = description_markup.split(self.sidebar_schedule_start_string, 1)[0]
            after_sched_start = description_markup.split(self.sidebar_schedule_start_string, 1)[1]
            after_sched_end = after_sched_start.split(self.sidebar_schedule_end_string, 1)[1]
            settings['description'] = before_sched_start + self.sidebar_schedule_start_string + "\n" + schedule + \
                                    self.sidebar_schedule_end_string + after_sched_end
            settings = self.reddit.get_subreddit(self.subreddit).update_settings(description=settings['description'])
            local_timezone = pytz.timezone(self.team_dict[self.teamName]['timezone'])
            formated_time = datetime.now(local_timezone).strftime("%I:%M %p")
            responses = ["Thibs would be proud of this hustle! Updated that schedy sched for u at around ", "Schedy sched updated ", "1000010010101000101001 at ", "Ok, just updated at ", "What it is, just updated at ", "Boom, did it at ", "Puttin in work sukka! Just updated that schedule at ", "Yoooooooooo.... did it again at ", "Knock knock. (Who's there?) BULLS BOT PUTTIN IN WORK! ... at ", " Yaawwn, got anything else for me to do? ... just updated again at ", "Guess what I just did at ", "Beep Boop Bop Beep Booop at "]
            response = responses[randrange(len(responses))]
            print '[In /r/' + self.subreddit + '] ' + response + formated_time
        else:
            print "could not authenticate through reddit"

    def add_game_thread_links(self, gtl):
        """
        adds a game_thread_links object to self.game_thread_links dict with today's date as a key
        """
        key_date_format = "%Y%m%d"
        key = datetime.now().strftime(key_date_format)
        self.game_thread_links[key] = gtl

    def get_game_thread_links_for_date(self, date):
        key_date_format = "%Y%m%d"
        key = date.strftime(key_date_format)
        game_thread = None
        if key in self.game_thread_links:
            game_thread = self.game_thread_links[key]
        # todo: query the sub for posts on date with proper flair
        return game_thread

    def get_game_thread_link_as_formatted_string(self, date):
        """
        returns an empty string or, if it exists, a game thread url formated as defined in game_thread_link_fmt
        """
        formatted_string = ''
        game_thread_links = self.get_game_thread_links_for_date(date)
        if game_thread_links is not None and game_thread_links.game is not None:
            formatted_string = self.game_thread_link_fmt.format(link=game_thread_links.game)
        return formatted_string

    def need_to_create_pregame_thread(self):
        """
        returns true if it's a game-day and there is no game_thread.pre link.
        """
        game_thread_links = self.get_game_thread_links_for_date(datetime.now())
        return self.is_today_a_game_day() \
            and (game_thread_links is None
                 or (game_thread_links is not None and game_thread_links.pre is None))

    def need_to_create_game_thread(self):
        """
        returns true if it's a game-day and the game hasn't started and it's within an hour to game-time
        and there is no game_thread.game link.
        """
        game_thread_links = self.get_game_thread_links_for_date(datetime.now())
        return self.is_today_a_game_day() \
            and -1 < self.get_seconds_till_game() < self.game_thread_create_time \
            and (game_thread_links is None
                 or (game_thread_links is not None and game_thread_links.game is None))

    def post_new_or_update_game_thread(self, game_thread_markup, game_thread_title):
        """
        checks for the existence of a game thread submission, if found, updates the text, otherwise submits new one
        """
        success = False
        if self.authenticate_reddit():
            todays_game_thread_links = self.get_game_thread_links_for_date(datetime.now())
            if todays_game_thread_links is not None and todays_game_thread_links.game is not None:
                # update thread
                game_thread_submission = self.reddit.get_submission(url=todays_game_thread_links.game)
                current_game_thread_post_text = \
                    self.current_game_thread_split_text +\
                    game_thread_submission.selftext.split(self.current_game_thread_split_text)[1]
                game_thread_submission.edit(
                    game_thread_markup + current_game_thread_post_text
                )
                success = True
            else:
                # submit new game thread
                game_thread_submission = self.reddit.get_subreddit(self.subreddit).submit(
                    text=game_thread_markup + self.current_game_thread_post_text,
                    title=game_thread_title
                )
                # add game thread link to game_thread_links dict
                if todays_game_thread_links is None:
                    todays_game_thread_links = game_thread_links()
                todays_game_thread_links.game = game_thread_submission.permalink
                self.add_game_thread_links(todays_game_thread_links)
                # sticky and flair
                game_thread_submission.sticky()
                game_thread_submission.set_flair(flair_text=self.game_thread_flair,
                                                 flair_css_class=self.game_thread_flair)
                success = True
        return success

    def generate_or_update_game_thread_if_necessary(self):
        game_is_live = self.is_the_game_on_now()
            # get pregame thread template
        if self.need_to_create_game_thread() or \
                (self.get_game_thread_links_for_date(datetime.now()) is not None and game_is_live):
            # get the game thread template
            # get game_day data
            local_game_time = self.game_day_info["local_game_time"]
            games = nba_game_scraper.get_games(local_game_time, 30)   # thirty second cache
            game_data = None
            # find the game our home-team is in
            for key, value in games.iteritems():
                if key.find(self.team_dict[self.teamName]['short_name']) is not -1:
                    game_data = value

            # local times
            local_time_format = "%I:%M %p"
            link_date_format = "%Y%m%d"
            link_date = local_game_time.strftime(link_date_format)
            game_time_eastern = local_game_time.astimezone(pytz.timezone('US/Eastern')).strftime(local_time_format)
            game_time_central = local_game_time.astimezone(pytz.timezone('US/Central')).strftime(local_time_format)
            game_time_mountain = local_game_time.astimezone(pytz.timezone('US/Mountain')).strftime(local_time_format)
            game_time_pacific = local_game_time.astimezone(pytz.timezone('US/Pacific')).strftime(local_time_format)

            #scores
            home_score = 0
            away_score = 0
            if 'home_score' in game_data and game_data['home_score'] is not None:
                home_score = game_data['home_score']
            if 'away_score' in game_data and game_data['away_score'] is not None:
                away_score = game_data['away_score']

            # format the template with game data
            game_thread_markup = self.current_game_thread_fmt.format(
                home_team_short=game_data['home_team'].upper(),
                home_team_name=self.team_dict_short_key[game_data['home_team'].upper()]['long_name'],
                home_subreddit=self.team_dict_short_key[game_data['home_team'].upper()]['sub'],
                home_score=home_score,
                home_team_win_loss='0-0',
                away_team_short=game_data['away_team'].upper(),
                away_team_name=self.team_dict_short_key[game_data['away_team'].upper()]['long_name'],
                away_subreddit=self.team_dict_short_key[game_data['away_team'].upper()]['sub'],
                away_score=away_score,
                away_team_win_loss='0-0',
                game_time_eastern=game_time_eastern,
                game_time_central=game_time_central,
                game_time_mountain=game_time_mountain,
                game_time_pacific=game_time_pacific,
                link_date=link_date
            )
            # format the title with game data
            game_thread_title = self.game_thread_title_fmt.format(
                home_team_name=self.team_dict_short_key[game_data['home_team'].upper()]['long_name'],
                home_team_win_loss='0-0',
                away_team_name=self.team_dict_short_key[game_data['away_team'].upper()]['long_name'],
                away_team_win_loss='0-0',
                month_day_year=local_game_time.strftime(self.game_thread_title_date_fmt)
            )
            # submit new or update
            success = self.post_new_or_update_game_thread(game_thread_markup, game_thread_title)

        elif self.need_to_create_pregame_thread():
            # create pregame thread
            print "Someone should implement creating a pregame thread"


def schedule_schedule_updates():
    bot = bulls_bot()
    run_updates = True
    consecutive_error_count = 0
    while run_updates:
        try:
            bot.generate_or_update_game_thread_if_necessary()
            schedule = bot.generate_default_schedule()  # get schedule
            bot.update_schedule(schedule)               # update subreddit
            update_freq = bot.get_current_update_freq() # figure out when to update again
            consecutive_error_count = 0
        except KeyboardInterrupt:
            print "keyboard interrupt. Stopping schedule updates"
            raise
        except BaseException, e:
            consecutive_error_count += 1
            print e
            print "an error occurred during schedule creation " + str(consecutive_error_count) + " consecutive errors"
            update_freq = 60    # try again in one minutes
            if consecutive_error_count > 2:
                print "too many consecutive errors. exiting."
                run_updates = False
                update_freq = 0
        print "sleeping for " + str(update_freq/60.0) + " minutes ... ... ..."
        time.sleep(update_freq)


if __name__ == "__main__":
    # bot = bulls_bot()
    # default_sched = bot.generate_default_schedule()
    # print default_sched
    # bot.update_schedule(default_sched)
    schedule_schedule_updates()

