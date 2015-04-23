import logging
import urllib2
from bs4 import BeautifulSoup
import socket

logger = logging.getLogger('NSS')


def scrape_standings(group="division"):
    logger.info("begin standings scrape")
    urls = dict(
        conference="http://www.nba.com/standings/team_record_comparison/conferenceNew_Std_Cnf.html",
        division="http://www.nba.com/standings/team_record_comparison/conferenceNew_Std_Div.html")
    try:
        standings_html = urllib2.urlopen(urls[group], timeout=5).read()
    except urllib2.URLError, e:
        if isinstance(e.reason, socket.timeout):
            # try once again
            logger.warning("timeout, trying again")
            standings_html = urllib2.urlopen(urls[group], timeout=15).read()
        else:
            logger.error(e)
            raise
    except socket.timeout:
        # For Python 2.7
        logger.warning("timeout, trying again")
        standings_html = urllib2.urlopen(urls[group], timeout=15).read()

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