# History

# Goals

Understand how the implementation works.  At least, how some of the interesting bits work.

Replicate behaviour quite closely, so understand game logic.

Replicate graphics and sounds.

# Rev.eng process

Wanted to try the special-purpose disassembler (IDA) but the free version does not support 6809.  Used disassembler which allows separate annotation file.

Only afterwards discovered Cutter / Rizen, which do support 6809, and which might be worth exploring next time I do something like this.

# Graphics

Find sections of the binary corresponding to graphics by finding references to those addresses in bits of code which blt to screen memory.  Decode with knowledge of D32 graphics hardware (6847 VDG chip) into PNGs.  Turn green (background) into transparent.

Scale to fit Pytch stage dimension.  Decisions about how to do the non-integer scaling.  Redraw sprites trying to capture idea.  Allow finer pixel grid.

# Screen layout

Identify properties of layout (e.g., which rows the patrols happen on) which are important to gameplay.  Evenly spaced (but with gap).  Scale to Pytch stage.

# Scoring

Scale up and keep blocky the digits.  One-player mode with bigger score display.

# Data structures

Use of static arrays of structs for:

* defender patrols
* defender explosions
* fragments of hit player
* (two-element) array of player data

Layouts of structs.

# Seemingly unused bits of binary

Handful of seemingly unused graphics, variables.  Both "completely unreferred-to" but also "written but never read".  And large run of nonsense data.

# Invalid opcodes

Logic might be OK with behaviour.  Could be bad cassette read but unlikely given that there are checksums.

# Sound

Got some sense of shape of sound effects from code, but too difficult to completely work out behaviour.  Would need cycle-counting.  From code can get general properties:

* Often made of "chirps", short bursts of sound where the period increases or decreases after each cycle (or sometimes half-cycle CHECK)
* Sounds are square waves and have to be generated with gaps which occur while the game does other things.
* Length of individual chirps shortens as game speeds up, as it has to.

Then ran in emulator [LINK XROAR], captured, analysed, re-synthesised.  Decided this was OK and in same spirit as re-doing the sprites at the higher resolution.  Sound cleaner and softer; not sure whether this is an improvement.
