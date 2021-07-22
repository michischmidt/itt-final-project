import time
import numpy
from numpy.core.records import record
import pyaudio
import fluidsynth
import os
import wave
import tempfile
from uuid import uuid4
from playsound import playsound

'''
RecordAudio saves records in a temporary folder.
Records can be played, deleted and exported.
'''

class RecordAudio:

    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 2
    fs = 44100  # Record at 44100 samples per second
    filename = "output.wav"
    sampwidth = 2

    def __init__(self):
        self.audio_paths = []
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

    def remove_all(self):
        for file in self.audio_paths:
            os.remove(file)
        self.audio_paths = []

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
        file = self.audio_paths.pop()
        os.remove(file)

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

s = []

fl = fluidsynth.Synth()

# Initial silence is 1 second
s = numpy.append(s, fl.get_samples(44100 * 1))
fl.start(driver='alsa')
sfid = fl.sfload('./pns_drum.sf2')
fl.program_select(0, sfid, 0, 0)

fl.noteon(0, 35, 100)

# Chord is held for 2 seconds
for i in range(8):
    s = numpy.append(s, fl.get_samples(int(44100 * 0.1)))
    fl.noteon(0, 38, 100)
    fl.noteon(0, 46, 100)

# Chord is held for 2 seconds
s = numpy.append(s, fl.get_samples(44100 * 1))

fl.noteon(0, 46, 100)

# Decay of chord is held for 1 second
s = numpy.append(s, fl.get_samples(44100 * 1))

fl.delete()

samps = fluidsynth.raw_audio_string(s)

recorder = RecordAudio()

recorder.add_record(samps)
recorder.add_record(samps)

recorder.undo()

time.sleep(1)

recorder.play_all()