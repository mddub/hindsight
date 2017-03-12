import datetime
import os
import re
import sys
from argparse import ArgumentParser
from collections import defaultdict
from datetime import timedelta

from dateutil.parser import parser

date_parser = parser()

SELFSPY_SQLITE_DB = os.path.expanduser('~/.selfspy/selfspy.sqlite')
LIFESLICE_SQLITE_DB = os.path.expanduser('~/Library/Application Support/LifeSlice/lifeslice.sqlite')
SCREENSHOTS_PATH = os.path.expanduser('~/Library/Application Support/LifeSlice/screenshot_thumbs')

arg_parser = ArgumentParser()
arg_parser.add_argument('--date', help='date to view')
arg_parser.add_argument('--screen', default='1', help='screen number')
args, _ = arg_parser.parse_known_args()

if args.date:
    date = date_parser.parse(args.date).date()
else:
    today = datetime.datetime.now()
    date = datetime.date(today.year, today.month, today.day)

files = os.listdir(SCREENSHOTS_PATH)
# screen_2017-01-20T11-00-00Z-0800.png
# screen_2_2017-01-20T11-00-00Z-0800.png
prefix = 'screen_' if args.screen == '1' else 'screen_{}_'.format(args.screen)
matches = filter(None, [re.match(prefix + date.strftime('%Y-%m-%d') + 'T(\d\d)-(\d\d)-(\d\d)Z(-\d{4})\.png', f) for f in files])
hour_minute_to_screenshot = {}
for match in matches:
    filename = match.group()
    hour, minute, second, offset = match.groups()
    hour, minute, second = map(int, (hour, minute, second))
    hour_minute_to_screenshot[(hour, minute)] = filename

include_selfspy_db = False
if include_selfspy_db:
    import sqlite3
    conn = sqlite3.connect(SELFSPY_SQLITE_DB)
    conn.row_factory = sqlite3.Row
    query = 'select * from window inner join process on window.process_id = process.id'
    query += ' where window.created_at >= datetime("' + date.strftime('%Y-%m-%d') + '")'
    query += ' and window.created_at < datetime("' + (date + timedelta(days=1)).strftime('%Y-%m-%d') + '")'
    windows_today = conn.execute(query).fetchall()

    selfspy_hour_minute_to_window_titles = defaultdict(list)
    for window in windows_today:
        _, created_at_str, title, _, _ , _, process_name = window
        created_at = date_parser.parse(created_at_str)
        selfspy_hour_minute_to_window_titles[(created_at.hour, 5 * (created_at.minute / 5))].append('%s %s %s' % (created_at, process_name, title))

include_lifeslice_db = True
if include_lifeslice_db:
    import sqlite3
    conn = sqlite3.connect(LIFESLICE_SQLITE_DB)
    conn.row_factory = sqlite3.Row

    query = 'select datetime, clickCount, cursorDistance from mouse'
    query += ' where interval=5'
    query += ' and datetime like "{}%"'.format(date.strftime('%Y-%m-%d'));
    mouse_periods = conn.execute(query).fetchall()

    lifeslice_hour_minute_to_mouse_distance = defaultdict(int)
    lifeslice_hour_minute_to_mouse_clicks = defaultdict(int)
    for (start_time_str, clicks, distance) in mouse_periods:
        start_time = date_parser.parse(start_time_str)
        lifeslice_hour_minute_to_mouse_distance[(start_time.hour, start_time.minute)] = distance / 1000.0
        lifeslice_hour_minute_to_mouse_clicks[(start_time.hour, start_time.minute)] = clicks / 2.0

    query = 'select datetime, keyCount, wordCount from keyboard'
    query += ' where interval=5'
    query += ' and datetime like "{}%"'.format(date.strftime('%Y-%m-%d'));
    keyboard_periods = conn.execute(query).fetchall()

    lifeslice_hour_minute_to_word_count = defaultdict(int)
    for (start_time_str, key_count, word_count) in keyboard_periods:
        start_time = date_parser.parse(start_time_str)
        lifeslice_hour_minute_to_word_count[(start_time.hour, start_time.minute)] = word_count / 2.0


print '''
<head>
    <meta charset="utf-8">
    <style>
        .screenshot {
            max-height: 68px;
            max-width: 120px;
        }
        .placeholder {
            height: 68px;
            width: 120px;
        }
        .selfspy-window-title-tooltip {
            display: none; top: 68px; left: 0px; width: 400px; min-height: 100px; font-size: 14px; background: beige; position: absolute; z-index: 999;
        }
        .lifeslice-count {
            width: 20px;
            position: absolute;
            bottom: 0;
            opacity: 0.6;
            left: 0;
            background: #ffff99;
            border: 1px solid white;
            border-bottom: none;
        }
        .lifeslice-mouse-clicks {
            left: 21px;
            background: #fdc086;
        }
        .lifeslice-keyboard-word-count {
            left: 42px;
            background: #377eb8;
        }
    </style>
</head>
    <table>
'''
print '<tr><td></td>'
for m in range(0, 60, 5):
    print '<th>%s</th>' % m
print '</tr>'

for h in range(24):
    print '<tr>'
    print '<th>%s</th>' % h
    for m in range(0, 60, 5):
        dom_id = 'windows-%02d%02d' % (h, m)
        mouseover, mouseout = '', ''
        if include_selfspy_db:
            mouseover, mouseout = ['document.querySelector(\'#' + dom_id + '\').style.display = \'%s\';' % d for d in ('inherit', 'none')]
        print '<td style="position: relative;">'
        if (h, m) in hour_minute_to_screenshot:
            print '<img src="{src}" class="screenshot" onmouseover="{mouseover}" onmouseout="{mouseout}">'.format(
                src=SCREENSHOTS_PATH + '/' + hour_minute_to_screenshot[(h, m)],
                mouseover=mouseover,
                mouseout=mouseout,
            )
            if include_selfspy_db:
                print '<div id="' + dom_id + '" class="window-title-tooltip">'
                for window in selfspy_hour_minute_to_window_titles[(h, m)]:
                    print window.encode('UTF-8') + '<br>'
                print '</div>'
        if include_lifeslice_db and sum(
            d[(h, m)] for d in (
                lifeslice_hour_minute_to_mouse_distance,
                lifeslice_hour_minute_to_mouse_clicks,
                lifeslice_hour_minute_to_word_count,
            )
        ) > 0:
            if (h, m) not in hour_minute_to_screenshot:
                print '<div class="placeholder"></div>'
            print '<div class="lifeslice-count lifeslice-mouse-distance" style="height: {height}%"></div>'.format(
                height=lifeslice_hour_minute_to_mouse_distance[(h, m)]
            )
            print '<div class="lifeslice-count lifeslice-mouse-clicks" style="height: {height}%"></div>'.format(
                height=lifeslice_hour_minute_to_mouse_clicks[(h, m)]
            )
            print '<div class="lifeslice-count lifeslice-keyboard-word-count" style="height: {height}%"></div>'.format(
                height=lifeslice_hour_minute_to_word_count[(h, m)]
            )
        print '</td>'
    print '</tr>'

print '</table>'
