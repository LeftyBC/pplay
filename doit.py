#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import random
from subprocess import Popen
import psutil
import threading

# TODO - configurable
DIR="/storage/music"

class PlaybackThread(threading.Thread):

    files = []
    proc = None
    FILETYPES=[".flac", ".mp3", ".wav", ".mp4"]
    playing = True

    def __init__(self, music_dir):
        threading.Thread.__init__(self)
        self.files = self.get_files(music_dir)
        self._randomize(self.files)

    def get_files(self,directory):
        files = []
        for root, dirs, fnames in os.walk(directory, topdown=True):
            for name in fnames:
                fn, ext = os.path.splitext(name)
                if ext.strip().lower() in self.FILETYPES:
                    fullpath = os.path.join(root, name)
                    files.append(fullpath)
        return files

    def _randomize(self, arr=[]):
        random.shuffle(arr)

    def _play_file(self, fullpath):
        FNULL=open(os.devnull, 'w') # file handle to /dev/null
        self.proc = psutil.Popen(["mplayer", fullpath], stdout=FNULL, stderr=FNULL, close_fds=True)
        print("Fired up mplayer with pid %s playing %s" % (self.proc.pid, fullpath))

    def _next_file(self):
        if len(self.files) > 0:
            return self.files.pop(0)
        else:
            return None

    def play_next(self):
        next_file = self._next_file()
        if next_file is None:
            return

        if self.proc and self.proc.is_running():
            proc.kill()
            proc.wait()

        self._play_file(next_file)

    def run(self):
        while True:
            self.play_next()
            self.proc.wait()


if __name__ == "__main__":
    threads = []

    threads.append(PlaybackThread(DIR))

    # start all threads
    for x in threads:
        print("Staring thread: %s", x)
        x.start()

    # main thread waits for all threads to die
    for x in threads:
        x.join()
