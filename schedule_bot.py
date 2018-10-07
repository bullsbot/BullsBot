__author__ = 'nmew'
from jinja2 import Environment, PackageLoader
from utils import dotdictify
import settings
import time
from datetime import datetime
import urllib2
import json
from bs4 import BeautifulSoup

ENV = Environment(loader=PackageLoader(settings.jinja['loader'], settings.jinja['templates_folder']))
TEMPLATE_FILE = settings.schedule['markdown_template_file']
# todo: do it like this: http://docs.python-guide.org/en/latest/scenarios/web/#jinja2


def get_scoreboard(date):
    url = settings.data['scoreboard_url'].format(date=date)
    return dotdictify(json.loads(urllib2.urlopen(url, timeout=2).read()))


def get_game_dates(team_nickname):
    url = settings.schedule['game_dates_url'].format(team_nickname)
    html = urllib2.urlopen(url, timeout=2).read()
    soup = BeautifulSoup(html)
    game_date_elems = soup.select('.nbaFnlStatTxSm')
    game_dates = []
    for elem in game_date_elems:
        game_dates.append(datetime.fromtimestamp(time.mktime(time.strptime(elem.string, '%b %d, %Y'))))
    return game_dates


def get_current_series_games(team_nickname, team_key):
    game_dates = get_game_dates(team_nickname)
    series_opponent = None
    series_games = []

    for game_date in game_dates[::-1][0:10]:
        scoreboard = get_scoreboard(game_date)
        games = scoreboard.get(settings.data['games_tree'])
        home_team_key = 'home.team_key'
        visitor_team_key = 'visitor.team_key'
        team_key = team_key
        for game_dict in games:
            game = dotdictify(game_dict)
            if team_key in [game[home_team_key], game[visitor_team_key]]:
                if team_key == game.get(home_team_key):
                    this_opponent = game[visitor_team_key]
                else:
                    this_opponent = game[home_team_key]

                if series_opponent is None:
                    series_opponent = this_opponent

                if this_opponent == series_opponent and 'playoffs' in game:
                    series_games.append(game)

                break
    return series_games[::-1]


def get_games_for_schedule():
    # todo: implement
    return []


def is_playoffs():
    # todo: implement
    return True


def generate_schedule(team_nickname, team_key):
    if is_playoffs():
        games = get_current_series_games(team_nickname, team_key)
    else:
        games = get_games_for_schedule()
    template = ENV.get_template(TEMPLATE_FILE)
    return template.render(games=games)


def replace_schedule_in_sidebar(sidebar_mkd, team_nickname, team_key):
    start_string = settings.schedule['sidebar_schedule_start_string']
    end_string = settings.schedule['sidebar_schedule_end_string']
    schedule_mkd = generate_schedule(team_nickname, team_key)
    mkd_before_sched = sidebar_mkd.split(start_string, 1)[0]
    mkd_after_sched = sidebar_mkd.split(start_string, 1)[1].split(end_string, 1)[1]
    return mkd_before_sched + start_string + schedule_mkd + end_string + mkd_after_sched