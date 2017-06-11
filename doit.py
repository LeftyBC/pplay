#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import random
from subprocess import Popen
import psutil
import threading
import urwid
import time
from mplayer import Player
import mplayer
import inspect
import mutagen

# TODO - configurable
DIR="/storage/music"
timer = None
playbackThread = None
songname = urwid.Text(('banner', u"None"), align='center')
statusbar = urwid.Text(('banner', u"Status"), align='center')
last_key = ""

palette = [
    ('banner', 'black', 'light gray'),
    ('streak', 'black', 'dark red'),
    ('bg', 'black', 'dark blue'),
]

class PlaybackThread(threading.Thread):

    files = []
    proc = None
    FILETYPES=[".flac", ".mp3", ".wav", ".mp4"]
    playing = True
    playlist_position = 0
    current_filename = ""

    def __init__(self, music_dir, exit_event):
        threading.Thread.__init__(self)

        FNULL=open(os.devnull,'w')
        self.player = Player(stdout=FNULL, stderr=FNULL, autospawn=True)
        self.player.cmd_prefix = mplayer.CmdPrefix.PAUSING_TOGGLE
        self.files = self.get_files(music_dir)
        self.playlist_position = 0
        self._randomize(self.files)
        self.exit_event = exit_event

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
        #FNULL=open(os.devnull, 'w') # file handle to /dev/null
        #self.proc = psutil.Popen(["mplayer", fullpath], stdout=FNULL, stderr=FNULL, close_fds=True)
        #print("Fired up mplayer with pid %s playing %s" % (self.proc.pid, fullpath))
        self.player.loadfile(fullpath)
        self.current_filename=fullpath
        self.player.time_pos = 0

    def _next_file(self):
        if len(self.files) > 0 and self.playlist_position < len(self.files):
            self.playlist_position += 1
            return self.files[self.playlist_position]
        else:
            return None

    def _prev_file(self):
        if len(self.files) > 0 and self.playlist_position > 0:
            self.playlist_position -= 1
            return self.files[self.playlist_position]
        else:
            return None

    def play_next(self):
        next_file = self._next_file()
        if next_file is None:
            return

        self._play_file(next_file)

    def play_prev(self):
        prev_file = self._prev_file()
        if prev_file is None:
            return

        self._play_file(prev_file)

    def play(self):
        self._play_file(self.files[self.playlist_position])

    def stop(self):
        self.player.stop()

    def pause(self):
        self.player.pause()

    def current(self):
        m = self._get_metadata()
        try:
            return "%s - %s (%s)" % (m["Artist"], m["TITLE"], self.current_filename) #self.player.get_meta_artist())
        except KeyError:
            return self.current_filename

    def _get_metadata(self):
        if self.current_filename:
            metadata = mutagen.File(self.current_filename, easy=True)
            if metadata:
                return metadata.tags
        return {}

    def run(self):
        while not self.exit_event.is_set():
            self.exit_event.wait()

        for t in inspect.getmembers(self.player):
            if t[1] is not None:
                print(t)
        print(self.player.metadata)
        self.player.quit()

def ui_tick(loop, user_data):
    songname.set_text("(%s) At %d: %s" % (last_key, time.time(), playbackThread.current()))
    loop.set_alarm_in(1.0, ui_tick)

exit_event = threading.Event()

def ui_handle_keys(key):
    last_key = key
    if key in ('q', 'Q'):
        playbackThread.stop()  # kill playback thread?
        exit_event.set()
        statusbar.set_text("exiting main thread")
        raise urwid.ExitMainLoop()
    elif key in ('z', 'Z'):
        playbackThread.play_prev()
        statusbar.set_text("Action: Prev")
    elif key in ('x', 'X'):
        playbackThread.play()
        statusbar.set_text("Action: Play")
    elif key in ('c', 'C'):
        playbackThread.pause()
        statusbar.set_text("Action: Pause")
    elif key in ('b', 'B'):
        playbackThread.play_next()
        statusbar.set_text("Action: Next")
    elif key in ('v', 'V'):
        playbackThread.stop()
        statusbar.set_text("Action: Stop")
    ui_tick(loop, None)

    return True


if __name__ == "__main__":

    threads = []
    playbackThread = PlaybackThread(DIR, exit_event)
    threads.append(playbackThread)

    # start all threads
    for x in threads:
        x.start()

    pile = urwid.Pile([songname, statusbar])
    map1 = urwid.AttrMap(pile, 'streak')
    fill = urwid.Filler(map1) # songname, 'top')
    map2 = urwid.AttrMap(fill, 'bg')
    loop = urwid.MainLoop(map2, palette, unhandled_input=ui_handle_keys)
    loop.set_alarm_in(1.0, ui_tick)
    ui_tick(loop, None)

    statusbar.set_text("Waiting...")
    loop.run()


