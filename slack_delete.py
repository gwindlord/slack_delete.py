#!/usr/bin/python3
import argparse
import requests
import time
import json

from datetime import datetime
from typing import List, Union, Dict

# mimetypes of files to delete (Slack API'types' sometimes omit files without any reason)
mimetypes = (
                'audio',
                'image',
                'video'
            )
wait_seconds = 2 # just in case not to be banned for robot requests

def main() -> None:
    """
    Entry point of the application
    :return: void
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', required=True, help='Specifies the OAuth token used for authentication, formerly created at (https://api.slack.com/docs/oauth-test-tokens)')
    parser.add_argument('-d', '--days', type=int, default=30, help='Delete files older than x days (optional)')
    parser.add_argument('-c', '--count', type=int, default=1000, help='Max amount of files to delete at once (optional)')
    parser.add_argument('-r', '--dry-run', action='store_true', help='Only print files list and exit (optional)')
    options = parser.parse_args()

    try:
        print('[*] Fetching file list..')
        files = list_files(token=options.token, count=options.count, days=options.days)

        print('[*] Deleting files..')
        delete_files(token=options.token, files=files, view_only=options.dry_run)

        print('[*] Done')

    except KeyboardInterrupt:
        print('\b\b[-] Aborted')
        exit(1)


def current_timestamp() -> str:
    """
    Return current timestamp in %Y-%m-%d %H:%M:%S form
    """

    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def calculate_days(days: int) -> int:
    """
    Calculate days to unix time
    :param days: int
    :return: int
    """

    return int(time.time()) - days * 24 * 60 * 60


def list_files(token: str, days: int, count: int) -> List[Dict[str, Union[str, int]]]:
    """
    Get a list of all files
    :param token: string
    :param count: int
    :param days: int
    :return: list
    """

    print('[*] %s delete files older than %s days' % (current_timestamp(), days))

    if days:
        params = {'token': token,'count': count,'ts_to': calculate_days(days)}
    else:
        params = {'token': token,'count': count}

    uri ='https://slack.com/api/files.list'
    response = requests.get(uri, params=params)
    resp = json.loads(response.text)['files']
    files = []

    for f in resp:
        if any([mimetype in f['mimetype'] for mimetype in mimetypes]):
            files.append({
                'id': f['id'],
                'name': f['name'],
                'timestamp': datetime.fromtimestamp(f['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                'mimetype': f['mimetype'],
                'size': f['size']
            })

    return files


def delete_files(token: str, files: List[Dict[str, Union[str, int]]], view_only: bool) -> None:
    """
    Delete a list of files by id
    :param token: string
    :param files: list
    :return: void
    """

    try:
        count = 0
        # uri ='https://slack.com/api/files.delete'
        uri ='https://slack.com/api/files.list'
        size_to_delete = sum([int(f['size']) for f in files])
        num_files = len(files)
        print('[i] %s found %s files in %s bytes' % (current_timestamp(), num_files, size_to_delete))
        print([(f['id'], f['name'], f['timestamp'], f['mimetype'], f['size']) for f in files])

        if view_only:
            return

        for f in files:
            count += 1
            params = {'token': token,'file': f['id']}
            dresponse = json.loads(requests.get(uri, params=params).text)
            time.sleep(wait_seconds)
            if dresponse['ok']:
                print('[+] %s Deleted: [%s] %s (%s)' % (current_timestamp(), f['id'], f['name'], f['timestamp']))
            else:
                print('[!] %s Unable to delete: [%s] %s, reason: %s' % (current_timestamp(), f['id'], f['name'], dresponse['error']))

    finally:
        print('[i] %s Attempted to delete %s bytes in %s files, actually deleted %s files' % (current_timestamp(), size_to_delete, num_files, count))


if __name__ =='__main__':
    main()
