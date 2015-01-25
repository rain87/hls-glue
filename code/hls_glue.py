#!/usr/bin/python -u

# dependencies:
# requests
# m3u8

target_server = 'kirito.la.net.ua'

import logging
import logging.config
import os
logging.config.fileConfig(os.path.join(os.path.dirname(__file__), 'logging.conf'))


from m3u8_streamer import M3u8Streamer
from urlparse import urljoin
import sys
import re

if __name__ == '__main__':
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
        try:
            sys.stdout.write(data)
        except:
            logger.exception('While sending response. Stopping server')
            break
    streamer.stop()
