#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-
# Script was rewritten by Erik Blank and Michael Schmidt

import pyaudio
import os
import wave
import tempfile
from uuid import uuid4
from playsound import playsound

'''
RecordAudio saves records in a temporary folder.
Records can be played, deleted and exported.
Actions as as adding records, deleting one record or even all records can be undone.
'''

class RecordAudio:

    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 2
    fs = 44100  # Record at 44100 samples per second
    filename = "output.wav"
    sampwidth = 2

    def __init__(self):
        self.audio_paths = []
        self.undo_stack = []
        self.tmpdir = tempfile.mkdtemp()

    def add_record(self, raw_audio_string):
        filepath = os.path.join(self.tmpdir, str(uuid4()) + ".wav")
        wf = wave.open(filepath, "wb")
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.sampwidth)
        wf.setframerate(self.fs)
        wf.writeframes(raw_audio_string)
        wf.close()
        self.audio_paths.append(filepath)
        self.undo_stack.append(self.audio_paths[:])

    def remove_all(self):
        self.audio_paths = []
        self.undo_stack.append(self.audio_paths[:])

    def remove_one(self, index):
        del self.audio_paths[index]
        self.undo_stack.append(self.audio_paths[:])

    def play(self, index):
        playsound(self.audio_paths[index])

    # creates new temporary directory to create an outputfile
    # of all audio files and plays it
    def play_all(self):
        outfile = os.path.join(tempfile.mkdtemp(), "output.wav")
        data= []
        for infile in self.audio_paths:
            w = wave.open(infile, 'rb')
            data.append( [w.getparams(), w.readframes(w.getnframes())] )
            w.close()
            
        output = wave.open(outfile, 'wb')
        output.setparams(data[0][0])
        for i in range(len(data)):
            output.writeframes(data[i][1])
        output.close()
        playsound(outfile)

    def undo(self):
        if len(self.undo_stack) > 1:
            del self.undo_stack[-1]
            self.audio_paths = self.undo_stack[-1]
        elif len(self.undo_stack) == 1:
            self.undo_stack = []
            self.audio_paths = []

    def export_record(self):
        outfile = "output.wav"
        data= []
        for infile in self.audio_paths:
            w = wave.open(infile, 'rb')
            data.append( [w.getparams(), w.readframes(w.getnframes())] )
            w.close()
            
        output = wave.open(outfile, 'wb')
        output.setparams(data[0][0])
        for i in range(len(data)):
            output.writeframes(data[i][1])
        output.close()

    def get_audios(self):
        return self.audio_paths
