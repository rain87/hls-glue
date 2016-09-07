#!/usr/bin/python -u

# dependencies:
# requests
# m3u8

target_server = 'kiev4-cdn.lanet.tv'

import logging
import logging.config
import os
logging.config.fileConfig(os.path.join(os.path.dirname(__file__), 'logging.conf'))


from m3u8_streamer import M3u8Streamer
from urlparse import urljoin
import sys
import re
from cStringIO import StringIO

def main():
    logger = logging.getLogger('main')
    logger.info('starting')
    # get url
    line = sys.stdin.readline().strip()
    logger.info('read {}'.format(line))
    path = re.match('GET (/.*) HTTP/\d\.\d', line).group(1).replace('.ts', '.m3u8')

    # skip rest of http header
    while sys.stdin.readline().strip():
        pass

    sys.stdout.write(
        'HTTP/1.0 200 OK\n'
        'Content-type: video/MP2T\n'
        'Connection: keep-alive\n'
        '\n\n')
    streamer = M3u8Streamer(urljoin(
        'http://' + target_server, 
        path))

    for data in streamer.iter_content():
        if not data:
            logger.error('Streamer has failed to return data')
            break
        try:
            sys.stdout.write(data)
        except:
            logger.exception('While sending response. Stopping server')
            break
    streamer.stop()


if __name__ == '__main__':
    try:
        sys.stderr.close()
        sys.stderr = StringIO()
        main()
    except:
        logging.getLogger('main').exception('Unexpected exception')
    data = sys.stderr.getvalue()
    if data:
        logging.getLogger('main').error(data)
