from threading import Thread, Condition
from Queue import Queue
import requests
import m3u8
from time import time
from urlparse import urljoin


class M3u8Streamer(object):
    """
    Converter that loads m3u8 playlist and returns continuous media stream 
    """
    def __init__(self, url):
        """
        @param url: m3u8 playlist url to load
        """
        self._url = url
        self._chunks = Queue()
        self._loader = Thread(target=self._loader_main)
        self._loader.daemon = True
        self._cond = Condition()
        self._stop_loader = False
        self._last_loaded_segment = None
        with self._cond:
            self._loader.start()
            self._cond.wait()

    def __del__(self):
        self.stop()

    def stop(self):
        """
        Stop downloading stream
        """
        self._stop_loader = True
        if self._loader.is_alive():
            self._cond.notify_all()
            self._loader.join()

    def iter_content(self):
        while self._loader.is_alive() or not self._chunks.empty():
            yield self._chunks.get()

    def _loader_main(self):
        with self._cond:
            self._cond.notify_all()
        while not self._stop_loader:
            self._ts_pls_load = time()
            pls = m3u8.load(self._url)
            playback_time = 0
            if self._last_loaded_segment == pls.segments[0]:
                del pls.segments[0]
            for segment in pls.segments:
                playback_time += segment.duration
                self._load_segment(segment)
                if self._stop_loader:
                    break
            sleep_time = playback_time - (time() - self._ts_pls_load) - (pls.segments[-1].duration / 2)
            self._last_loaded_segment = pls.segments[-1].uri
            if not self._stop_loader and sleep_time > 0:
                with self._cond:
                    self._cond.wait(sleep_time)

    def _load_segment(self, segment):
        url = segment.base_uri + '/' + segment.uri
        req = requests.get(url, stream=True)
        for chunk in req.iter_content(chunk_size=512 * 1024):
            if chunk:
                self._chunks.put(chunk)
            if self._stop_loader:
                break
        pass
