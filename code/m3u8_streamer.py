from threading import Thread, Condition
from Queue import Queue
import requests
import m3u8
from time import time
from urlparse import urljoin
import logging
import urllib2


class M3u8Streamer(object):
    """
    Converter that loads m3u8 playlist and returns continuous media stream 
    """
    def __init__(self, url):
        """
        @param url: m3u8 playlist url to load
        """
        self._logger = logging.getLogger('M3u8Streamer')
        self._url = url
        self._chunks = Queue()
        self._loader = Thread(target=self._loader_main)
        self._watchdog = Thread(target=self._watchdog_main)
        self._cond = Condition()
        self._stop_loader = False
        self._last_loaded_segments = []
        self._no_data_timeout = 30
        self._last_data_recv = time()
        self._watchdog.start()
        with self._cond:
            self._loader.start()
            self._cond.wait()

    def __del__(self):
        self.stop()

    def _stop_thread(self, thread, name):
        if thread.is_alive():
            self._logger.info('stopping {} thread'.format(name))
            with self._cond:
                self._cond.notify_all()
            thread.join()
            if thread.is_alive():
                self._logger.info('Failed to stop {}'.format(name))
            else:
                self._logger.info('stopped {}'.format(name))
        else:
            self._logger.info('{} is already stopped'.format(name))

    def stop(self):
        """
        Stop downloading stream
        """
        self._stop_loader = True
        self._stop_thread(self._loader, 'Loader')
        self._stop_thread(self._watchdog, 'Watchdog')

    def iter_content(self):
        while self._loader.is_alive() or not self._chunks.empty():
            yield self._chunks.get()

    def _loader_main(self):
        with self._cond:
            self._cond.notify_all()
        while not self._stop_loader:
            ts_pls_load = time()
            try:
                pls = m3u8.load(self._url)
            except urllib2.HTTPError as e:
                self._logger.warning('Network error while loading m3u8: {};'
                    ' retrying in small timeout'.format(e))
                with self._cond:
                    self._cond.wait(2)
                continue
            playback_time = 0
            self._logger.debug('Got {} segments'.format(len(pls.segments)))
            for segment in pls.segments:
                if self._stop_loader:
                    break
                playback_time += segment.duration
                if segment.uri in self._last_loaded_segments:
                    self._logger.warning('Dropping overlapped segment {}'.format(segment.uri))
                    continue
                self._load_segment(segment)
            sleep_time = playback_time - (time() - ts_pls_load) - pls.segments[-1].duration
            self._last_loaded_segments = [segment.uri for segment in pls.segments]
            self._logger.info('Sleep is {}'.format(sleep_time))
            if not self._stop_loader and sleep_time > 0:
                self._last_data_recv += sleep_time
                with self._cond:
                    self._cond.wait(sleep_time)

    def _load_segment(self, segment):
        self._logger.info('Loading segment {}'.format(segment.uri))
        url = segment.base_uri + '/' + segment.uri
        ts_start = time()
        size = 0
        req = requests.get(url, stream=True)
        for chunk in req.iter_content(chunk_size=512 * 1024):
            if chunk:
                size += len(chunk)
                self._chunks.put(chunk)
                self._last_data_recv = time()
            if self._stop_loader:
                break
        duration = time() - ts_start
        size /= 1e6
        self._logger.info('Done ({} Mb in {} seconds @ {} Mb/s)'.format(size, duration, size / duration))

    def _watchdog_main(self):
        while not self._stop_loader:
            everything_is_ok_interval = self._last_data_recv + self._no_data_timeout - time()
            self._logger.debug('Watchdog {}'.format(everything_is_ok_interval))
            if everything_is_ok_interval < 0:
                # seems it is not ok, actually -_-
                self._logger.warning('Watchdog has detected long no-data gap, stopping streamer')
                self._chunks.put(None)
                self._stop_loader = True
                break
            with self._cond:
                self._cond.wait(everything_is_ok_interval)
