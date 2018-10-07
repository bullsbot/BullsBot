from datetime import datetime
import time
import pytz

"""
Settings for bullsbot. Note that this is a python file, so have at it! ... but if it's not python the bot won't load.
Remember to use \n for new lines in your markdown.
"""
reddit = dict(
    username='BullsBot',
    subreddit='chicagobulls'
)

calendar = dict(
    no_date_flag="#NODATE",
    url="https://calendar.google.com/calendar/ical/rlj9ovepenpevlf0rrsgc359fc%40group.calendar.google.com/private-081c866936df070f14242923b4e1bbc3/basic.ics",
)

data = dict(
    scoreboard_url="http://data.nba.com/json/cms/noseason/scoreboard/{date:%Y%m%d}/games.json",
    games_tree="sports_content.games.game",

    # these functions calculate a string given the game object. This output string gets added to the game object
    add_to_game=dict(
        game_datetime=lambda game: pytz.timezone('US/Eastern').localize(datetime.fromtimestamp(
            time.mktime(time.strptime(game['home_start_date'] + game['home_start_time'], '%Y%m%d%H%M')))),
        series_leader=lambda game: (
            game["visitor.team_key"] + ' leads series ' + game['playoffs.visitor_wins'] + '-' + game['playoffs.home_wins']
            if int(game['playoffs.visitor_wins']) > int(game['playoffs.home_wins'])
            else
            game["home.team_key"] + ' leads series ' + game['playoffs.home_wins'] + '-' + game['playoffs.visitor_wins']
            if int(game['playoffs.visitor_wins']) < int(game['playoffs.home_wins'])
            else 'Series tied at ' + game['playoffs.visitor_wins'] + '-' + game['playoffs.home_wins']
        ),
        period_time_str=lambda game: ("G{game[playoffs][game_number]} - " +
                                      ("{dt:%d/%m}" if int(game['period_time.game_status']) == 0
                                       else "{game[period_time][period_status]}"
                                      if game['period_time.game_clock'] == ''
                                      else "Q{game[period_time][period_value]} {game[period_time][game_clock]}")
        ).format(game=game, dt=datetime.fromtimestamp(
            time.mktime(time.strptime(game['home_start_date'] + game['home_start_time'], '%Y%m%d%H%M')))),
    ),
)

team = dict(
    team_data_file="data/teams.csv"
)

standings = dict(
    standings_grouping="conference",    # 'conference' or 'division'
    # we look for these two strings in the sidebar,
    # then replace anything between them with the standings format
    sidebar_standings_start_string="#####**Standings**\nWest|W/L|GB|East|W/L|GB\n:--|:--:|:--:|:--|:--:|:--:\n",
    sidebar_standings_end_string="\n\n",
    # format for the division standings
    division_standings_format="[](#{short_name}){med_name}|{wins}|{losses}|{percent}\n",
    # format for a team in the conference standings (east and west are shown side by side)
    conference_standings_format="*{rank}*[](#{short_name})|{wins}-{losses}|{behind}"
)

bot = dict(
    team_name="Chicago Bulls",               # must match a team in teams.csv
    timezone='America/Los_Angeles',          # time zone name (see wikipedia.org/wiki/List_of_tz_database_time_zones)
    non_game_day_update_freq=60 * 60 * 10,   # every 10 hours on non-game days
    game_day_update_freq=60 * 60,            # every hour on game days
    near_game_update_freq=60 * 5,            # every 5 minutes as we approach game time
    game_time_update_freq=60 * 1.5,          # every 1.5 minutes once the game has started
    game_thread_create_time=60 * 60         # how many seconds before tip-off should game threads be created
)

schedule = dict(
    update_schedule=True,
    max_events_to_display=14,
    prior_events_to_display=3,
    min_events_to_display=10,
    sidebar_schedule_start_string="> ",   # the schedule begins after this line(s)
    sidebar_schedule_end_string="\n\n",     # and ends just before this line(s)
    # event_fmt is for events in the calendar like [NBA Draft]{#DRAFT} [MONTH DAY]{#D}
    event_fmt="[{event_title}]({event_hashtag}) [{month_day}](#D)\n",
    # GAME FMT OPTIONS:
    # {away_score} {away_team_short}
    # {home_score} {home_team_short} {month_day} {game_status} {game_time_local}
    # FYI: the winning team will get ** around their 'team_short'
    past_game_fmt="[{away_team_short}](#T1)[{away_score}](#S1)[{home_team_short}](#T2)[{home_score}](#S2)[FINAL](#ST)[{month_day}](#DT)\n",
    current_game_fmt="[{away_team_short}](#T1)[{away_score}](#S1)[{home_team_short}](#T2)[{home_score}](#S2)[{game_status}](#ST)[{month_day}](#DT)\n",
    future_game_fmt="[{away_team_short}](#T1)[](#S1)[{home_team_short}](#T2)[](#S2)[{month_day}](#ST)[{game_time_local}](#DT)\n",
    # game_thread_link is added before past_game_fmt and current_game_fmt
    game_thread_link_fmt="[]({link})",
    event_markdown_pre=" - ",   # goes before each game/event
    event_markdown_post="",     # goes after each game/event
)

