#!/bin/bash

set -e

mkdir -p docs

pandoc --css=styling.css \
       -s \
       -f markdown+smart \
       --to=html5 \
       write-up.md \
       -o docs/index.html

./make-html.sh

cp -u \
   docs-sources/styling.css \
   docs-sources/cassette-inlay.jpg \
   docs-sources/screenshot-1.png \
   docs-sources/d32-player-ship.png \
   docs-sources/pytch-player-ship.png \
   docs-sources/Pytch-hw-invaders-revenge.jpg \
   docs-sources/howler.core.min.js \
   docs-sources/sound-samples.js \
   docs-sources/sound-wave.png \
   New-sounds/samples/defender-base-hit-0.wav \
   docs

cp -u \
   New-sounds/synthesised-output/defender-base-hit-0.wav \
   docs/synth-defender-base-hit-0.wav

cp -u \
   rendered-asm/out.html \
   docs/disassembly.html

cp -u \
   rendered-asm/invaders-revenge.css \
   docs/disassembly.css
