import urllib2
from bs4 import BeautifulSoup
import socket


def scrape_standings():
    print "begin standings scrape"
    url = "http://espn.go.com/nba/standings/_/group/3"
    try:
        standings_html = urllib2.urlopen(url, timeout=2).read()
    except urllib2.URLError, e:
        if isinstance(e.reason, socket.timeout):
            # try once again
            print "timeout, trying again"
            standings_html = urllib2.urlopen(url, timeout=3).read()
        else:
            raise
    except socket.timeout:
        # For Python 2.7
        print "timeout, trying again"
        standings_html = urllib2.urlopen(url, timeout=3).read()

    soup = BeautifulSoup(standings_html)
    teams = soup.select('table.tablehead > tr[align] > td:nth-of-type(1) > a')
    standings = {}
    for team in teams:
        standings[team.string] = dict(
            wins=team.findParent().findNextSibling().string,
            losses=team.findParent().findNextSibling().findNextSibling().string,
            percent=team.findParent().findNextSibling().findNextSibling().findNextSibling().string
        )
    print "standings scrape complete"
    return standings


if __name__ == "__main__":
    scrape_standings()