thread = dict(
    # POST GAME THREAD OPTIONS:
    # {home_team_short} {home_team_name} {home_team_win_loss} {home_score} {full_date} {link_date}
    # {home_team_short} {away_team_name} {away_team_win_loss} {away_score}
    post_game_thread_fmt="HOME TEAM|FINAL SCORE|AWAY TEAM\n:--:|:--:|:--:\n[](#{home_team_short}){home_team_name}*{home_team_win_loss}*|**{home_score}-{away_score}** *{full_date}* *[BOX SCORE](http://www.nba.com/games/{link_date}/{away_team_short}{home_team_short}/gameinfo.html#nbaGIboxscore)*|[](#{away_team_short}){away_team_name}*{away_team_win_loss}*\n",

    # POST GAME THREAD TITLE OPTIONS:
    # {sub_team_name} {sub_team_win_loss} {sub_score} {beat_or_lose}
    # {non_sub_team_name} {non_sub_team_win_loss} {non_sub_score}
    post_game_thread_title_fmt="POST GAME: {sub_team_name} ({sub_team_win_loss}) {beat_or_lose} {non_sub_team_name} ({non_sub_team_win_loss}) ({sub_score}-{non_sub_score})",
    # just add any timezone and it'll be replaced by the time in
    pre_game_thread_fmt="----\n- [](#{home_team_short})\n- [{home_team_name}](#HT) [{home_team_win_loss}](#HR) /r/{home_subreddit}\n- [VS.](#VS)\n- [{away_team_name}](#AT) [{away_team_win_loss}](#AR) /r/{away_subreddit}\n- [](#{away_team_short})\n\n----\n----\n- *Gametime* [Box score](http://www.nba.com/games/{link_date}/{away_team_short}{home_team_short}/gameinfo.html#nbaGIboxscore) [Game story](http://www.nba.com/games/{link_date}/{away_team_short}{home_team_short}/gameinfo.html)\n- [](#US)[*Eastern:***{US/Eastern}**](#TM) [*Central:***{US/Central}**](#TM) [*Mountain:***{US/Mountain}**](#TM) [*Pacific:***{US/Pacific}**](#TM)\n- [](#EU) [*UK:***{Europe/London}**](#TM) [*CET:***{Europe/Paris}**](#TM) [*GMT+2:***{Europe/Helsinki}**](#TM) [*GMT+3:***{Europe/Minsk}**](#TM)\n\n----\n- *Location:* {location}\n- *Broadcast:* {broadcast}\n- *Discuss:* [Reddit Stream](http://reddit-stream.com/)",
    pre_game_thread_title_fmt="PRE GAME: {home_team_name} vs. {away_team_name} ({month_day_year})",
    pre_game_date_fmt="%A***%b %d***%Y",
    current_game_thread_fmt="HOME TEAM|GAME THREAD|AWAY TEAM\n:--:|:--:|:--:\n[](#{home_team_short}){home_team_name}*{home_team_win_loss}*|**{home_score}-{away_score}** *VERSUS* *[BOX SCORE](http://www.nba.com/games/{link_date}/{away_team_short}{home_team_short}/gameinfo.html#nbaGIboxscore)*|[](#{away_team_short}){away_team_name}*{away_team_win_loss}*\n[](#empty)|*Eastern* **{game_time_eastern}**|[](#empty)\nSubreddit|*Central* **{game_time_central}**|Subreddit\n/r/{home_subreddit}|*Mountain* **{game_time_mountain}**|/r/{away_subreddit}\n[](#empty)|*Pacific* **{game_time_pacific}**|[](#empty)\n\n[](#empty)|INFORMATION|[](#empty)\n:--|:--|:--\n[](#empty)|*BROADCAST* {broadcast}|[](#empty)\n[](#empty)|*STREAMS* TBD|[](#empty)\n[](#empty)|*DISCUSS* [Reddit Steam](http://reddit-stream.com/)|[](#empty)\n",
    current_game_thread_split_text="[](#empty)|INFORMATION",
    game_thread_title_fmt="GAME THREAD: {home_team_name} vs. {away_team_name}",
    game_thread_title_date_fmt="%b %d, %Y",
    playoff_pre_game_thread_title_fmt="PRE GAME: {visitor.city} {visitor.nickname} vs. {home.city} {home.nickname} [{series_leader}]",
    playoff_game_thread_title_fmt="PLAYOFFS GAME {playoffs.game_number}: {visitor.city} {visitor.nickname} vs. {home.city} {home.nickname} [{series_leader}]",
    game_thread_flairs=dict(
        game='playoffs',
        pre='pregame',
        post='postgame'
    )
)
