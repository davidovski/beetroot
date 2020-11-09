import pip_manager as pm

pm.install_missing("wave", "pygame", "PySimpleGUI")

import pygame
import wave
import time
import PySimpleGUI as sg
import sys
import math
import os

current_time = lambda: int(round(time.time() * 1000))


class BeatSyncer():

    def __init__(self, file=""):
        self.last = 0
        self.screen = None
        self.file = file
        self.fps_clock = None
        self.bpms = []
        self.offsets = []
        self.start = 0
        self.END_EVENT = pygame.USEREVENT + 1

        if file == "":
            self.open_selection()
        else:
            self.load_music(file)
            self.initialize_pygame()

    def load_music(self, file):
        self.file = file
        print("loading music.. " + file)
        pygame.init()

        print("mixer pre init")
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        print("mixer init")

        pygame.mixer.init()
        print("loading file")

        pygame.mixer.music.load(file)
        print("setting end event")

        pygame.mixer.music.set_endevent(self.END_EVENT)

    def open_selection(self):
        layout = [[sg.Text('Filename')],
                  [sg.Input(), sg.FileBrowse()],
                  [sg.OK(), sg.Cancel()]]

        window = sg.Window('Beetroot', layout)

        event, values = window.Read()

        if event == "OK":
            print(values[0])
            self.load_music(values[0])
            self.initialize_pygame()

    def play_music(self):
        print("playing music")
        pygame.mixer.music.play(1)
        self.start = current_time()
        # Game loop.

    def initialize_pygame(self):
        print("initialising pygame")

        self.fps_clock = pygame.time.Clock()

        width, height = 640, 480
        self.screen = pygame.display.set_mode((width, height))

        self.play_music()
        while True:
            self.loop()

    def get_average_bpm(self):
        bpm = 0
        for b in self.bpms:
            bpm += b
        if len(self.bpms) > 0:
            bpm = bpm / len(self.bpms)
        return bpm

    def get_average_offset(self):
        offset = 0
        for b in self.offsets:
            offset += b
        offset = offset / len(self.offsets)
        return offset

    def get_average_beat_time(self):
        return (1 / self.get_average_bpm()) * 60 * 1000

    def loop(self):

        now = current_time()
        elapsed = now - self.start
        density = 0

        if len(self.bpms) > 0:
            avg_beat_time = self.get_average_beat_time()
            avg_bpm = self.get_average_bpm()
            last_beat_elapsed = math.floor((elapsed + self.get_average_offset()) / avg_beat_time) * avg_beat_time
            time_since = (elapsed - last_beat_elapsed) + self.get_average_offset()

            density = 1 - (time_since / 100)

            density = 0 if density < 0 else 1 if density > 1 else density

        self.screen.fill((density * 255, density * 255, density * 255))

        for event in pygame.event.get():
            if event.type == self.END_EVENT:
                self.save_data("bashar")
                pygame.quit()
                self.confirm_bpm()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                if not self.last == 0:
                    beat_time = now - self.last

                    bpm = 1 / (beat_time / 1000 / 60)
                    self.bpms.append(bpm)

                    # print("bpm = " + str(round(self.get_average_bpm())))

                    avg_beat_time = self.get_average_beat_time()
                    beats_since_start = elapsed / avg_beat_time
                    beats_left_over = beats_since_start - math.floor(beats_since_start)
                    offset = beats_left_over * avg_beat_time

                    self.offsets.append(offset)

                self.last = now

        pygame.display.update()
        self.fps_clock.tick(100)

    def confirm_bpm(self):

        name = self.file[:-3] + "data"
        bpm = round(self.get_average_bpm(), 2)
        beat_time = round(self.get_average_beat_time(), 2)
        offset = round(self.get_average_offset(), 2)

        layout = [[sg.Text("BPM:" + str(bpm) + " offset:" + str(offset) + " beat time: " + str(beat_time))],
                  [sg.Text("Save this as " + name + "?")],
                  [sg.OK(), sg.Cancel()]]

        window = sg.Window('Beetroot', layout)

        event, values = window.Read()

        if event == "OK":
            self.save_data(name)

    def save_data(self, filename):
        bpm = round(self.get_average_bpm(), 2)
        offset = round(self.get_average_offset(), 2)
        beat_time = round(self.get_average_beat_time(), 2)
        with open(filename, "w") as f:
            f.write(str(bpm) + "\n" + str(offset)+ "\n" + str(beat_time))


if __name__ == "__main__":
    bs = BeatSyncer(file="./bashar.mp3")

