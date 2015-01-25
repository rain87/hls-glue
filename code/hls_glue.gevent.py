#!/usr/bin/python

# dependencies:
# gevent
# requests
# m3u8

listen_ip = '' # empty stays for 0.0.0.0
listen_port = 9090
connections = 30
target_server = 'kirito.la.net.ua'


from gevent.pywsgi import WSGIServer
from gevent.pool import Pool
from m3u8_streamer import M3u8Streamer
from urlparse import urljoin


class ResultWrapper(object):
    def __init__(self, data, close):
        self._data = data
        self.close = close

    def __str__(self):
        return self._data

    def __iter__(self):
        for chunk in self._data:
            yield chunk

    def __len__(self):
        return self._data.__len__()


def application(env, start_response):
    start_response('200 ok', [('Content-type', 'video/MP2T'), ('Connection', 'Keep-alive')])
    streamer = M3u8Streamer(urljoin(
        'http://' + target_server, 
        env['PATH_INFO'].replace('.ts', '.m3u8'))
    )
    for data in streamer.iter_content():
        print '-----------get {} bytes'.format(len(data))
        if data:
            yield ResultWrapper(data, streamer.stop)
    pass


if __name__ == '__main__':
    print 'Starting on {}:{}'.format(listen_ip, listen_port)
    WSGIServer((listen_ip, listen_port), application, spawn=Pool(connections)).serve_forever()
