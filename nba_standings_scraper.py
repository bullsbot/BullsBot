import logging
import urllib2
from bs4 import BeautifulSoup
import socket

logger = logging.getLogger('NSS')


def scrape_standings(group="division"):
    logger.info("begin standings scrape")
    urls = dict(
        league="http://espn.go.com/nba/standings/_/group/1",
        conference="http://espn.go.com/nba/standings/_/group/2",
        division="http://espn.go.com/nba/standings/_/sort/gamesBehind/group/3")
    try:
        standings_html = urllib2.urlopen(urls[group], timeout=2).read()
    except urllib2.URLError, e:
        if isinstance(e.reason, socket.timeout):
            # try once again
            logger.warning("timeout, trying again")
            standings_html = urllib2.urlopen(urls[group], timeout=3).read()
        else:
            logger.error(e)
            raise
    except socket.timeout:
        # For Python 2.7
        logger.warning("timeout, trying again")
        standings_html = urllib2.urlopen(urls[group], timeout=3).read()

    soup = BeautifulSoup(standings_html)
    teams = soup.select('table.tablehead > tr[align] > td[align] > a')
    standings = {}
    rank = 0
    for team in teams:
        games_behind = team.findParent().findNextSibling().findNextSibling().findNextSibling().findNextSibling().string
        half_game = u'\u00bd' in games_behind
        games_behind = ''.join([i if ord(i) < 128 else '' for i in games_behind.replace(' ', '')])
        if half_game:
            games_behind += '.5'
        elif '-' not in games_behind:
            games_behind += '.0'

        standings[team.string] = dict(
            wins=team.findParent().findNextSibling().string,
            clinched="x - " in str(team.findParent()),
            losses=team.findParent().findNextSibling().findNextSibling().string,
            percent=team.findParent().findNextSibling().findNextSibling().findNextSibling().string,
            behind=games_behind,
            streak=team.findParent().findNextSibling().findNextSibling().findNextSibling()
                        .findNextSibling().findNextSibling().findNextSibling()
                        .findNextSibling().findNextSibling().findNextSibling()
                        .findNextSibling().findNextSibling().findNextSibling().string,
            division_rank=rank
        )
        rank += 1
    logger.info("standings scrape complete")
    return standings


if __name__ == "__main__":
    scrape_standings()