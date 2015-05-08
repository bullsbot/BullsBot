from datetime import datetime
import time
import pytz

"""
Settings for bullsbot. Note that this is a python file, so have at it! ... but if it's not python the bot won't load.
Remember to use \n for new lines in your markdown.
"""
reddit = dict(
    username='BullsBot',
    # subreddit='chicagobulls'
)

calendar = dict(
    no_date_flag="#NODATE",
    url="https://www.google.com/calendar/ical/chicagobullsbot%40gmail.com/private-48b0043bc03da315706a2ca595c0e63b/basic.ics",
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
    update_standings=False,
    standings_grouping="conference",
    sidebar_standings_start_string="####**Playoffs Seeding**\nWest|W/L|GB|East|W/L|GB\n:--|:--:|:--:|:--|:--:|:--:\n",
    sidebar_standings_end_string="\n\n",
    division_standings_format="[](#{short_name}){med_name}|{wins}|{losses}|{percent}\n",
    conference_standings_format="*{rank}*[](#{short_name})|{wins}-{losses}|{behind}"
)

bot = dict(
    team_name="Chicago Bulls",
    timezone='America/Los_Angeles',
    non_game_day_update_freq=60 * 60 * 10, # every 10 hours on non-game days
    game_day_update_freq=60 * 60, # every hour on game days
    near_game_update_freq=60 * 5, # every 5 minutes as we approach game time
    game_time_update_freq=60 * 1.5, # every 1.5 minutes once the game has started
    game_thread_create_time=60 * 60         # how many seconds before tip-off should game threads be created
)

schedule = dict(
    update_schedule=True,
    max_events_to_display=14,
    prior_events_to_display=3,
    min_events_to_display=10,
    sidebar_schedule_start_string="* **Schedule**",
    sidebar_schedule_end_string="\n\n",
    markdown_template_file="schedule.markdown",
    game_dates_url="http://www.nba.com/gameline/{}/",
    event_fmt="[{event_title}]({event_hashtag}) [{month_day}](#DESC)\n",
    past_game_fmt="[{game_status}](#STATUS) [{away_team_short}](#TEAM) [{away_score}](#SCORE) [{home_team_short}](#TEAM2) [{home_score}](#SCORE2) [{month_day}](#DATE)\n",
    current_game_fmt="[{game_status}](#STATUS) [{away_team_short}](#TEAM) [{away_score}](#SCORE) [{home_team_short}](#TEAM2) [{home_score}](#SCORE2) [{month_day}](#DATE)\n",
    future_game_fmt="[{month_day}](#STATUS) [{away_team_short}](#TEAM) [](#SCORE) [{home_team_short}](#TEAM2) [](#SCORE2) [{game_time_local}](#DATE)\n",
    game_thread_link_fmt="[]({link})",
    event_markdown_pre=" - ", # goes before each game/event
    event_markdown_post="", # goes after each game/event
)

thread = dict(
    create_game_threads=True,
    post_game_thread_fmt="HOME TEAM|FINAL SCORE|AWAY TEAM\n:--:|:--:|:--:\n[](#{home_team_short}){home_team_name}*{home_team_win_loss}*|**{home_score}-{away_score}** *{full_date}* *[BOX SCORE](http://www.nba.com/games/{link_date}/{away_team_short}{home_team_short}/gameinfo.html#nbaGIboxscore)*|[](#{away_team_short}){away_team_name}*{away_team_win_loss}*\n",
    post_game_thread_title_fmt="POST GAME: {sub_team_name} {beat_or_lose} {non_sub_team_name}",
    pre_game_thread_fmt="HOME TEAM|INFORMATION|AWAY TEAM\n:--:|:--:|:--:\n[](#{home_team_short}){home_team_name}*{home_team_win_loss}*|*{full_date}*|[](#{away_team_short}){away_team_name}*{away_team_win_loss}*\n\n[](#empty)|DETAILED OVERVIEW|[](#empty)\n:--|:--|:--\n[](#empty)|*BROADCAST* {broadcast}|[](#empty)\n[](#empty)|*GAME TIMES* [Eastern: {game_time_eastern}](#TIME) / [Central: {game_time_central}](#TIME) / [Mountain: {game_time_mountain}](#TIME) / [Pacific:  {game_time_pacific}](#TIME)|[](#empty)\n[](#empty)|*MISC/NOTES* [Game Story](http://www.nba.com/games/{link_date}/{away_team_short}{home_team_short}/gameinfo.html)|[](#empty)\n[](#empty)|*SUBREDDITS* /r/{home_subreddit} / /r/{away_subreddit}|[](#empty)\n",
    pre_game_thread_title_fmt="PRE GAME: {home_team_name} vs. {away_team_name} ",
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

jinja = dict(
    loader='jinja_loader',
    templates_folder='templates'
)