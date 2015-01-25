#!/usr/bin/python -u

# dependencies:
# requests
# m3u8

target_server = 'kirito.la.net.ua'


from m3u8_streamer import M3u8Streamer
from urlparse import urljoin
import sys
import re
import os


if __name__ == '__main__':
    # get url
    line = sys.stdin.readline().strip()
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

    f = open('/tmp/test.ts', 'wb')
    for data in streamer.iter_content():
        #sys.stdout.write(data)
        os.write(sys.stdout.fileno(), data)
        f.write(data)
        f.flush()
