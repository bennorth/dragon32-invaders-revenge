---
title: The Dragon 32 game _Invader's Revenge_
author: "[Ben North](https://github.com/bennorth)"
date: September 2025
---

# Overview

In my increasingly-distant youth, my family had a Dragon 32 home computer, which I spent many hours with.  For a lot of this time, I was writing programs of various kinds, with the built-in Basic and then also assembly language.  But, unsurprisingly, I also played games, including one called *Invader's Revenge*, written by Kenneth Kalish.  You controlled a yellow ship, and had to shoot enemy ships while not crashing into anything or being shot by the enemy base.  Good fun.

<figure>
<div style="display:grid;grid-template-columns:7fr 5fr;align-items:center;">
<div style="margin:1rem;"><img src="screenshot-1.png" width="100%"></div>
<div style="margin:1rem;"><img src="cassette-inlay.jpg" width="100%"></div></div>
<caption><p style="margin:0.5rem;">Screenshot and cassette inlay for <i>Invader's Revenge</i>.</p><p style="font-size:0.9rem;"><i>Cassette inlay image from <a href="https://archive.worldofdragon.org/">The Dragon Archive</a></i>.</p></caption>
</figure>

In my current job, I am developing and researching [Pytch](https://pytch.org/), a free online educational coding platform which helps people learn Python by writing "Scratch-like" programs.  I thought a port of *Invader's Revenge* could be a good example of what can be made in Pytch.

I could probably have achieved this by taking screenshots and working out the game logic just by observations, but thought it would be a more interesting exercise to reverse engineer the original machine code.  This would also allow a dose of nostalgia for the Dragon and working in assembly language, albeit someone else's.


# Pytch version

_EMBED PYTCH VERSION.  And link for "demo", which allows "see inside"._


# Annotated disassembly

The starting point was a raw binary dump of the game, 7525 bytes long.  Using a combination of existing tools and various bits of ad-hoc Python code, I produced what I hope is a reasonably readable disassembly of the game's code and data.

<style>
pre.asm-snippet {
width: 26em;
margin: 1em auto;
padding: 12px;
background-color: #F9F2AA;
span.comment {
    color: #005740;
    font-style: italic;
    font-weight: bold;
}
span.instr {
    color: #944000
}
span.identifier {
    color: blue;
}
}
</style>
<a href="disassembly.html"><figure>
<div style="background-color: #f8f8f8; margin:1rem; font-size: 2rem; font-family: 'Menlo', 'Monaco', 'Ubuntu Mono', 'Consolas', 'source-code-pro', 'monospace'"><p style="text-align:center;margin:0rem 1rem;">E4&nbsp;84&nbsp;10&nbsp;26&nbsp;03&nbsp;5C E6&nbsp;84&nbsp;C4&nbsp;AA&nbsp;E7&nbsp;80</p></div>
<p style="font-size:3rem;">↧</p>
<div>
<pre class="asm-snippet" style="text-align:left;">
<span class="comment">; Turn next mask byte into red/blue</span>
<span class="comment">; detect mask</span>
  <span class="instr">LDB</span>  ,U+
  <span class="instr">ASLB</span>

<span class="comment">; If the player overlaps with something</span>
<span class="comment">; red or blue...</span>
  <span class="instr">ANDB</span> ,X
<span class="comment">; ...they have hit a defender or defender</span>
<span class="comment">; shot; chain to handler</span>
  <span class="instr">LBNE</span>  <span class="identifier">Sub_HandlePlayerCrash</span>

<span class="comment">; Mask out yellow from destination byte</span>
  <span class="instr">LDB</span>  ,X
  <span class="instr">ANDB</span> #$AA
  <span class="instr">STB</span>  ,X+
</pre>
</figure></a>

## Result

Code and data are shown with different background colours.  Subroutines are cross-linked, to make them clickable at call sites.  Chunks of data which represent graphics are rendered.

* [Disassembly — about 3.5k lines of 6809 assembly language](disassembly.html).

## Observations

Various features of the code struck me as interesting:

* **No pseudo-random numbers.**  Although the behaviour of the defenders seems random, there are not even any pseudo-random numbers involved.  The random-looking behaviour emerges from the deterministic logic for starting new defender patrols.
* **Interleaved code and data.**  The lump of machine code is not neatly divided into data and code.  Code is interspersed with data; sometimes a variable appears in the middle of the code for the subroutine it is used in.
* **Fine-grained movement for the player ship.**  The defenders move horizontally by four pixels at a time, allowing simpler code because four pixels are stored in one byte of video memory.  The fact that the defenders move in four-pixel steps is part of the style of the game.  But the player can move at a two-pixel resolution, and has two different bitmaps (["right position"](disassembly.html#LBL--GFX_PlayerRightPosn) and ["left position"](disassembly.html#LBL--GFX_PlayerLeftPosn)) to support this.
* **Inventive use of the system stack.**  I saw a few nice examples of manipulating values stored on the system stack, for example overwriting a saved value, multiplying by three, and saving a `RTS` opcode by pulling the program counter in the same instruction as restoring a saved register.
* **Seemingly unused variables.**  There are a few locations which are written to but, as far as I could tell, never read from, so their purpose is unclear to me.  There are other locations which are, as far as I can tell, completely unused.
* **Seemingly unused graphics.**  There are some bytes near the start which can be interpreted as [a small defender-like graphic](disassembly.html#LBL--GFX_SmallUnusedDefender).  Maybe there were plans to use this as another "special" defender?
* **Fall-through code.**  In a few places, one subroutine "falls through" into another.  Another way of thinking of this is that some routines have multiple entry points.
* **Collision detection via colours.**  In some situations, the code measures the game state by reading the video display memory, rather than with reference to stored program data.  The code looks for the presence of, say, a defender, by looking for pixels which are either blue or red.  I suspect the choice of this colour scheme was influenced by the fact that the two-bit codes for blue and red are `10` and `11` respectively, allowing a simple bitwise-and test for defender-coloured pixels.
* **Split responsibility for destroying defenders.**  As far as I can tell, the job of destroying a defender when a player's shot hits it is split between the [subroutine which moves the shots](disassembly.html#LBL--Sub_MovePlayerShotsDown), and [the subroutine which moves the defenders](disassembly.html#LBL--Sub_MoveDefenderCheckHit).  This all seems quite intricate but I expect is the best fit for the data structures used and the time constraints the code works under.
* **Timekeeping with delays or sounds.**  Each update usually ends with a do-nothing delay loop, which gets shorter as the player gets more points.  But when a sound effect is playing, bit-banging the audio output serves the dual purpose of creating the delay, so the do-nothing loop is skipped.  The sound effects have to match the dynamic delay, so the sound effects get more frantic as the game speeds up — this counts as a feature I think.
* **Score stored in Binary Coded Decimal.**  The player's score is stored in units of 100 points, as a four-digit BCD (16-bit) value.  The code uses the special 6809 instruction `DAA` (for _Decimal Adjust after Addition_) for arithmetic with BCD values.  The logic for awarding an extra life each 10,000 points falls out in a pleasingly simple way from this representation.
* **Differing basic block layout.**  Code which in a high-level language would be an `if/else` is laid out differently in different places.  Sometimes one of the blocks is 'inline', and other times both the `if` and the `else` arms are separate and jumped to and from.
* **Iteration over arrays.**  Sometimes this is done by counting how many entries remain to be processed, and other times by comparing the record pointer with the "one past the end" value.
* **Looping and sequencing split over updates.**  The fundamental logic implemented by [the code which animates the result of a defender shot hitting something](**TODO**) is reasonably straightforward.  However, the code has to carefully track progress through the logic with an explicit state value, because it has to do a small piece of work each time it is called.  This makes the code more complex.
* **Partially-written single joystick mode?**  There is some duplicated state for recording whether the game is in one- or two-player mode.  Different variables are used in the logic for player state vs the logic for selecting which joystick to read.  I wonder whether there were plans to allow two players to play a two-player game where only one joystick was used.
* **Stack leak.**  The code which implements the timeout when prompting the user for the speed and number of shots leaks two bytes of stack, because it does a `JMP` to the reset routine even though conceptually it is a subroutine.  This was suspected by code inspection and verified under GDB.  Compare the care taken in a similar situation in the [end-of-game code](disassembly.html#LBL--Sub_EndOfGame).
* **Unused slot for defender explosion data?**  There is [space reserved](disassembly.html#LBL--Arr_DefenderExplosions) for up to ten defender explosions.  However, the [code which processes this array](disassembly.html#LBL--Sub_StepDefenderExplns) seems to only handle the first nine entries — it initialises a counter to `10` then, in each iteration, decrements this counter and then tests it for being non-zero.  I wasn't able to verify this behaviour in play though.
* **Large unused section of memory image.**  The cassette memory image has a 602-byte section (out of a 7,525-byte image) of meaningless values, as far as I can tell.  Perhaps this came about from a development process which made it difficult to mode large blocks of code or data, and so space had to be reserved?

## Methods used while reverse-engineering

I had heard of, and wanted to try, the special-purpose reverse-engineering disassembler [IDA](https://hex-rays.com/), but the free version does not support the 6809 processor.  Only too late did I discover the free-software [Cutter](https://cutter.re/), based on [Rizin](https://rizin.re/), which does support the 6809.  This might be worth exploring if I do something like this again.

The tool I ended up using was [f9dasm](https://github.com/Arakula/f9dasm).  As well as the binary machine-code dump, you supply a separate file of annotations and other directives.  The `f9dasm` tool then disassembles the machine code according to your directives and annotations.  I added a post-processing step, implemented as a collection of ad-hoc Python scripts, to break the disassembly into "chunks" for more readable rendering in HTML.  A "chunk" is a subroutine or a piece of data.

The whole process was highly iterative.  The starting point was to trace execution from the entry-point address, and then go round and round with a mixture of the following activities.

* Identify a subroutine or block of data.
* Decode a block of data representing a graphics sprite.
* Conjecture the fields of a data structure.
* Conjecture the semantics of a variable.
* Conjecture what a particular subroutine did with variables or overall machine state (e.g., display or sound).
* Make or refine notes and comments on a subroutine, variable, or data structure.
* Give a name to a subroutine or piece of data.

Understanding a variable or data structure was the most important and helpful task.  It was not always immediately obvious (to me) what role a particular variable had, so making a conjecture and then refining it was quite common.

Looking for sections of code which write to video memory was a helpful technique, because by noting where the data was read from, I could tell whether that section drew the player ship, a defender ship, etc.

Almost all of the work was done just by looking at the code, although for a handful of tricky parts I used [the XRoar emulator](https://www.6809.org.uk/xroar/), and its ability to act as a debug target for a custom build of the GNU Debugger.  In particular, I decided that working out the exact waveform of a sound effect from the code was too much work; see below.


# Port to Pytch

## Layout

The Dragon and Pytch screen dimensions differ.  The Dragon, in the graphics mode used, has a 128×192 pixel grid, with each pixel twice as wide as it is high.  The Pytch "stage" is 480×360.

In broad terms, the game layout has an upper score/display area, and a lower play area, separated by a pair of thin red bars.  The Dragon also has a fairly broad border round the active display area.  I drew a static background image which I hope is a reasonable replication of the overall effect.

The defenders patrol in horizontal "lanes".  I tried to get a close match to the spacing of these lanes, including a gap such that the player cannot be hit at a particular vertical position.  This is coupled with the graphics design in terms of the dimensions of the sprites; see below.

## Movement

The horizontal "stepping" motion of the defenders and their base is part of the aesthetics of the design, so I kept that.  In the Dragon original, the player ship has finer-grained movement; in the port I allow it to move with single-pixel resolution.

## Graphics

To keep things on an integer grid, the sprites had to be different sizes to the originals.  I redrew them by hand with reference to the originals, trying to keep the look and feel of images, but I did have to make some changes.  In some cases I used the higher resolution available.  For some explosion graphics, the original was not symmetrical; here I drew symmetrical versions, although I'm not sure whether this was the right thing to do.

Example of a higher-resolution sprite:

<figure>
<div style="background-color:#1dae15;display:grid;grid-template-columns:1fr 1fr;align-items:center;">
<div style="margin:2.5rem;"><img src="d32-player-ship.png" width="100%"></div>
<div style="margin:2.5rem;"><img src="pytch-player-ship.png" width="100%"></div></div>
<caption><p style="margin:0.5rem;">Dragon 32 and Pytch graphics for the player's ship.</p></caption>
</figure>

## Sounds

From inspection of the code, it was possible to tell that each sound effect consists of a sequence of "chirps" — short fragments of rising or falling pitch.  However, replicating the sound effects based on the code would have required an exact understanding of the timing of the instructions used, so I took a different approach.

Running the game under the XRoar emulator, I captured the sound effects.  Analysing the sounds in Jupyter Lab, and using regression to estimate the starting pitch and rate of change of pitch for each chirp, allowed them to be re-synthesised.  On the Dragon, the output waveform is essentially a square wave.  In the re-synthesis, I used something slightly more rounded.  This gives a softer sound, which I think I'm happy with.

Example of captured vs re-synthesised sound effect:

<figure>
<p style="margin:1rem;">
<button id="sample-btn-1" style="margin:1rem 3rem;"><div><p><img style="margin: 1rem 0.5rem;" src="sound-wave.png"></p><p style="font-size:3rem;">▶</p><p>Captured original</p></div></button>
<button id="sample-btn-2" style="margin:1rem 3rem;"><div><p><img style="margin: 1rem 0.5rem;" src="sound-wave.png"></p><p style="font-size:3rem;">▶</p><p>Re-synthesised</p></div></button>
</p>
</figure>
<script src="howler.core.min.js"></script>
<script src="sound-samples.js"></script>

## Code

With the understanding of the game logic gained from the reverse engineering, I was able to write event-driven code to give (something very close to) the same behaviour.  In some cases, such as stepping through the phases of a defender explosion, the concurrency provided by Pytch made the code much simpler.

## Differences

The Pytch port is not a perfect re-creation.  The main differences in the Pytch version are:

* The player has to use the keyboard; there is no joystick support — although see below.
* The game is one-player only.
* The game does not track the high-score.
* The game plays once and then stops.  You have to click Pytch's "play" button to have another game.
* There is a sound effect when you gain an extra ship at multiples of 10,000 points.

## Hardware controller

We have an experimental version of Pytch which can interface with hardware via the GPIO pins on a Raspberry Pi.  In this version, you *can* play Invader's Revenge with an arcade-style joystick and fire button.

<figure>
<div style="display:grid;">
<div style="margin:1rem;"><img src="Pytch-hw-invaders-revenge.jpg" width="100%"></div></div>
<caption><p style="margin:0.5rem;">Hardware-enhanced Pytch version of <i>Invader's Revenge</i> running on a Raspberry Pi&nbsp;5.</p></caption>
</figure>


# Conclusions

I ended up getting drawn into this project rather more than I originally planned, but the result was a full understanding of almost all of the code of the game.  Porting the code to Pytch was an interesting exercise, and the resulting game is fun to play.


# Links

* [Interview with the game's author, Ken Kalish](https://www.lcurtisboyle.com/nitros9/interview.html)
* [*Cobra*: A game my Dad and I wrote on the Dragon 32.](https://redfrontdoor.org/blog/?p=453)
