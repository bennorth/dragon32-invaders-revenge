#!/bin/bash

date +"%H:%M:%S Starting"

python gen_vars.py > vars.f9dasm \
    && ./f9dasm/f9dasm -info invaders-revenge.f9dasm \
        | tail +3 \
        > inv-rev.f9out \
    && poetry run python reformat.py \
        < inv-rev.f9out \
        > rendered-asm/out1.html \
    && mv rendered-asm/out1.html rendered-asm/out.html

date +"%H:%M:%S Done"
