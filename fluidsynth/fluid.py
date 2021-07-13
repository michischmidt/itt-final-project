# example code from https://github.com/nwhitehead/pyfluidsynth

import time
import fluidsynth

fs = fluidsynth.Synth(1)

# different operating systems need different drivers
# on Linux, 'pulseaudio' is often a save bet
# on MacOS, 'portaudio' seems to work
# on Windows, select 'dsound'
fs.start(driver='alsa')

# load a sound font that contains the actual audio files for the midi events
# there are many different free sound fonts available in the web
# in this case we use the default general midi sound font
# sfid = fs.sfload('/usr/share/sounds/sf2/default-GM.sf2')
sfid = fs.sfload('/home/michael/Downloads/pns_drum.sf2')
# sfid = fs.sfload('/home/michael/Downloads/acoustic_guitars.sf2')

# select MIDI track, sound font, MIDI bank and preset
fs.program_select(0, sfid, 0, 0)

# play a C major chord
# parameters are MIDI track, note ID and velocity
# E A D G B E
# fs.noteon(0, 60, 100)
# time.sleep(0.5)
# fs.noteon(0, 67, 100)
# time.sleep(0.5)
# fs.noteon(0, 76, 100)
# fs.noteon(0, 64, 100)
# time.sleep(0.5)
# fs.noteon(0, 69, 100)
# time.sleep(0.5)
# fs.noteon(0, 74, 100)
# time.sleep(0.5)
# fs.noteon(0, 79, 100)
# time.sleep(0.5)
# fs.noteon(0, 83, 100)
# time.sleep(0.5)
# fs.noteon(0, 88, 100)
# time.sleep(0.5)

# DRUM KIT MAPPING
# Bass/Kick drum
fs.noteon(0, 35, 100)
time.sleep(0.5)
# Snare Drum
fs.noteon(0, 38, 100)
time.sleep(0.5)
# Hi-Hat Cymbal
fs.noteon(0, 46, 100)
time.sleep(0.5)
# Crash Cymbal
fs.noteon(0, 49, 100)
time.sleep(0.5)
# Tom Drum 1
fs.noteon(0, 45, 100)
time.sleep(0.5)
# Tom Drum 2
fs.noteon(0, 50, 100)
time.sleep(0.5)
# Ride Cymbal
fs.noteon(0, 51, 100)
time.sleep(0.5)
# Floor Tom Drum
fs.noteon(0, 41, 100)
time.sleep(0.5)

time.sleep(1.0)

# stop playing the chord
# parameters are MIDI track and note ID
# fs.noteoff(0, 60)
# fs.noteoff(0, 67)
# fs.noteoff(0, 76)
fs.noteoff(0, 64)
fs.noteoff(0, 69)
fs.noteoff(0, 74)
fs.noteoff(0, 79)
fs.noteoff(0, 83)
fs.noteoff(0, 88)

time.sleep(1.0)

fs.delete()
