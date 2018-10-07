import logging
from urllib.request import urlopen
import urllib.error
from bs4 import BeautifulSoup
import socket

logger = logging.getLogger('NSS')


def scrape_standings(group="division"):
    logger.info("begin standings scrape")
    urls = dict(
        conference="",
        division="")
    try:
        standings_html = urlopen(urls[group], timeout=2).read()
    except urllib.error.HTTPError as e:
        if isinstance(e.reason, socket.timeout):
            # try once again
            logger.warning("timeout, trying again")
            standings_html = urlopen(urls[group], timeout=3).read()
        else:
            logger.error(e)
            raise

    soup = BeautifulSoup(standings_html.replace('<html class="ie9">', '').replace('<html class="ie8">', ''))
    teams = soup.select('td.team > a')
    standings = {}
    rank = 0
    for team in teams:
        standings[team.string.replace('.', '')] = dict(
            clinched="x" in str(team.findParent()) or "e" in str(team.findParent()) or "w" in str(team.findParent()),
            elimintated="o" in str(team.findParent()),
            wins=team.findParent().findNextSibling().string,
            losses=team.findParent().findNextSibling().findNextSibling().string,
            percent=team.findParent().findNextSibling().findNextSibling().findNextSibling().string,
            behind=team.findParent().findNextSibling().findNextSibling().findNextSibling().findNextSibling().string,
            streak=team.findParent().findNextSibling().findNextSibling().findNextSibling().findNextSibling().findNextSibling().findNextSibling().findNextSibling().findNextSibling().findNextSibling().findNextSibling().string,
            division_rank=rank
        )
        rank += 1
    logger.info("standings scrape complete")
    return standings


if __name__ == "__main__":
    scrape_standings()
