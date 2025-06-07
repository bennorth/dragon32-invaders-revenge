# History

# Goals

Understand how the implementation works.  At least, how some of the interesting bits work.

Replicate behaviour quite closely, so need to understand game logic.

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

## Defender state

`Arr_DefendersData`
`Data_Shot_0`; maybe give another label?
`PlayerData_0_00_b_BaseFirePeriod` is start of first of two
`Arr_DefenderExplosions`
`Arr_PlayerExplnFragments`


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

# Misc remarks

Interspersing of data and code.  Even sometimes a variable right in the middle of the subroutine it's part of: `Var_b_ShotSoundProgress` in the middle of `Sub_LaunchPlayerShot`.

Inventive use of system stack here and there.  Search for ",S".

Re-use of "special defender explosion" intro for high-score sound effect.

A few variables (locations) left whose purpose haven't been able to work out.  Some seem completely unused; some are written to but never read.

Colour-code disassembly with backgrounds according to: code, data used locally just to one subroutine, data used across subroutines?

Fall-through into subroutine: Sub_CycleDefenderLaunchLocPtr

Pointers into arrays stored just after that array, giving rise to code comparing a pointer's value to its location.  See also `ShotPtrLimit`.

When blitting, checks that destination is in range (within screen memory) which panic if fail.

Use of colour checks for hit detection, e.g., `Sub_StepDefenderShotMovement`.  Choice of colours for sprites is influenced by making it easier for the code to detect them.

Use of `PULS PC,A` to save a byte over `PULS A / RTS`.

Most (all?) sounds clear `Var_b_PostDrawDelay`, to try to keep the frame rate consistent whether there is a sound playing or not.  Sound effects therefore have to shorten at higher game speeds, but this could be called a feature because the game sounds more frantic as it speeds up.

Use of BCD and dedicated instructions (`DAA`) to store and work with score.

Shared code between subs `Sub_MovePlayerRight` and `Sub_MovePlayerLeft`.

Differences in if/then/else basic-block layout.  `Sub_RedrawPlayer` has `RP_L5`; others (FIND SOME) more "inline".

When iterating over a fixed-size array, sometimes the codes counts how many entries, other times compares pointer to one-past-end of array.

Should we find a use for the *SmallUnusedDefender*?

The code for testing the keyboard and updating the player's position is inline in `MainPlayLoop` but other tasks are in subroutines.

Code at `CLS_L2` is unclear; looks like the `BNE` will never be taken, because X will always be decremented to zero.  Am I missing something?

Code for moving player: why do we store unchanged X?

# Refs

* [Undocumented 6809 opcodes](https://github.com/hoglet67/6809Decoder/wiki/Undocumented-6809-Behaviours)

# TODO

Consistency in descriptions of structs.

