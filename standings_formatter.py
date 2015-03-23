__author__ = 'nmew'


class StandingsFormatter(object):
    def __init__(self, team_dict, team_dict_med_key, team_name,
                 league_standings_format='{short_name} {med_name} {wins}/{losses} {percent}',
                 conference_standings_format='{short_name} {med_name} {wins}/{losses} {percent}',
                 division_standings_format='{short_name} {med_name} {wins}/{losses} {percent}'):
        self.team_dict = team_dict
        self.team_dict_med_key = team_dict_med_key
        self.team_name = team_name
        self.conference_standings_format = conference_standings_format
        self.division_standings_format = division_standings_format

    def get_formatter(self, group):
        """
        Returns the appropriate standings formatter method for a particular group
        (as defined in espn standings). The group can be either 'league', 'conference' or 'division'

        :param group: A string, either 'league', 'conference' or 'division' defining how standings are formatted
        """
        return getattr(self, "format_" + group + "_standings")

    def format_league_standings(self, standings):
        raise NotImplementedError

    def format_conference_standings(self, standings):
        sorted_team_standings = sorted(standings.items(), key=lambda t: float(t[1]['division_rank']))
        division = self.team_dict[self.team_name]['division']
        standings_string = ""
        for med_name, team_standings in sorted_team_standings:
            if self.team_dict_med_key[med_name]['division'] == division:
                standings_string += self.conference_standings_format.format(
                    short_name=self.team_dict_med_key[med_name]['short_name'],
                    med_name=med_name,
                    wins=team_standings['wins'],
                    losses=team_standings['losses'],
                    percent=team_standings['percent']
                )
        return standings_string.rstrip("\n")

    def format_division_standings(self, standings):
        sorted_team_standings = sorted(standings.items(), key=lambda t: float(t[1]['division_rank']))
        division = self.team_dict[self.team_name]['division']
        standings_string = ""
        for med_name, team_standings in sorted_team_standings:
            if self.team_dict_med_key[med_name]['division'] == division:
                standings_string += self.division_standings_format.format(
                    short_name=self.team_dict_med_key[med_name]['short_name'],
                    med_name=med_name,
                    wins=team_standings['wins'],
                    losses=team_standings['losses'],
                    percent=team_standings['percent']
                )
        return standings_string.rstrip("\n")