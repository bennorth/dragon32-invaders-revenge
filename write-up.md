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

* **Interleaved code and data.**  The lump of machine code is not neatly divided into data and code.  Code is interspersed with data, sometimes even a variable appearing in the middle of the code for the subroutine it is used in.
* **Inventive use of the system stack.**  I saw a few nice examples of manipulating values stored on the system stack, for example overwriting a saved value, and multiplying by three.
* **Seemingly unused variables.**  There are a few locations which are written to but, as far as I could tell, never read from, so their purpose is unclear to me.
* **Fall-through code.**  In a few places, one subroutine "falls through" into another.  Another way of thinking of this is that some routines have multiple entry points.
* **Collision detection via colours.**  RESUME HERE.

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

_One example of scaled up old vs new comparison._

## Sounds

Analyse from emulator and re-synthesise.

_One example of audio players for captured vs re-synthesised sounds.  Use howler.js maybe._

## Code

Convert into event-driven style.  Things like stepping through phases of an explosion are then simpler.

## Differences

No joysticks.  One-player only.  No high-score tracking.  Play game once then stop.


# Links

* [*Cobra*: A game my Dad and I wrote on the Dragon 32.](https://redfrontdoor.org/blog/?p=453)
