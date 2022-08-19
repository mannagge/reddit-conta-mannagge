#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""All mannaggias are beautiful: let's count them!"""

import os
import re
import random
import sqlite3
import argparse

import praw
import prawcore

VERSION = '1.0'

DB_PATH = '/contamannagge/data'
DB_FILENAME = 'mannagge.db'
DB_FILE = os.path.join(DB_PATH, DB_FILENAME)

DB_TABLE = 'mannagge (id INTEGER PRIMARY KEY AUTOINCREMENT, created_utc INTEGER, author_id CHAR(8), author_name CHAR(20), comment_id CHAR(8), link_id CHAR(10), permalink CHAR(384), mannaggia TEXT)'
DB_INSERT = 'INSERT INTO mannagge (created_utc, author_id, author_name, comment_id, link_id, permalink, mannaggia) VALUES (?, ?, ?, ?, ?, ?, ?)'

GREETINGS = (
    'molto bene /u/%(author_name)s, anche oggi hai mannaggiato!',
    'grande /u/%(author_name)s, che gran bella mannaggia che hai tirato!',
    'sorbole /u/%(author_name)s, oggi sei proprio in vena di mannagge...',
    'mi è semblato di sentile una mannaggia, /u/%(author_name)s...',
    'lo avete sentito tutti, signore e signori! Ebbene sì, /u/%(author_name)s ha mannaggiato!',
    'tutte le mannagge sono belle, /u/%(author_name)s, ma la tua è veramente stupenda!',
    'c\'è una mannaggia che cresce in me... ma vedo che /u/%(author_name)s mi ha preceduto!',
    'una mannaggia al giorno, leva il medico di torno, e /u/%(author_name)s lo sa bene!',
    'siamo fieri di te, /u/%(author_name)s: questa è proprio una bella mannaggia!')

REPLY_TMPL = """%(greeting)s

Finora ho assistito a %(total_mannagge)d mannagge, di cui %(total_from_author)d da te.

Gli utenti più mannaggeri sono: ^(però non fate a gara: le mannagge vi devono uscire dal cuore <3)

%(mannaggetors)s

Le vostre mannagge preferite:

%(top_mannagge)s

^(Sono un umile bot; se volete vedere come sono fatto dentro, il mio codice è [qui](%(homepage)s))
"""

re_cit = re.compile(r'^>.*\n?', re.M)
re_targeted_mannagge = re.compile(
    r'\b(mannagg(?:ia|e)\s+.*?(?=[!\.\(;\?:\n]|$))', re.M | re.I)
re_loose_mannagge = re.compile(r'(mannagg[ie][a-z]*)\b', re.I)


def extractMannagge(body):
    """Return a list of mannagge from a string."""
    # strip quotes
    body = re_cit.sub('', body)
    targeted = re_targeted_mannagge.findall(body)
    body = re_targeted_mannagge.sub('', body)
    loose = re_loose_mannagge.findall(body)
    return [mannaggia.strip() for mannaggia in targeted + loose]


def buildReply(cfgArgs, author_name, mannagge):
    """Prepare a reply to celebrate a mannaggia."""
    conn = connectAndPrepare()
    curs = conn.cursor()
    curs.execute('SELECT COUNT(*) FROM mannagge')
    total_mannagge = curs.fetchone()[0]
    curs.execute(
        'SELECT COUNT(*) FROM mannagge WHERE author_name = ?', (author_name,))
    total_from_author = curs.fetchone()[0]
    args = dict(author_name=author_name, total_mannagge=total_mannagge,
                total_from_author=total_from_author)
    args['greeting'] = random.choice(GREETINGS) % args
    curs.execute(
        'SELECT author_name, COUNT(*) FROM mannagge GROUP BY author_name ORDER BY COUNT(*) DESC LIMIT 5')
    mannagging_users = curs.fetchall()
    args['mannaggetors'] = '\n'.join(
        ['* /u/%s: %d %s' % (raw[0], raw[1], 'mannaggia' if raw[1] == 1 else 'mannagge') for raw in mannagging_users])
    curs.execute(
        'SELECT mannaggia, COUNT(*) FROM mannagge GROUP BY mannaggia ORDER BY COUNT(*) DESC LIMIT 5')
    top_mannagge = curs.fetchall()
    args['top_mannagge'] = '\n'.join(
        ['* %s: %d %s' % (raw[0], raw[1], 'volta' if raw[1] == 1 else 'volte') for raw in top_mannagge])
    args['username'] = cfgArgs.username
    args['homepage'] = cfgArgs.homepage
    msg = REPLY_TMPL % args
    return msg


