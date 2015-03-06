import logging
import urllib2
from bs4 import BeautifulSoup
import socket

logger = logging.getLogger('')


def scrape_standings():
    logger.info("begin standings scrape")
    url = "http://espn.go.com/nba/standings/_/sort/gamesBehind/group/3"
    try:
        standings_html = urllib2.urlopen(url, timeout=2).read()
    except urllib2.URLError, e:
        if isinstance(e.reason, socket.timeout):
            # try once again
            logger.warning("timeout, trying again")
            standings_html = urllib2.urlopen(url, timeout=3).read()
        else:
            logger.error(e)
            raise
    except socket.timeout:
        # For Python 2.7
        logger.warning("timeout, trying again")
        standings_html = urllib2.urlopen(url, timeout=3).read()

    soup = BeautifulSoup(standings_html)
    teams = soup.select('table.tablehead > tr[align] > td:nth-of-type(1) > a')
    standings = {}
    rank = 0
    for team in teams:
        standings[team.string] = dict(
            wins=team.findParent().findNextSibling().string,
            losses=team.findParent().findNextSibling().findNextSibling().string,
            percent=team.findParent().findNextSibling().findNextSibling().findNextSibling().string,
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