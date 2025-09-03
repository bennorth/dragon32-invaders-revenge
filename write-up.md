---
title: The Dragon 32 game _Invader's Revenge_
author: "[Ben North](https://github.com/bennorth)"
date: August 2025
---

# Overview

In my increasingly-distant youth, my family had a Dragon 32 home computer, which I spent many hours with.  For a lot of this time, I was writing programs of various kinds, with the built-in Basic and then also assembly language.  But, unsurprisingly, I also played games, including one called *Invader's Revenge*, written by Kenneth Kalish.  You controlled a yellow ship, and had to shoot enemy ships while avoiding being shot by the enemy base.  Good fun.

<figure>
<div style="display:grid;grid-template-columns:7fr 5fr;align-items:center;">
<div style="margin:1rem;"><img src="screenshot-1.png" width="100%"></div>
<div style="margin:1rem;"><img src="cassette-inlay.jpg" width="100%"></div></div>
<caption><p style="margin:0.5rem;">Screenshot and cassette inlay for <i>Invader's Revenge</i>.</p><p style="font-size:0.9rem;"><i>Cassette inlay image from <a href="https://archive.worldofdragon.org/">The Dragon Archive</a></i>.</p></caption>
</figure>

In my current job, I am developing and researching [Pytch](https://pytch.org/), a free online educational coding platform to help people learn Python by writing "Scratch-like" programs.  I thought a port of *Invader's Revenge* could be a good example of what can be made in Pytch.

I could probably have achieved this by taking screenshots and working out the game logic just by observations, but thought it would be a more interesting exercise to reverse engineer the original machine code.  This would also allow a dose of nostalgia for the Dragon and working in assembly language, albeit someone else's.

## Pytch version

_EMBED PYTCH VERSION.  And link for "demo", which allows "see inside"._


# Annotated disassembly

Using a combination of existing tools and various bits of ad-hoc Python code, I produced what I hope is a reasonably readable disassembly of the game's code and data.

## Result

Code and data are shown with different background colours.  Subroutines are cross-linked, to make them clickable at call sites.  Chunks of data which represent graphics are rendered.

* [Disassembly](disassembly.html).

## Observations

Various features of the code struck me as interesting:

* **No pseudo-random numbers.**  Although the behaviour of the defenders seems random, there are not even any pseudo-random numbers involved.  The random-looking behaviour emerges from the deterministic logic for starting new defender patrols.
* **Interleaved code and data.**  The lump of machine code is not neatly divided into data and code.  Code is interspersed with data, sometimes even a variable appearing in the middle of the code for the subroutine it is used in.
* **Fine-grained movement for the player ship.**  The defenders move horizontally by four pixels at a time, allowing simpler code because four pixels are stored in one byte of video memory.  The fact that the defenders move in four-pixel steps is part of the style of the game.  But the player can move at two-pixel resolution, and has two different bitmaps (["right position"](disassembly.html#LBL--GFX_PlayerRightPosn) and ["left position"](disassembly.html#LBL--GFX_PlayerLeftPosn)) to support this.
* **Inventive use of the system stack.**  I saw a few nice examples of manipulating values stored on the system stack, for example overwriting a saved value, multiplying by three, and saving a `RTS` opcode by pulling the program counter in the same instruction as restoring a saved register.
* **Seemingly unused variables.**  There are a few locations which are written to but, as far as I could tell, never read from, so their purpose is unclear to me.
* **Seemingly unused graphics.**  There are some bytes near the start which can be interpreted as [a small defender-like graphic](disassembly.html#LBL--GFX_SmallUnusedDefender).  Maybe there were plans to use this as another "special" defender?
* **Fall-through code.**  In a few places, one subroutine "falls through" into another.  Another way of thinking of this is that some routines have multiple entry points.
* **Collision detection via colours.**  For some code, the "source of truth" is the video display memory.  The code looks for the presence of, say, a defender, by looking for pixels which are either blue or red.  I suspect the choice of this colour scheme was influenced by the fact that the two-bit codes for blue and red are `10` and `11` respectively, allowing a simple bitwise-and test for defender-coloured pixels.
* **Split responsibility for destroying defenders.**  As far as I can tell, the job of destroying a defender when a player's shot hits it is split between the [subroutine which moves the shots](disassembly.html#LBL--Sub_MovePlayerShotsDown), and [the subroutine which moves the defenders](disassembly.html#LBL--Sub_MoveDefenderCheckHit).  This all seems quite intricate but I expect is the best fit for the data structures used and the time constraints the code works under.
* **Timekeeping with delays or sounds.**  Each update usually ends with a do-nothing delay loop, which gets shorter as the player gets more points.  But when a sound effect is playing, bit-banging the audio output serves the dual purpose of creating the delay, so the do-nothing loop is skipped.  The sound effects have to match the dynamic delay, so the sound effects get more frantic as the game speeds up — this counts as a feature I think.
* **Score stored in BCD.**  The player's score is stored in units of 100 points, as a four-digit BCD (16-bit) value.  The code uses the special 6809 instruction `DAA` (for _Decimal Adjust after Addition_) for arithmetic with BCD values.  The logic for awarding an extra life each 10,000 points falls out in a pleasingly simple way from this representation.
* **Differing basic block layout.**  Code which in a high-level language would be an `if/else` is coded in different layouts in different places.  Sometimes one of the blocks is 'inline', and other times both the `if` and the `else` arms are separate and jumped to and from.
* **Iteration over arrays.**  Sometimes this is done by counting how many entries remain to be processed, and other times by comparing the record pointer with the "one past the end" value.
* **Iteration and sequencing split over updates.**  The fundamental logic implemented by [the code which animates the result of a defender shot hitting something](**TODO**) is not particularly complex.  However, the code has to carefully track progress through the logic with an explicit state value, because it has to do a small piece of work each time it is called.  This makes the code more complex.
* **Partially-written single joystick mode?**  There is some duplicated state for recording whether the game is in one- or two-player mode.  Different variables are used in the logic for player state vs the logic for selecting which joystick to read.  I wonder whether there were plans to allow two players to play a two-player game where only one joystick was used.
* **Stack leak.**  The code which implements the timeout when prompting the user for the speed and number of shots leaks two bytes of stack, because it does a `JMP` to the reset routine even though conceptually it is a subroutine.  This was suspected by code inspection and verified under GDB.  Compare the care taken in a similar situation in the [end-of-game code](disassembly.html#LBL--Sub_EndOfGame).
* **Unused slot for defender explosion data?**  There is [space reserved](disassembly.html#LBL--Arr_DefenderExplosions) for up to ten defender explosions.  However, the [code which processes this array](disassembly.html#LBL--Sub_StepDefenderExplns) seems to only handle the first nine entries — it initialises a counter to `10` then, in each iteration, decrements this counter and then tests it for being non-zero.  I wasn't able to verify this behaviour in play though.

## Methods used while reverse-engineering

I had heard of, and wanted to try, the special-purpose reverse-engineering disassembler [IDA](https://hex-rays.com/), but the free version does not support the 6809 processor.  Only too late did I discover the free-software [Cutter](https://cutter.re/), based on [Rizin](https://rizin.re/), which does support the 6809.  This might be worth exploring if I do something like this again.

The tool I ended up using was [f9dasm](https://github.com/Arakula/f9dasm).  As well as the binary machine-code dump, you supply a separate file of annotations and other directives.  The `f9dasm` tool then disassembles the machine code according to your directives and annotations.  I added a post-processing step, implemented as a collection of ad-hoc Python scripts, to break the disassembly into "chunks" for more readable rendering in HTML.  A "chunk" is a subroutine or a piece of data.

The whole process was highly iterative.  The starting point was to trace execution from the entry-point address, and then go round and round with a mixture of the following activities.

* Identify a subroutine or block of data.
* Decode a block of data representing a graphics sprite.
* Deduce the fields of a data structure.
* Deduce the semantics of a variable.
* Deduce what a particular subroutine did with variables or overall machine state (e.g., display or sound).
* Make or refine notes and comments on a subroutine, variable, or data structure.
* Give a name to a subroutine or piece of data.

Understanding a variable or data structure was the most important and helpful task.  It was not always immediately obvious (to me) what role a particular variable had, so making a conjecture and then refining it was quite common.

Looking for sections of code which write to video memory was a helpful technique, because by noting where the data was read from, I could tell whether that section drew the player ship, a defender ship, etc.

Almost all of the work was done just by looking at the code, although for a handful of tricky parts I used [the XRoar emulator](https://www.6809.org.uk/xroar/), and its ability to act as a debug target for a custom build of the GNU Debugger.  In particular, I decided that working out the exact waveform of a sound effect from the code was too much work; see below.


# Port to Pytch

## Layout

Screen dimensions differ.  Overall layout of upper score/display area and lower play area, separated by red bars.  Positioning of defenders.  Vertical spacing of the "lanes" the defenders patrol in.  Horizontal stepping motion is part of design so keep that.  Player ship can have free movement though.

## Graphics

Keep things integer, so sprites had to be different sizes.  Redraw by hand with reference to originals.  Try to keep look/feel of images but had to make some changes.  Sometimes use higher resolution.  Impose symmetry; not sure whether this was the right thing to do, though.

<figure>
<div style="background-color:#1dae15;display:grid;grid-template-columns:1fr 1fr;align-items:center;">
<div style="margin:2.5rem;"><img src="d32-player-ship.png" width="100%"></div>
<div style="margin:2.5rem;"><img src="pytch-player-ship.png" width="100%"></div></div>
<caption><p style="margin:0.5rem;">Dragon 32 and Pytch graphics for the player's ship.</p></caption>
</figure>

## Sounds

Analyse from emulator and re-synthesise.

_One example of audio players for captured vs re-synthesised sounds.  Use howler.js maybe._

## Code

Convert into event-driven style.  Things like stepping through phases of an explosion are then simpler.

## Differences

No joysticks.  One-player only.  No high-score tracking.  Play game once then stop.


# Links

* [Interview with the game's author, Ken Kalish](https://www.lcurtisboyle.com/nitros9/interview.html)
* [*Cobra*: A game my Dad and I wrote on the Dragon 32.](https://redfrontdoor.org/blog/?p=453)
