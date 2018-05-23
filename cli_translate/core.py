#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
 Translator,py
 :author insolita
 :url https://github.com/insolita/cli_translate
 :description Main purpose of package it is a quick translation text in clipboard,
  and also ability to store translations for future analyze, create memory cards
'''
import sys
import argparse
import pyperclip
import os
import requests
import sqlite3
from contextlib import closing
from pyquery import pyquery
from datetime import datetime

GOOGLE_URL = 'http://translate.google.com/m'
YANDEX_URL = 'https://translate.yandex.net/api/v1.5/tr.json/translate?key=%s&lang=%s'

CLIENT_BRANDS = {
    'google': {
        'header': 'Translated by (Google Translate)',
        'footer': '==== https://translate.google.com  ===='
        },
    # Api usage requirements
    'yandex': {
        'header': 'Translated by (Яндекс.Переводчик)',
        'footer': '==== http://translate.yandex.ru ===='
    }
}


class TranslateStorage(object):
    def __init__(self, db_path):
        self.db_path = os.path.expanduser(db_path)
        self.table_name = 'translations'
        self.db = self._init_db_path()
        self._init_migrations()

    def _init_db_path(self):
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
        return os.path.join(self.db_path, self.table_name + '.db')

    def _query(self, sql, params=(), fetchall=False):
        with closing(sqlite3.connect(self.db, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)) as connect:
            with connect:
                with closing(connect.cursor()) as cursor:
                    cursor.execute(sql, params)
                    result = cursor.fetchall() if fetchall else cursor.fetchone()
                    return result

    def _init_migrations(self):
        check_table_sql = 'SELECT name FROM sqlite_master WHERE type="table" AND name="%s";' % self.table_name
        create_table_sql = '''
        CREATE TABLE %s(
            id INTEGER PRIMARY KEY,
            client TEXT,
            source TEXT,
            translation TEXT,
            from_lang TEXT,
            to_lang TEXT,
            created_at TIMESTAMP
        );
        ''' % self.table_name
        exists = self._query(check_table_sql)
        if not exists or exists[0] != self.table_name:
            self._query(create_table_sql)

    def drop_table(self):
        self._query('DROP TABLE %s' % self.table_name)

    def save(self, client, source, translated, from_lang, to_lang):
        insert_sql = '''
            INSERT INTO %s(client, source, translation, from_lang, to_lang, created_at) VALUES(?,?,?,?,?,?);
        ''' % self.table_name
        self._query(insert_sql, (client, source, translated,
                                 from_lang, to_lang, datetime.now()))

    def stat(self):
        total_sql = 'SELECT COUNT(id) as cnt FROM %s' % self.table_name
        total_by_client = 'SELECT client, COUNT(id) as cnt FROM %s GROUP BY client' % self.table_name
        total_by_from_lang = 'SELECT from_lang, COUNT(id) as cnt FROM %s GROUP BY from_lang' % self.table_name
        total_by_to_lang = 'SELECT to_lang, COUNT(id) as cnt FROM %s GROUP BY to_lang' % self.table_name

        stat = {
            'total': self._query(total_sql)[0],
            'clients': self._query(total_by_client, fetchall=True),
            'to_lang': self._query(total_by_to_lang, fetchall=True),
            'from_lang': self._query(total_by_from_lang, fetchall=True),
        }
        return stat


class GoogleTranslate(object):
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'

    def translate(self, text, target_language='ru', source_language='auto'):
        headers = {'User-Agent': self.user_agent}
        params = {'q': text, 'hl': target_language,
                  'sl': source_language, 'ie': 'UTF-8', 'prev': '_m'}
        response = requests.get(GOOGLE_URL, params=params, headers=headers)
        if response.status_code != requests.codes.ok:
            print(response.reason)
            exit(1)
        pq = pyquery.PyQuery(response.text)
        translated = pq.find('div.t0').text()
        return translated


class YandexTranslate(object):
    def __init__(self, api_key):
        self.api_key = api_key

    def translate(self, text, target_language='ru', source_language='auto'):
        lang = source_language+'-' + \
            target_language if source_language != 'auto' else target_language
        response = requests.post(YANDEX_URL % (self.api_key, lang), data={
                                 'text': text}, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        if response.status_code != requests.codes.ok:
            print(response.reason)
            exit(1)
        translated = response.json()
        return translated['text'][0]


def client_factory(client, api_key=None):
    if client == 'yandex':
        if api_key is None:
            api_key = os.environ.get('YANDEX_TRANSLATE_API_KEY', default=None)
            if api_key is None:
                print('''Environment variable YANDEX_TRANSLATE_API_KEY required;
                         go to https://translate.yandex.ru/developers/keys,
                         register free api key, and add it in environment''')
                return None
        return YandexTranslate(api_key)
    else:
        return GoogleTranslate()


def _resolve_text(args):
    text = args.text if args.text else None
    if not text:
        text = pyperclip.paste()
    if not text or args.interactive:
        print('Type text for translation, then press "Ctrl+D" :"\n')
        text = sys.stdin.read()
        text = text.strip()
        if not text or text in ['quit', 'exit', 'xxx', '000']:
            exit(0)
    return text


def _show_result(result, client, is_raw, is_notify, source=None):
    header = CLIENT_BRANDS[client]['header']
    if is_raw:
        message = result
    else:
        message = [] if source is None else [source]
        if not is_notify:
            message.append('\u001b[1m\u001b[32m%s\u001b[0m\u001b[0m' % header)
        message.append(result)
        message.append(CLIENT_BRANDS[client]['footer'])
        message = '\n%s\n' % '\n'.join(message)
    if is_notify:
        import subprocess
        subprocess.Popen(
            ['notify-send', '--app-name=Cli Translator', '--urgency=low', header, message])
    else:
        print(message)


def _clean_db(db):
    storage = TranslateStorage(db)
    storage.drop_table()
    exit(0)


def _db_usage(db):
    storage = TranslateStorage(db)
    stat = storage.stat()
    def list_format(key, lst):
        return lst if key=='total' else '\n'.join([' \u001b[1m%s:\u001b[0m %s' % x for x in lst])
    stat = dict([(k, list_format(k, v)) for (k,v) in stat.items()])
    view = '\u001b[33m By Clients:\u001b[0m\n{clients}\n'\
           '\u001b[33m By Source Lang:\u001b[0m\n{from_lang}\n'\
           '\u001b[33m By Target Lang:\u001b[0m\n{to_lang}\n'\
           '\u001b[31m Total:\u001b[0m{total}\n'
    print(view.format(**stat))
    exit(0)


def translate(args):
    client = args.client if args.client in ['google', 'yandex'] else 'google'
    text = _resolve_text(args)
    translation_client = client_factory(client, args.yandex_key)
    result = translation_client.translate(text.encode(
        'UTF-8'), target_language=args.to, source_language=args.source)
    if args.nosave == False and args.db:
        storage = TranslateStorage(args.db)
        storage.save(client, text, result, args.source, args.to)
    _show_result(result, client, args.raw, args.notify,
                 text if args.original else None)
    if args.clip:
        pyperclip.copy(result)
    exit(0)


def _ensure_clip_support(clipboard):

    if not pyperclip.is_available():
        pyperclip.set_clipboard(clipboard)
        if not pyperclip.is_available():
            print("Copy functionality unavailable!")
            print('''On Linux, install xclip or xsel or klipper via package manager. For example, in Debian:
                 sudo apt-get install xclip
                 sudo apt-get install xsel
                 ''')
            exit(1)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("text", type=str, nargs='?',
                        action="store", default=None, help="Text for translation")
    parser.add_argument("-to", "--to", type=str, default='ru',
                        help="Target language (Default ru) (ru|en|es|fr..etc)")
    parser.add_argument("-src", "--source", type=str, default='auto',
                        help="Source language (Default  auto)")
    parser.add_argument("-o", "--original", action="store_true",
                        help="Show original text")
    parser.add_argument("--raw", action="store_true",
                        help="Output raw translation result")
    parser.add_argument("-i", "--interactive",
                        action="store_true", help="Interactive text input")
    parser.add_argument("-c", "--client", type=str, action="store",
                        default='google', help="Translation client (google|yandex)")
    parser.add_argument("-k", "--yandex_key", type=str, action="store",
                        default=None, help="API key for Yandex.Translate")
    parser.add_argument("--db", type=str, action="store",
                        default="~/.db/", help='Path to directory where translation database will be stored')
    parser.add_argument("--nosave", action="store_true",
                        help="Don't save translation in database")
    parser.add_argument("--cleandb", action="store_true",
                        help="Clean up translation database")
    parser.add_argument("--dbstat", action="store_true",
                        help="Database statistic")
    parser.add_argument("-n", "--notify", action="store_true",
                        help="Output translation result as system notification  (notify-send)")

    parser.add_argument("-p", '--clip', action="store_true",
                        help="Put translation into clipboard")
    parser.add_argument("-x", '--clipboard', action="store", default="xclip",
                        help="Clipboard utility")                    
    args = parser.parse_args()

    _ensure_clip_support(args.clipboard)

    if args.cleandb:
        _clean_db(args.db)
    elif args.dbstat:
        _db_usage(args.db)
    else:
        translate(args)


if __name__ == '__main__':
    main()
