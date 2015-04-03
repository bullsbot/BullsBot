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

team = dict(
    team_data_file="data/teams.csv"
)

standings = dict(
    standings_grouping="conference",
    sidebar_standings_start_string="#####**Standings**\nWest|W/L|GB|East|W/L|GB\n:--|:--:|:--:|:--|:--:|:--:\n",
    sidebar_standings_end_string="\n\n",
    division_standings_format="[](#{short_name}){med_name}|{wins}|{losses}|{percent}\n",
    conference_standings_format="*{rank}*[](#{short_name})|{wins}-{losses}|{behind}"
)

bot = dict(
    team_name="Chicago Bulls",
    timezone='America/Los_Angeles',
    non_game_day_update_freq=60 * 60 * 10,   # every 10 hours on non-game days
    game_day_update_freq=60 * 60,            # every hour on game days
    near_game_update_freq=60 * 5,            # every 5 minutes as we approach game time
    game_time_update_freq=60 * 1.5,          # every 1.5 minutes once the game has started
    game_thread_create_time=60 * 60         # how many seconds before tip-off should game threads be created
)

schedule = dict(
    max_events_to_display=14,
    prior_events_to_display=3,
    min_events_to_display=10,
    sidebar_schedule_start_string="> \n",   # the schedule begins after this line(s)
    sidebar_schedule_end_string="\n\n",     # and ends just before this line(s)
    # event_fmt is for events in the calendar like [NBA Draft]{#DRAFT} [MONTH DAY]{#DESC}
    event_fmt="[{event_title}]({event_hashtag}) [{month_day}](#DESC)\n",
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

    pre_game_thread_fmt="HOME TEAM|INFORMATION|AWAY TEAM\n:--:|:--:|:--:\n[](#{home_team_short}){home_team_name}*{home_team_win_loss}*|*{full_date}*|[](#{away_team_short}){away_team_name}*{away_team_win_loss}*\n\n[](#empty)|DETAILED OVERVIEW|[](#empty)\n:--|:--|:--\n[](#empty)|*BROADCAST* {broadcast}|[](#empty)\n[](#empty)|*GAME TIMES* [Eastern: {game_time_eastern}](#TIME) / [Central: {game_time_central}](#TIME) / [Mountain: {game_time_mountain}](#TIME) / [Pacific:  {game_time_pacific}](#TIME)|[](#empty)\n[](#empty)|*MISC/NOTES* [Game Story](http://www.nba.com/games/{link_date}/{away_team_short}{home_team_short}/gameinfo.html)|[](#empty)\n[](#empty)|*SUBREDDITS* /r/{home_subreddit} / /r/{away_subreddit}|[](#empty)\n",
    pre_game_thread_title_fmt="PRE GAME: {home_team_name} ({home_team_win_loss}) vs. {away_team_name} ({away_team_win_loss}) ({month_day_year})",
    pre_game_date_fmt="%A***%b %d***%Y",
    current_game_thread_fmt="HOME TEAM|GAME THREAD|AWAY TEAM\n:--:|:--:|:--:\n[](#{home_team_short}){home_team_name}*{home_team_win_loss}*|**{home_score}-{away_score}** *VERSUS* *[BOX SCORE](http://www.nba.com/games/{link_date}/{away_team_short}{home_team_short}/gameinfo.html#nbaGIboxscore)*|[](#{away_team_short}){away_team_name}*{away_team_win_loss}*\n[](#empty)|*Eastern* **{game_time_eastern}**|[](#empty)\nSubreddit|*Central* **{game_time_central}**|Subreddit\n/r/{home_subreddit}|*Mountain* **{game_time_mountain}**|/r/{away_subreddit}\n[](#empty)|*Pacific* **{game_time_pacific}**|[](#empty)\n\n[](#empty)|INFORMATION|[](#empty)\n:--|:--|:--\n[](#empty)|*BROADCAST* {broadcast}|[](#empty)\n[](#empty)|*STREAMS* TBD|[](#empty)\n[](#empty)|*DISCUSS* [Reddit Steam](http://reddit-stream.com/)|[](#empty)\n",
    current_game_thread_split_text="[](#empty)|INFORMATION",
    game_thread_title_fmt="GAME THREAD: {home_team_name} ({home_team_win_loss}) vs. {away_team_name} ({away_team_win_loss}) ({month_day_year})",
    game_thread_title_date_fmt="%b %d, %Y",
    game_thread_flairs=dict(
        game='gamethread',
        pre='pregame',
        post='postgame'
    )
)