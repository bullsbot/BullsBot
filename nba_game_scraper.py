import logging
import time as time_
import urllib2
from bs4 import BeautifulSoup
import socket

logger = logging.getLogger('NGS')

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


def fetch_html(url):
    html = ''
    try:
        html = urllib2.urlopen(url, timeout=2).read()
    except urllib2.URLError, e:
        if isinstance(e.reason, socket.timeout):
            # try once again
            logger.warning("timeout, trying again")
            html = urllib2.urlopen(url, timeout=3).read()
        else:
            logger.error(e)
            raise
    except socket.timeout:
        # For Python 2.7
        logger.warning("timeout, trying again")
        html = urllib2.urlopen(url, timeout=3).read()
    return html


def fetch_nba_games_html(date):
        # todo: try-catch if more timeouts?
        date_format = "%Y%m%d"
        scores_url = "http://www.nba.com/gameline/"
        logger.info("Fetching " + scores_url + date.strftime(date_format))
        return fetch_html(scores_url + date.strftime(date_format))


def parse_nba_games_html(games_html):
        logger.debug("Begin Scrape")
        soup = BeautifulSoup(games_html)
        game_containers = soup.select('.GameLine')
        # create dict
        games = {}
        for i, game_container in enumerate(game_containers):
            # logger.debug("Scraping game " + str(i))
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
        logger.info("Scrape complete. {} games found.".format(len(games)))
        return games


def scrape_broadcast_info(date, home_team_short, away_team_short):
    broadcasts = dict(
        local=[],
        national=[]
    )
    url = "http://www.nba.com/games/{date}/{away_team_short}{home_team_short}/gameinfo.html"
    url_date_format = "%Y%m%d"
    game_info_url = url.format(
        date=date.strftime(url_date_format),
        away_team_short=away_team_short,
        home_team_short=home_team_short
    )
    html = fetch_html(game_info_url)
    soup = BeautifulSoup(html)
    broadcasts_rows = soup.select('table#nbaGITvInfo > tr')
    for row in broadcasts_rows:
        children = list(row.children)
        children.reverse()
        if len(children) > 3 and children[1].string is not None and children[1].string.strip().lower() in broadcasts:
            broadcasts[children[1].string.strip().lower()].append(children[2].string.strip())

    return broadcasts

if __name__ == "__main__":
    import datetime
    broadcast_info = scrape_broadcast_info(datetime.date.fromordinal(datetime.date.today().toordinal()-1), "CHI", "MIN")

    # broadcast_info = nba_game_scraper.scrape_broadcast_info(datetime.now(local_timezone),
    #                                                    game_data['home_team'].upper(),
    #                                                    game_data['away_team'].upper())
    broadcast_strings = []
    for key, channels in broadcast_info.iteritems():
        if len(channels) > 0:
            broadcast_strings.append(key.capitalize() + ": **" + "** ~~/~~ **".join(channels) + "**")
    broadcast = "  ~~/~~  ".join(broadcast_strings)
    logger.info(broadcast)