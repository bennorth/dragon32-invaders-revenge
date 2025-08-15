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
   docs

cp -u \
   rendered-asm/out.html \
   docs/disassembly.html

cp -u \
   rendered-asm/invaders-revenge.css \
   docs/disassembly.css
