{%- macro home_visitor_scores(game) -%}
    {%- if game.home.score != game.visitor.score -%}
        {%- if game.home.score|int > game.visitor.score|int -%}
[{{game.visitor.team_key}}](#TEAM) [{{game.visitor.score}}](#SCORE) [**{{game.home.team_key}}**](#TEAM2) [**{{game.home.score}}**](#SCORE2)
        {%-  else -%}
[**{{game.visitor.team_key}}**](#TEAM) [**{{game.visitor.score}}**](#SCORE) [{{game.home.team_key}}](#TEAM2) [{{game.home.score}}](#SCORE2)
        {%- endif -%}
    {%- else -%}
[{{game.visitor.team_key}}](#TEAM) [{{game.visitor.score}}](#SCORE) [{{game.home.team_key}}](#TEAM2) [{{game.home.score}}](#SCORE2)
    {%- endif -%}
{%- endmacro -%}

{%- for game in games -%}
    {%- if 'playoffs' in game -%}

        {%- if game.period_time.period_status == 'TBD' %}
 - [G{{game.playoffs.game_number}}{% if game.playoffs.game_necessary_flag|int %}*{% endif %} - {{game.date|timestampformat('%Y%m%d', '%-m/%-d')}}](#STATUS) {{home_visitor_scores(game)}} [TBD](#DATE)
        {%- elif game.period_time.game_status == '3' %}
 - [G{{game.playoffs.game_number}} - FINAL](#STATUS) {{home_visitor_scores(game)}} [{{game.date|timestampformat('%Y%m%d', '%b %-d')}}](#DATE)
        {%- elif game.period_time.game_status == '2' %}
 - [{{game.period_time.period_status}} {{game.period_time.game_clock}}](#STATUS) {{home_visitor_scores(game)}} [{{(game.date ~ game.time)|timestampformat('%Y%m%d%H%M', '%-I:%M %p', tzout='America/Chicago')}}](#DATE)
        {%- elif game.period_time.game_status == '1' %}
 - [G{{game.playoffs.game_number}} - {{game.date|timestampformat('%Y%m%d', '%-m/%-d')}}](#STATUS) {{home_visitor_scores(game)}} [{{(game.date ~ game.time)|timestampformat('%Y%m%d%H%M', '%-I:%M %p', tzout='America/Chicago')}}](#DATE)
        {%- endif -%}

    {%- else %}
 - [{{game.date|timestampformat('%Y%m%d', '%b %d')}}](#STATUS) {{home_visitor_scores(game)}} [{{(game.date ~ game.time)|timestampformat('%Y%m%d%H%M', '%-I:%M %p', tzout='America/Chicago')}}](#DATE)
    {%- endif -%}
{%- endfor -%}