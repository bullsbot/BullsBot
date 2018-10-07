import logging
import time as time_
from urllib.request import urlopen
import urllib.error
import json
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
        games_json = fetch_nba_games_json(date)                     # fetch html from nba.com
        games = parse_nba_games_json(games_json)                    # scrape for game info
        all_games_cache[date.strftime(date_format)] = games, time   # cache game info
    return games


def fetch_json(url):
    json_games = ''
    try:
        with urlopen(url) as games_url:
            json_games = json.loads(games_url.read().decode())
    except urllib.error.HTTPError as e:
        if isinstance(e.reason, socket.timeout):
            # try once again
            logger.warning("timeout, trying again")
            with urlopen(url) as games_url:
                json_games = json.loads(games_url.read().decode())
        else:
            logger.error(e)
            raise
    return json_games


def fetch_nba_games_json(date):
        # todo: try-catch if more timeouts?
        date_format = "%Y%m%d"
        scores_url = "http://data.nba.com/prod/v2/" + date.strftime(date_format) + "/scoreboard.json"
        logger.info("Fetching " + scores_url)
        return fetch_json(scores_url)


def parse_nba_games_json(games_json):
        logger.debug("Begin Scrape")
        game_containers = games_json["games"]
        # create dict
        games = {}
        for i, game_container in enumerate(game_containers):
            # logger.debug("Scraping game " + str(i))
            game = {}
            # find game status
            if game_container['statusNum'] == 1:
                game['current_status'] = 'PRE'
                game['game_status'] = 'PRE'
            elif game_container['statusNum'] == 2:
                game['current_status'] = str(game_container['clock']) + ' ' + str(game_container['period']['current']) + 'Q'
                game['game_status'] = str(game_container['clock']) + ' ' + str(game_container['period']['current']) + 'Q'
            elif game_container['statusNum'] == 3:
                game['current_status'] = 'FINAL'
                game['game_status'] = 'FINAL'
            # find away team
            game['away_team'] = game_container["vTeam"]["triCode"]
            # find home team
            game['home_team'] = game_container["hTeam"]["triCode"]
            # find scores if they exist
            if not game_container['statusNum'] == 1:
                game['home_score'] = game_container['hTeam']['score']
                game['away_score'] = game_container['vTeam']['score']
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
