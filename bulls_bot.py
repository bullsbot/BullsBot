__version__ = '0.0.3'

import logging
from datetime import datetime, timedelta, time as dttime
import time
import getpass
import vobject
import pytz
from urllib.request import urlopen
import praw
import prawcore
from random import randrange
import settings
import nba_game_scraper
import nba_standings_scraper
import util
import os
from standings_formatter import StandingsFormatter

log_date_fmt = '%y-%m-%d %X %Z'
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt=log_date_fmt,
                    filename='bullsbot.log',
                    filemode='a')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format for console use
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt=log_date_fmt)
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)


class GameThreadLinks(object):
    """ Object containing links to game thread links
    """

    def __init__(self, pre=None, game=None, post=None):
        self.pre = pre              # link to pregame thread
        self.game = game            # link to game thread
        self.post = post            # link to postgame thread


class bulls_bot(object):
    """ Reddit bot that handles updating the sidebar and game-threads periodically
    """

    def __init__(self):
        self.logger = logging.getLogger('BB')
        # username
        if 'username' not in settings.reddit:
            self.username = input('Reddit Username: ')
        else:
            self.username = settings.reddit['username']
            self.logger.info("Reddit Username: {}".format(self.username))
            # sub
        if 'subreddit' not in settings.reddit:
            self.subreddit = input('Subreddit (e.g. chicagobulls, not /r/chicagobulls): ')
        else:
            self.subreddit = settings.reddit['subreddit']
            self.logger.info("Reddit Subreddit: {}".format(self.subreddit))

        # bot
        self.reddit = None
        self.userAgent = 'BullsBot/v0.0.3 by ' + self.username

        # check that the username and password work, if not die now!
        if not self.authenticate_reddit():
            self.logger.info("Could not login to reddit with " + self.username)
            raise praw.exceptions.LoginRequired("bulls_bot")
        else:
            self.logger.info(self.username + ' successfully logged in.')

        # load all other settings from settings file
        self.load_settings()

    def load_settings(self):
        # calendar link(s)
        self.calendar_no_date_flag = settings.calendar['no_date_flag']
        self.logger.info('using default calendar url')
        self.calendarURL = settings.calendar['url']

        # team
        self.teamName = settings.bot['team_name']
        # team data
        self.teamInfoFilePath = settings.team['team_data_file']
        # load team data
        self.load_teams()

        # standings
        self.latest_standings = None
        self.standings_sidebar_last_updated = None
        self.standings_grouping = settings.standings['standings_grouping']
        self.sidebar_standings_start_string = settings.standings['sidebar_standings_start_string']
        self.sidebar_standings_end_string = settings.standings['sidebar_standings_end_string']
        # self.sidebar_standings_row_fmt = "[](#{short_name}){med_name}|{wins}|{losses}|{percent}\n"
        formatter = StandingsFormatter(self.team_dict, self.team_dict_med_key, self.teamName,
                                       division_standings_format=settings.standings['division_standings_format'],
                                       conference_standings_format=settings.standings['conference_standings_format']
        )
        self.standings_formatter = formatter.get_formatter(self.standings_grouping)

        # gameday info
        self.bot_timezone = pytz.timezone(settings.bot['timezone'])
        self.game_day_info = None
        self.last_game_day_check = datetime.min
        # game thread links (key is date, value is game_thread_links object)
        self.game_thread_links = {}
        # update frequencies
        self.non_game_day_upate_freq = settings.bot['non_game_day_update_freq']
        self.game_day_upate_freq = settings.bot['game_day_update_freq']
        self.near_game_upate_freq = settings.bot['near_game_update_freq']
        self.game_time_upate_freq = settings.bot['game_time_update_freq']
        self.game_thread_create_time = settings.bot['game_thread_create_time']

        # schedule template
        self.max_events_to_display = settings.schedule['max_events_to_display']
        self.prior_events_to_display = settings.schedule['prior_events_to_display']
        self.min_events_to_display = settings.schedule['min_events_to_display']
        self.sidebar_schedule_start_string = settings.schedule['sidebar_schedule_start_string']
        self.sidebar_schedule_end_string = settings.schedule['sidebar_schedule_end_string']
        # schedule markdown formats
        self.event_fmt = settings.schedule['event_fmt']
        self.past_game_fmt = settings.schedule['past_game_fmt']
        self.current_game_fmt = settings.schedule['current_game_fmt']
        self.future_game_fmt = settings.schedule['future_game_fmt']
        self.game_thread_link_fmt = settings.schedule['game_thread_link_fmt']
        self.event_markdown_pre = settings.schedule['event_markdown_pre']
        self.event_markdown_post = settings.schedule['event_markdown_post']

        # thread markdown formats
        self.post_game_thread_fmt = settings.thread['post_game_thread_fmt']
        self.post_game_thread_title_fmt = settings.thread['post_game_thread_title_fmt']
        self.pre_game_thread_fmt = settings.thread['pre_game_thread_fmt']
        self.pre_game_thread_title_fmt = settings.thread['pre_game_thread_title_fmt']
        self.pre_game_date_fmt = settings.thread['pre_game_date_fmt']
        self.current_game_thread_fmt = settings.thread['current_game_thread_fmt']
        self.current_game_thread_split_text = settings.thread['current_game_thread_split_text']
        self.game_thread_title_fmt = settings.thread['game_thread_title_fmt']
        self.game_thread_title_date_fmt = settings.thread['game_thread_title_date_fmt']
        self.game_thread_flairs = settings.thread['game_thread_flairs']

    def authenticate_reddit(self):
        """
        checks if logged in and if not, logs in for us. returns false if we couldn't log in
        """
        authenticated = False
        try:
            if self.reddit is None:
                #Initiate PRAW
                self.reddit = praw.Reddit(
                    client_id=os.environ['client_id'],
                    client_secret=os.environ['client_secret'],
                    refresh_token=os.environ['refresh_token'],
                    user_agent=self.userAgent)

            authenticated = True
        except:
            authenticated = False
        return authenticated

    def get_cal(self):
        """ get calendar from url
        """
        calendarContent = urlopen(self.calendarURL).read().decode("utf-8")
        cal = vobject.readOne(calendarContent)
        return cal

    def load_teams(self):
        # load team info
        self.team_dict = {}
        self.team_dict_med_key = {}
        self.team_dict_short_key = {}
        with open(self.teamInfoFilePath, "r") as teamInfoFile:
            for teamInfoRow in teamInfoFile.read().split("\n"):
                teamInfo = teamInfoRow.split(',')
                tmp_team_dict = {
                    'long_name': teamInfo[0],
                    'med_name': teamInfo[1],
                    'short_name': teamInfo[2].upper(),
                    'sub': teamInfo[3],
                    'timezone': teamInfo[4],
                    'division': teamInfo[5],
                    'conference': teamInfo[6]
                }
                self.team_dict[teamInfo[0]] = tmp_team_dict
                self.team_dict_med_key[teamInfo[1]] = tmp_team_dict
                self.team_dict_short_key[teamInfo[2].upper()] = tmp_team_dict

    def get_standings(self):
        if self.latest_standings is None:
            self.load_standings()
        return self.latest_standings

    def load_standings(self):
        tmp_standings = nba_standings_scraper.scrape_standings(group=self.standings_grouping)
        if tmp_standings and tmp_standings is not None:
            self.latest_standings = tmp_standings

    def is_game_vevent(self, vevent):
        # simple and stupid for now
        # return vevent.summary.valueRepr().find(self.event_flag) == -1
        return vevent.summary.valueRepr().find('#') == -1

    def load_gameday_info(self):
        # todo: create gameday_info class
        current_local_datetime = datetime.now(self.bot_timezone)
        current_local_date = current_local_datetime.date()
        cal = self.get_cal()
        is_game_day = False
        for event in cal.vevent_list:
            if self.is_game_vevent(event) and type(event.dtstart.value) is datetime:
                local_game_time = event.dtstart.value.astimezone(self.bot_timezone)
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

    def is_game_over(self):
        return self.game_day_info is not None \
                   and 'current_status' in self.game_day_info \
            and (self.game_day_info['current_status'] == 'FINAL')

    def is_the_game_on_now(self):
        local_timezone = pytz.timezone(self.team_dict[self.teamName]['timezone'])
        current_local_datetime = datetime.now(local_timezone)
        is_game_live = False
        if self.is_today_a_game_day():
            minutes_till_tipoff = (self.game_day_info['local_game_time'] - current_local_datetime).total_seconds() / 60
            # if it's before tipoff, assume it's not on yet
            if minutes_till_tipoff > 5:
                is_game_live = False
                self.game_day_info['current_status'] = 'PRE'
            else:
                # otherwise, check game status
                games = nba_game_scraper.get_games(datetime.now(self.bot_timezone), 30)   # thirty second cache
                live_game_on = False
                game_found = False
                # key is like CHI_SAS, value is a dict with game data
                for key, value in games.iteritems():
                    if key.find(self.team_dict[self.teamName]['short_name']) is not -1:
                        game_found = True
                        self.game_day_info['current_status'] = value['current_status']
                        if value['current_status'] == 'LIVE':
                            is_game_live = True
                        break
                        # if the scraper couldn't find the game (a possibility with nba.com)
                        # and the last status wasn't FINAL, assume it's still on
                if not game_found and (self.game_day_info['current_status'] != 'FINAL'):
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
        current_local_date = datetime.now(self.bot_timezone).date()
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
        events = sorted(cal.vevent_list, key=lambda vevent: vevent.dtstart.value if (
            type(vevent.dtstart.value) is datetime) else datetime(vevent.dtstart.value.year, vevent.dtstart.value.month,
                                                                  vevent.dtstart.value.day, tzinfo=cal_timezone))
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
                # add timezone if it's already a datetime
                localGameTime = event.dtstart.value.astimezone(local_timezone)
            else:
                # otherwise, it's a date so create new datetime with the date and give it the local timezone
                # (if we were to use the calendars timezone and then convert it to local time, we could potentially change the date)
                localGameTime = datetime(event.dtstart.value.year, event.dtstart.value.month, event.dtstart.value.day,
                                         tzinfo=local_timezone)
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
                    # get event formatted to proper markdown
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
                    # replace trailing newline and return
        return schedule_as_string.rstrip('\n')

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
                month_day = local_date_time.strftime(date_format).upper() + '-' + local_end_date_time.strftime(
                    day_format)
            # if they are in two different months
            else:
                month_day = local_date_time.strftime(short_date_format) + '-' + local_end_date_time.strftime(
                    short_date_format)
        title_and_hashtag = summary.replace(self.calendar_no_date_flag, '').split(' #')
        title = title_and_hashtag[0].strip()
        try:
            hashtag = "#" + title_and_hashtag[1].strip()
        except IndexError:
            hashtag = "#"

        if summary.find(self.calendar_no_date_flag) is not -1:
            month_day = '-'

        return self.event_fmt.format(event_title=title, event_hashtag=hashtag, month_day=month_day)

    def format_game(self, game, timezone):
        date_format = "%b %d"
        time_format = "%I:%M %p"
        # if startDate <= game.dtstart.value <= endDate:
        if type(game.dtstart.value) is datetime:
            chiDateTime = game.dtstart.value.astimezone(timezone)
        else:
            chiDateTime = datetime(game.dtstart.value.year, game.dtstart.value.month, game.dtstart.value.day,
                                   tzinfo=timezone)
        month_day = chiDateTime.strftime(date_format).upper().replace(" 0", " ")
        if type(game.dtstart.value) is datetime:
            game_time_local = chiDateTime.strftime(time_format).lstrip("0")
        else:
            game_time_local = 'TBA'
        # Get Summary
        self.logger.debug('Summary: ' + game.summary.valueRepr())
        self.logger.debug('Location: ' + game.location.valueRepr())
        home_and_away_teams = game.summary.valueRepr().split(" @ ")
        if len(home_and_away_teams) == 1:
            # older espn calendars use 'at' instead of '@'
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
                self.logger.error(
                    'could not find game data for ' + away_team_short + '_' + home_team_short + ' on ' + month_day)
                raise
                # if game start time has passed and we're in the middle of the game
            #  and the game is not listed as live or final or postponed, raise error
            if chiDateTime < datetime.now(timezone) and self.game_day_info is not None \
                and (self.game_day_info['current_status'] == 'LIVE') \
                and not (game_data['current_status'] == "LIVE"
                         or game_data['current_status'] == "FINAL"
                         or game_data['current_status'] == "PPD"):
                raise AssertionError('no LIVE, FINAL, or PPD status on game with start time in past')

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

        if has_scores and (game_data['current_status'] == "FINAL"):
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
        elif has_scores and (game_data['current_status'] == "LIVE"):
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
        # by default next update time should be tomorrow
        now = datetime.now(self.bot_timezone)
        tomorrow = datetime.now(self.bot_timezone).date() + timedelta(1)
        five_am = datetime.combine(tomorrow, dttime(2, 0, 0)).replace(tzinfo=self.bot_timezone)
        current_update_freq = (five_am - now).total_seconds()
        if self.is_today_a_game_day():
            todays_game_thread_links = self.get_game_thread_links_for_date(now)
            if self.is_the_game_on_now():
                # if the game is on now, update at the game time update frequency
                current_update_freq = self.game_time_upate_freq
            elif (todays_game_thread_links is None or todays_game_thread_links.game is None) \
                and self.get_seconds_till_game() > - 1:
                # if there's no game thread and the game hasn't started
                # update when the game thread is supposed to get created
                current_update_freq = self.get_seconds_till_game() - self.game_thread_create_time
            elif self.is_game_over() and (todays_game_thread_links is None or todays_game_thread_links.post is None):
                # if the game is over and no post-game is on, update immediately
                current_update_freq = 0
            elif self.is_game_over() and todays_game_thread_links is not None \
                and todays_game_thread_links.post is not None:
                # if the game is over and post-game thread is created, update tomorrow at 5am
                current_update_freq = (five_am - now).total_seconds()
            else:
                # game isn't on and isn't over so update when the game is about to start
                current_update_freq = self.get_seconds_till_game()
                # make sure the soonest we can update is in 30 seconds
        return max(current_update_freq, 30)

    def generate_default_schedule(self):
        self.logger.info("generating default schedule")
        begin_date = None
        # find date to begin schedule with
        cal = self.get_cal()
        local_timezone = pytz.timezone(self.team_dict[self.teamName]['timezone'])
        cal_timezone = pytz.timezone(cal.contents['x-wr-timezone'][0].value)
        # for vevent in cal.vevent_list:
        events = sorted(cal.vevent_list, key=lambda vevent: vevent.dtstart.value if (
            type(vevent.dtstart.value) is datetime) else datetime(vevent.dtstart.value.year, vevent.dtstart.value.month,
                                                                  vevent.dtstart.value.day, tzinfo=cal_timezone),
                        reverse=True)
        # events = sorted(cal.vevent_list, key=attrgetter('dtstart.value'), reverse=True)
        current_local_date = datetime.now(self.bot_timezone).date()
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
                        begin_date = datetime(event.dtstart.value.year, event.dtstart.value.month,
                                              event.dtstart.value.day, tzinfo=local_timezone)
                    break

        return self.schedule_maker(startDate=begin_date, max_events=self.max_events_to_display)

    def update_schedule(self, schedule=None):
        self.logger.info("begin updating schedule ... ")
        if schedule is None:
            schedule = self.generate_default_schedule()
            # make sure we're logged in (and if not, log in)
        if self.authenticate_reddit():
            #Get the sidebar
            # settings=r.get_settings(self.team_dict[self.teamName]['sub'])
            self.logger.info("fetching subreddit settings")
            settings = self.reddit.subreddit(self.subreddit).mod.settings()
            description_markup = settings['description']
            self.logger.info("updating subreddit settings with schedule")
            before_sched_start = description_markup.split(self.sidebar_schedule_start_string, 1)[0]
            after_sched_start = description_markup.split(self.sidebar_schedule_start_string, 1)[1]
            after_sched_end = after_sched_start.split(self.sidebar_schedule_end_string, 1)[1]
            settings['description'] = before_sched_start + self.sidebar_schedule_start_string + "\n" + schedule + \
                                      self.sidebar_schedule_end_string + after_sched_end
            settings = self.reddit.subreddit(self.subreddit).mod.update(description=settings['description'])
            local_timezone = pytz.timezone(self.team_dict[self.teamName]['timezone'])
            formated_time = datetime.now(local_timezone).strftime("%I:%M %p")
            responses = ["Thibs would be proud of this hustle! Updated that schedy sched for u at around ",
                         "Schedy sched updated ", "1000010010101000101001 at ", "Ok, just updated at ",
                         "What it is, just updated at ", "Boom, did it at ",
                         "Puttin in work sukka! Just updated that schedule at ", "Yoooooooooo.... did it again at ",
                         "Knock knock. (Who's there?) BULLS BOT PUTTIN IN WORK! ... at ",
                         " Yaawwn, got anything else for me to do? ... just updated again at ",
                         "Guess what I just did at ", "Beep Boop Bop Beep Booop at "]
            response = responses[randrange(len(responses))]
            self.logger.info('[In /r/' + self.subreddit + '] ' + response + formated_time)
        else:
            self.logger.error("could not authenticate through reddit")

    def add_game_thread_links(self, gtl, gameDate=None):
        """
        adds a game_thread_links object to self.game_thread_links dict with today's date as a key
        """
        key_date_format = "%Y%m%d"
        if gameDate is None:
            gameDate = datetime.now(self.bot_timezone)
        key = gameDate.strftime(key_date_format)
        self.game_thread_links[key] = gtl

    def findGameThreadsByDate(self, subreddit, game_thread_flairs, date, local_timezone):
        query = "("
        for flair in game_thread_flairs.values():
            if query == "(":
                query += "flair:'" + flair + "'"
            else:
                query += " OR flair:'" + flair + "'"
        query += ")"
        posts = subreddit.search(query=query, sort='new', time_filter='all', limit=30)
        gtl = GameThreadLinks()
        found = False
        for post in posts:
            print('1')
            if datetime.fromtimestamp(post.created_utc, local_timezone).date() == date:
                # if right date
                game_pre_post = None
                for key, flair in game_thread_flairs.items():
                    if flair == post.link_flair_css_class:
                        game_pre_post = key
                if game_pre_post is not None:
                    found = True
                    # if it's flair matches one of our game thread flairs
                    if getattr(gtl, game_pre_post) is None:
                        # set it
                        self.logger.debug('found ' + game_pre_post + ' game thread for ' +
                                          str(datetime.fromtimestamp(post.created_utc, local_timezone).date()))
                        setattr(gtl, game_pre_post, post.permalink)

            elif datetime.fromtimestamp(post.created_utc, local_timezone).date() < date:
                # if this is older than the date we're searching break
                break
        if not found:
            gtl = None
        return gtl

    def get_game_thread_links_for_date(self, date, game_pre_post=None):
        if game_pre_post is None:
            game_pre_post = ['game', 'pre', 'post']
        elif not isinstance(game_pre_post, list):
            game_pre_post = [game_pre_post]
        local_timezone = pytz.timezone(self.team_dict[self.teamName]['timezone'])
        date = date.astimezone(self.bot_timezone)
        key_date_format = "%Y%m%d"
        key = date.strftime(key_date_format)
        game_thread = None
        if key in self.game_thread_links:
            game_thread = self.game_thread_links[key]
            # if any of the game threads requested are none, search sub
        missing_game_thread_flairs = {}
        for key in game_pre_post:
            if game_thread is None or getattr(game_thread, key) is None:
                missing_game_thread_flairs[key] = self.game_thread_flairs[key]

        if date.date() <= datetime.now(self.bot_timezone).date() \
            and len(missing_game_thread_flairs) > 0 \
            and self.authenticate_reddit():
            # couldn't find link, let's find them
            tmp_game_thread = self.findGameThreadsByDate(self.reddit.subreddit(self.subreddit),
                                                         missing_game_thread_flairs, date.date(), local_timezone)
            # set missing game threads if found
            if game_thread is None and tmp_game_thread is not None:
                game_thread = tmp_game_thread
            elif tmp_game_thread is not None:
                for key in missing_game_thread_flairs.keys():
                    setattr(game_thread, key, getattr(tmp_game_thread, key))
                    # save game thread
            if game_thread is not None:
                self.add_game_thread_links(game_thread, gameDate=date)
        return game_thread

    def get_game_thread_link_as_formatted_string(self, date):
        """
        returns an empty string or, if it exists, a game thread url formated as defined in game_thread_link_fmt
        """
        formatted_string = ''
        game_thread_links = self.get_game_thread_links_for_date(date, game_pre_post='game')
        if game_thread_links is not None and game_thread_links.game is not None:
            long_link = game_thread_links.game
            redditcom = "reddit.com/"
            short_link = "/" + long_link.split(redditcom)[1].split("/")[3]
            formatted_string = self.game_thread_link_fmt.format(link=short_link)
        return formatted_string

    def need_to_create_postgame_thread(self):
        """
        returns true if it's a game-day and there is no game_thread.pre link.
        """
        game_thread_links = self.get_game_thread_links_for_date(datetime.now(self.bot_timezone), game_pre_post='post')
        return self.is_today_a_game_day() and self.is_game_over() \
            and (game_thread_links is None
                 or (game_thread_links is not None and game_thread_links.post is None))

    def need_to_create_pregame_thread(self):
        """
        returns true if it's a game-day and there is no game_thread.pre link.
        """
        game_thread_links = self.get_game_thread_links_for_date(datetime.now(self.bot_timezone), game_pre_post='pre')
        return self.is_today_a_game_day() \
            and (game_thread_links is None
                 or (game_thread_links is not None and game_thread_links.pre is None))

    def need_to_create_game_thread(self):
        """
        returns true if it's a game-day and the game hasn't started and it's within an hour to game-time
        and there is no game_thread.game link.
        """
        game_thread_links = self.get_game_thread_links_for_date(datetime.now(self.bot_timezone), game_pre_post='game')
        return self.is_today_a_game_day() \
                   and -1 < self.get_seconds_till_game() < self.game_thread_create_time \
            and (game_thread_links is None
                 or (game_thread_links is not None and game_thread_links.game is None))

    def post_new_or_update_game_thread(self, game_thread_markup, game_thread_title, game_pre_post):
        """
        checks for the existence of a game thread submission, if found, updates the text, otherwise submits new one
        """
        self.logger.debug('post_new_or_update_game_thread')
        success = False
        if self.authenticate_reddit():
            flair = self.game_thread_flairs[game_pre_post]
            todays_game_thread_links = self.get_game_thread_links_for_date(datetime.now(self.bot_timezone),
                                                                           game_pre_post=game_pre_post)
            if game_pre_post == 'game':
                link = None
                if todays_game_thread_links is not None:
                    link = getattr(todays_game_thread_links, game_pre_post)

                if link is not None:
                    # update thread
                    self.logger.debug('updating thread')
                    updated_game_thread_markup = game_thread_markup.split(self.current_game_thread_split_text)[0]
                    game_thread_submission = self.reddit.get_submission(url=link)
                    current_game_thread_post_text = \
                        self.current_game_thread_split_text + \
                        game_thread_submission.selftext.split(self.current_game_thread_split_text)[1]
                    game_thread_submission.edit(
                        updated_game_thread_markup + current_game_thread_post_text
                    )
                    success = True
                else:
                    # submit new game thread
                    self.logger.debug('submitting new game thread')
                    game_thread_submission = self.reddit.subreddit(self.subreddit).submit(
                        text=game_thread_markup,
                        title=game_thread_title
                    )
                    # add game thread link to game_thread_links dict
                    if todays_game_thread_links is None:
                        todays_game_thread_links = GameThreadLinks()
                    todays_game_thread_links.game = game_thread_submission.permalink
                    self.add_game_thread_links(todays_game_thread_links)
                    # sticky and flair
                    game_thread_submission.sticky()
                    game_thread_submission.set_flair(flair_text=flair, flair_css_class=flair)
                    # create and replace reddit stream link (see reddit-stream.com)
                    game_thread_submission.edit(
                        game_thread_markup.replace('reddit-stream.com/',
                                                   'reddit-stream.com/comments/' + game_thread_submission.id)
                    )
                    success = True
            else:
                # submit new pre or post thread
                self.logger.debug('submitting new pre or post thread (' + game_pre_post + ')')
                game_thread_submission = self.reddit.subreddit(self.subreddit).submit(
                    text=game_thread_markup,
                    title=game_thread_title
                )
                # add game thread link to game_thread_links dict
                if todays_game_thread_links is None:
                    todays_game_thread_links = GameThreadLinks()
                setattr(todays_game_thread_links, game_pre_post, game_thread_submission.permalink)
                self.add_game_thread_links(todays_game_thread_links)
                # sticky and flair
                game_thread_submission.sticky()
                game_thread_submission.set_flair(flair_text=flair, flair_css_class=flair)
                success = True

        return success

    def generate_or_update_game_thread_if_necessary(self):
        """
        Creates or updates game threads as necessary.
        """
        self.logger.debug('generate_or_update_game_thread_if_necessary')
        if not self.is_today_a_game_day():
            if self.authenticate_reddit():
                subreddit = self.reddit.subreddit(self.subreddit)
                topExists = True
                botExists = True

                try:
                    topSticky = subreddit.sticky(1)
                except:
                    topExists = False
                
                try:
                    botSticky = subreddit.sticky(2)
                except:
                    botExists = False
                
                if topExists and topSticky.link_flair_css_class in self.game_thread_flairs.values():
                    # if submission is top stickied with one of our game thread flairs, un-sticky it
                    self.logger.info("unstickying last " + submission.link_flair_css_class + " from top")
                    topSticky.mod.undistinguish()
                if botExists and topSticky.link_flair_css_class in self.game_thread_flairs.values():
                    # if submission is bottom stickied with one of our game thread flairs, un-sticky it
                    self.logger.info("unstickying last " + submission.link_flair_css_class + " from bottom")
                    botSticky.mod.undistinguish()

        else:
            # if it is a game day, check to see if we need to create a game thread
            game_is_live = self.is_the_game_on_now()
            need_to_create_postgame_thread = self.need_to_create_postgame_thread()
            need_to_create_pregame_thread = self.need_to_create_pregame_thread()
            need_to_create_game_thread = self.need_to_create_game_thread()
            need_to_update_game_thread = \
                self.get_game_thread_links_for_date(datetime.now(self.bot_timezone), game_pre_post='game') is not None \
                    and (game_is_live or self.game_day_info['current_status'] == 'LIVE')

            variables = {}
            if need_to_create_postgame_thread \
                or need_to_create_game_thread \
                or need_to_update_game_thread \
                or need_to_create_pregame_thread:
                # get the game game time
                local_game_time = self.game_day_info["local_game_time"]
                # local times
                local_time_format = "%I:%M %p"
                link_date_format = "%Y%m%d"
                link_date = local_game_time.strftime(link_date_format)
                variables = util.get_zoned_dates_for_format_string(
                    self.pre_game_thread_fmt + self.current_game_thread_fmt + self.post_game_thread_fmt + \
                    self.pre_game_thread_title_fmt + self.game_thread_title_fmt + self.post_game_thread_title_fmt,
                    local_game_time
                )

                # get game_day data
                games = nba_game_scraper.get_games(local_game_time, 30)   # thirty second cache
                game_data = None
                # find the game our home-team is in
                for key, value in games.iteritems():
                    if key.find(self.team_dict[self.teamName]['short_name']) is not -1:
                        game_data = value
                        # what if game is not in list? nba.com will periodically remove a game for some reason
                home_team_info = self.team_dict_short_key[game_data['home_team'].upper()]
                home_team_standings = self.get_standings()[home_team_info['med_name']]
                away_team_info = self.team_dict_short_key[game_data['away_team'].upper()]
                away_team_standings = self.get_standings()[away_team_info['med_name']]
                broadcast_info = nba_game_scraper.scrape_broadcast_info(datetime.now(self.bot_timezone),
                                                                        game_data['home_team'].upper(),
                                                                        game_data['away_team'].upper())
                broadcast_strings = []
                for key, channels in broadcast_info.iteritems():
                    if len(channels) > 0:
                        broadcast_strings.append(key.capitalize() + ": **" + "** ~~/~~ **".join(channels) + "**")
                broadcast = "  ~~/~~  ".join(broadcast_strings)

                if need_to_create_pregame_thread:
                    # create pre-game thread
                    self.logger.info('creating pre-game thread')
                    pregame_thread_markup = self.pre_game_thread_fmt.format(
                        home_team_short=game_data['home_team'].upper(),
                        home_team_name=home_team_info['long_name'],
                        home_subreddit=home_team_info['sub'],
                        home_team_win_loss=home_team_standings['wins'] + '-' + home_team_standings['losses'],
                        away_team_short=game_data['away_team'].upper(),
                        away_team_name=away_team_info['long_name'],
                        away_subreddit=away_team_info['sub'],
                        away_team_win_loss=away_team_standings['wins'] + '-' + away_team_standings['losses'],
                        link_date=link_date,
                        full_date=local_game_time.strftime(self.pre_game_date_fmt),
                        broadcast=broadcast,
                        game_time_eastern=game_time_eastern,
                        game_time_central=game_time_central,
                        game_time_mountain=game_time_mountain,
                        game_time_pacific=game_time_pacific
                    )
                    # format the title with game data
                    pregame_thread_title = self.pre_game_thread_title_fmt.format(
                        home_team_name=home_team_info['long_name'],
                        home_team_win_loss=home_team_standings['wins'] + '-' + home_team_standings['losses'],
                        away_team_name=away_team_info['long_name'],
                        away_team_win_loss=away_team_standings['wins'] + '-' + away_team_standings['losses'],
                        month_day_year=local_game_time.strftime(self.game_thread_title_date_fmt)
                    )
                    success = self.post_new_or_update_game_thread(pregame_thread_markup,
                                                                  pregame_thread_title, 'pre')

                else:
                    # create post-game or game thread
                    #scores
                    home_score = 0
                    away_score = 0
                    if 'home_score' in game_data and game_data['home_score'] is not None:
                        home_score = game_data['home_score']
                    if 'away_score' in game_data and game_data['away_score'] is not None:
                        away_score = game_data['away_score']

                    if need_to_create_postgame_thread:
                        # create post-game thread
                        self.logger.info('creating post-game thread')
                        # format the template with game data
                        postgame_thread_markup = self.post_game_thread_fmt.format(
                            home_team_short=game_data['home_team'].upper(),
                            home_team_name=home_team_info['long_name'],
                            home_score=home_score,
                            home_team_win_loss=home_team_standings['wins'] + '-' + home_team_standings['losses'],
                            away_team_short=game_data['away_team'].upper(),
                            away_team_name=away_team_info['sub'],
                            away_score=away_score,
                            away_team_win_loss=away_team_standings['wins'] + '-' + away_team_standings['losses'],
                            link_date=link_date,
                            full_date=local_game_time.strftime(self.game_thread_title_date_fmt)
                        )
                        # Where are we and did we win
                        our_score = home_score
                        their_score = away_score
                        other_team = self.team_dict_short_key[game_data['away_team'].upper()]['long_name']
                        our_standings = home_team_standings
                        their_standings = away_team_standings
                        if self.team_dict_short_key[game_data['away_team'].upper()]['long_name'] == self.teamName:
                            our_score = away_score
                            their_score = home_score
                            other_team = self.team_dict_short_key[game_data['home_team'].upper()]['long_name']
                            their_standings = home_team_standings
                            our_standings = away_team_standings
                        beat_or_lose = ' defeat the '
                        our_win_loss = str(1 + int(our_standings['wins'])) + '-' + our_standings['losses']
                        their_win_loss = their_standings['wins'] + '-' + str(1 + int(their_standings['losses']))
                        sub_team_name = self.teamName
                        if int(our_score) < int(their_score):
                            our_win_loss = our_standings['wins'] + '-' + str(1 + int(our_standings['losses']))
                            their_win_loss = str(1 + int(their_standings['wins'])) + '-' + their_standings['wins']
                            beat_or_lose = ' fall to the '
                        else:
                            # if we win and they had a streak going, we're streakbreakers!
                            streakWinLoss = our_standings['streak'].split(' ')[0]
                            streakCount = int(our_standings['streak'].split(' ')[1])
                            if streakCount >= 5 and streakWinLoss == 'Win':
                                sub_team_name = self.teamName + ' Streakbreakers'
                                # format the title with game data
                        postgame_thread_title = self.post_game_thread_title_fmt.format(
                            sub_team_name=sub_team_name,
                            sub_team_win_loss=our_win_loss,
                            non_sub_team_name=other_team,
                            non_sub_team_win_loss=their_win_loss,
                            beat_or_lose=beat_or_lose,
                            sub_score=our_score,
                            non_sub_score=their_score
                        )
                        success = self.post_new_or_update_game_thread(postgame_thread_markup,
                                                                      postgame_thread_title, 'post')

                    else:
                        # create game thread
                        self.logger.info('creating game thread')
                        # format the template with game data
                        game_thread_markup = self.current_game_thread_fmt.format(
                            home_team_short=game_data['home_team'].upper(),
                            home_team_name=home_team_info['long_name'],
                            home_subreddit=home_team_info['sub'],
                            home_score=home_score,
                            home_team_win_loss=home_team_standings['wins'] + '-' + home_team_standings['losses'],
                            away_team_short=game_data['away_team'].upper(),
                            away_team_name=away_team_info['long_name'],
                            away_subreddit=away_team_info['sub'],
                            away_score=away_score,
                            away_team_win_loss=away_team_standings['wins'] + '-' + away_team_standings['losses'],
                            game_time_eastern=game_time_eastern,
                            game_time_central=game_time_central,
                            game_time_mountain=game_time_mountain,
                            game_time_pacific=game_time_pacific,
                            link_date=link_date,
                            broadcast=broadcast
                        )
                        # format the title with game data
                        game_thread_title = self.game_thread_title_fmt.format(
                            home_team_name=home_team_info['long_name'],
                            home_team_win_loss=home_team_standings['wins'] + '-' + home_team_standings['losses'],
                            away_team_name=away_team_info['long_name'],
                            away_team_win_loss=away_team_standings['wins'] + '-' + away_team_standings['losses'],
                            month_day_year=local_game_time.strftime(self.game_thread_title_date_fmt)
                        )
                        # post or update game thread
                        success = self.post_new_or_update_game_thread(game_thread_markup, game_thread_title, 'game')

    def update_standings_sidebar(self):
        """ Updates subreddit sidebar with standings table once a day and after a game
        """
        standings_table = self.generate_standings()
        if self.authenticate_reddit():
            self.logger.info("fetching subreddit settings")
            settings = self.reddit.get_settings(self.subreddit)
            description_markup = settings['description']
            self.logger.info("updating subreddit settings with standings")
            before_standings_start = description_markup.split(self.sidebar_standings_start_string, 1)[0]
            after_standings_start = description_markup.split(self.sidebar_standings_start_string, 1)[1]
            after_standings_end = after_standings_start.split(self.sidebar_standings_end_string, 1)[1]

            settings['description'] = before_standings_start \
                                      + self.sidebar_standings_start_string \
                                      + standings_table \
                                      + self.sidebar_standings_end_string \
                                      + after_standings_end

            self.reddit.subreddit(self.subreddit).update_settings(
                description=settings['description']
            )
            self.standings_sidebar_last_updated = datetime.now(self.bot_timezone)
            self.logger.info("updated standings sidebar at " + str(self.standings_sidebar_last_updated))

    def generate_standings(self):
        """ formats markup with division team standings
        """
        # sort by division rank
        return self.standings_formatter(self.get_standings())


