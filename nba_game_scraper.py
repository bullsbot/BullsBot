import time as time_
import urllib2
from bs4 import BeautifulSoup
import socket


def get_games(date, time_till_stale=10800):
    """
    time_till_stale is in seconds
    """
    if 'all_games_cache' not in globals():
        global all_games_cache
        all_games_cache = {}
    date_format = "%Y%m%d"
    time = time_.time()
    cache_is_fresh = True
    try:
        games, cached_at = all_games_cache[date.strftime(date_format)]  # look in cache
        if cached_at < (time - time_till_stale):
            cache_is_fresh = False
    except KeyError:                                                # if not in cache
        cache_is_fresh = False

    if not cache_is_fresh:
        games_html = fetch_nba_games_html(date)                     # fetch html from nba.com
        games = parse_nba_games_html(games_html)                    # scrape for game info
        all_games_cache[date.strftime(date_format)] = games, time   # cache game info
    return games


def fetch_nba_games_html(date):
        # todo: try-catch if more timeouts?
        date_format = "%Y%m%d"
        scores_url = "http://www.nba.com/gameline/"
        print "Fetching " + scores_url + date.strftime(date_format)
        try:
            game_html = urllib2.urlopen(scores_url + date.strftime(date_format), timeout=2).read()
        except urllib2.URLError, e:
            if isinstance(e.reason, socket.timeout):
                # try once again
                print "timeout, trying again"
                game_html = urllib2.urlopen(scores_url + date.strftime(date_format), timeout=3).read()
            else:
                raise
        except socket.timeout:
            # For Python 2.7
            print "timeout, trying again"
            game_html = urllib2.urlopen(scores_url + date.strftime(date_format), timeout=3).read()

        print "Fetched"
        return game_html


def parse_nba_games_html(games_html):
        print "Begin Scrape"
        soup = BeautifulSoup(games_html)
        game_containers = soup.select('.GameLine')
        # create dict
        games = {}
        for i, game_container in enumerate(game_containers):
            print "Scraping game ", str(i)
            game = {}
            # get container id
            container_id = game_container['id']
            # find game status
            status = game_container['class'][0].strip().upper()
            game['current_status'] = game_container['class'][0].strip().upper()
            if status == "LIVE" or status == "LIVEOT":
                # show quarter and time if live
                game['game_status'] = soup.select('#'+container_id + ' div[class$="Status"] [class="nbaLiveStatTxSm"]')[0].string.upper().replace('"', '')
            elif status == "PRE":
                # leave as PRE if pre, we can look for this later and replace with a localized time
                game['game_status'] = status
            else:
                # otherwise, show the status we find
                game['game_status'] = soup.select('#'+container_id + ' div[class$="Status"] [class$="StatTx"]')[0].string
            # find away team
            game['away_team'] = soup.select('#'+container_id + ' div[class$="TeamAw"] [class$="TeamName"]')[0].string.upper()
            # find home team
            game['home_team'] = soup.select('#'+container_id + ' div[class$="TeamHm"] [class$="TeamName"]')[0].string.upper()
            # find scores if they exist
            away_score_containers = soup.select('#'+container_id + ' div[class$="TeamAw"] [class*="TeamNum"]')
            if len(away_score_containers) > 0:
                game['away_score'] = away_score_containers[0].string
                game['home_score'] = soup.select('#'+container_id + ' div[class$="TeamHm"] [class*="TeamNum"]')[0].string
            # add to list of games
            games[game['away_team'] + '_' + game['home_team']] = game
        print "Scrape complete."
        return games


