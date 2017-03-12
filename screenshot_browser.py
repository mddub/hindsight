import datetime
import os
import re
import sys
from argparse import ArgumentParser
from collections import defaultdict
from datetime import timedelta

import sqlite3
from dateutil.parser import parser

date_parser = parser()

SQLITE_DB = '/Users/mark/.selfspy/selfspy.sqlite'
SCREENSHOTS_PATH = '/Users/mark/Library/Application Support/LifeSlice/screenshot_thumbs'
#IMG_STYLE = 'max-height: 45px; max-width: 80px;'
IMG_STYLE = 'max-height: 68px; max-width: 120px;'
DIV_STYLE = 'display: none; top: 68px; left: 0px; width: 400px; min-height: 100px; font-size: 14px; background: beige; position: absolute; z-index: 999;'

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

if False:
    hour_minute_to_window_titles = defaultdict(list)
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    query = 'select * from window inner join process on window.process_id = process.id'
    query += ' where window.created_at >= datetime("' + date.strftime('%Y-%m-%d') + '")'
    query += ' and window.created_at < datetime("' + (date + timedelta(days=1)).strftime('%Y-%m-%d') + '")'
    windows_today = conn.execute(query).fetchall()
    for window in windows_today:
        _, created_at_str, title, _, _ , _, process_name = window
        created_at = date_parser.parse(created_at_str)
        hour_minute_to_window_titles[(created_at.hour, 5 * (created_at.minute / 5))].append('%s %s %s' % (created_at, process_name, title))

print '<meta charset="utf-8">'
print '<table><tr><td></td>'
for m in range(0, 60, 5):
    print '<th>%s</th>' % m
print '</tr>'

for h in range(24):
    print '<tr>'
    print '<th>%s</th>' % h
    for m in range(0, 60, 5):
        dom_id = 'windows-%02d%02d' % (h, m)
        mouseover, mouseout = ['document.querySelector(\'#' + dom_id + '\').style.display = \'%s\';' % d for d in ('inherit', 'none')]
        print '<td style="position: relative;">'
        if (h, m) in hour_minute_to_screenshot:
            print '<img src="{src}" style="{style}" onmouseover="{mouseover}" onmouseout="{mouseout}">'.format(
                src=SCREENSHOTS_PATH + '/' + hour_minute_to_screenshot[(h, m)],
                style=IMG_STYLE,
                mouseover=mouseover,
                mouseout=mouseout,
            )
        print '<div id="' + dom_id + '" style="' + DIV_STYLE + '">'
        if False:
            for window in hour_minute_to_window_titles[(h, m)]:
                print window.encode('UTF-8') + '<br>'
        print '</div>'
        print '</td>'
    print '</tr>'

print '</table>'