def schedule_schedule_updates():
    bot = bulls_bot()
    run_updates = True
    consecutive_error_count = 0
    while run_updates:
        try:
            # try:
            # bot.load_standings()                                  # update standings
            # bot.generate_or_update_game_thread_if_necessary()     # update or create game threads if necessary
            # bot.update_standings_sidebar()                        # update standings in sidebar if necessary
            schedule = bot.generate_default_schedule()            # get schedule
            bot.update_schedule(schedule)                         # update schedule in sidebar
            update_freq = bot.get_current_update_freq()           # figure out when to update again
            consecutive_error_count = 0
        except KeyboardInterrupt as e:
            logging.error("keyboard interrupt. Stopping schedule updates")
            logging.exception(e)
            raise
        except BaseException as e:
            consecutive_error_count += 1
            logging.exception(e)
            logging.warning("an error occurred during schedule creation " + str(consecutive_error_count) +
                            " consecutive errors")
            update_freq = 60    # try again in one minutes
            if consecutive_error_count > 10:
                logging.warning("too many consecutive errors. exiting.")
                run_updates = False
                update_freq = 0
                raise
        logging.info("sleeping for " + str(update_freq / 60.0) + " minutes ... ... ...")
        time.sleep(update_freq)


if __name__ == "__main__":
    # bot = bulls_bot()
    # default_sched = bot.generate_default_schedule()
    # print default_sched
    # bot.update_schedule(default_sched)
    schedule_schedule_updates()