def connectAndPrepare():
    """Connect to the database and build the required indices."""
    try:
        os.makedirs(DB_PATH)
    except FileExistsError:
        pass
    conn = sqlite3.connect(DB_FILE)
    curs = conn.cursor()
    curs.execute('CREATE TABLE IF NOT EXISTS %s' % DB_TABLE)
    for col in 'created_utc', 'author_name', 'mannaggia':
        try:
            curs.execute(
                'CREATE INDEX mannaggia_%s_idx ON mannagge (%s)' % (col, col))
        except sqlite3.OperationalError:
            continue
    curs.close()
    return conn


def storeMannagge(created_utc, author, comment_id, link_id, permalink, mannagge):
    """Store our precious mannaggia to the database."""
    conn = connectAndPrepare()
    curs = conn.cursor()
    for mannaggia in mannagge:
        curs.execute(DB_INSERT, (int(created_utc), author.id,
                     author.name, comment_id, link_id, permalink, mannaggia))
    conn.commit()
    curs.close()
    conn.close()


def listen(args):
    """Begin counting mannagge."""
    reddit = praw.Reddit(username=args.username,
                         password=args.password,
                         client_id=args.client_id,
                         client_secret=args.client_secret,
                         user_agent=args.user_agent)
    try:
        print('I: start listening for mannagge on %s' % args.subs)
        for comment in reddit.subreddit(args.subs).stream.comments(skip_existing=True):
            try:
                if comment.edited:
                    continue
                created_utc = comment.created_utc
                author = comment.author
                comment_id = comment.id
                link_id = comment.link_id
                permalink = comment.permalink
                body = comment.body
                mannagge = extractMannagge(body)
                if author.name == args.username:
                    continue
                if not mannagge:
                    continue
                print('I: at %s user %s mannagged in a post (id: %s, link_id: %s, permalink: %s): %s' % (created_utc,
                        author, comment_id, link_id, permalink, ' | '.join(mannagge)))
                storeMannagge(created_utc, author, comment_id,
                              link_id, permalink, mannagge)
                replyMsg = buildReply(args, author.name, mannagge)
                try:
                    comment.reply(body=replyMsg)
                    print('I: replied to %s' % author.name)
                except prawcore.exceptions.Forbidden as e:
                    print('W: exception caught posting a reply: %s', e)
            except praw.exceptions.APIException as e:
                print('W: exception caught (may be a rate limit): %s' % e)
    except KeyboardInterrupt:
        print('I: stop listening')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Count mannagge.')
    parser.add_argument('--username', default=os.environ.get('CONTAMANNAGGE_USERNAME'),
                        help='username of the Reddit account')
    parser.add_argument('--password', default=os.environ.get('CONTAMANNAGGE_PASSWORD'),
                        help='password of the Reddit account')
    parser.add_argument('--client-id', default=os.environ.get('CONTAMANNAGGE_CLIENT_ID'),
                        help='client ID of the Reddit bot')
    parser.add_argument('--client-secret', default=os.environ.get('CONTAMANNAGGE_CLIENT_SECRET'),
                        help='client secret of the Reddit bot')
    parser.add_argument(
        '--bot-name', default=os.environ.get('CONTAMANNAGGE_BOT_NAME', 'ContaMannagge'))
    parser.add_argument('--user-agent', default=os.environ.get('CONTAMANNAGGE_USER_AGENT'),
                        help='user agent of the Reddit bot')
    parser.add_argument('--homepage', default=os.environ.get('CONTAMANNAGGE_HOMEPAGE', 'https://github.com/mannagge/reddit-conta-mannagge'),
                        help='home page of this bot')
    parser.add_argument('--subs', default=os.environ.get('CONTAMANNAGGE_SUBS', 'mannaggiabottests'),
                        help='subs to listen to (join them with a +, if more than one)')
    parser.add_argument('--db-path', default=os.environ.get('CONTAMANNAGGE_DB_PATH'),
                        help='directory where the mannagge database will be stored')
    parser.add_argument('--version', action='version', version=VERSION)
    args = parser.parse_args()
    if args.db_path:
        DB_PATH = args.db_path
        DB_FILE = os.path.join(DB_PATH, DB_FILENAME)
    if not args.user_agent:
        args.user_agent = '%s by /u/%s' % (args.bot_name, args.username)
    listen(args)
