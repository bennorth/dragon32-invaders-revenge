# Screen layout

The border is part of the look, so keep that.  Generally, scale the
D32 screen (which is 128×192) to the Pytch stage (480×360) by a factor
of 7/4.  This leads to 448×336, and so a border of 16 on each side and
12 at top and bottom.  Game area is then

* -224 <= x <= 224
* -168 <= y <= 168

Sections of game area are:

* Scores display
* Stack of player sprites indicating lives
* Double red line separating top/main areas
* Main play area

Our defenders are 12 high.


## Defender base

Is (on D32) 9 high and enters play at either:

* $1CA0 = (0, 181)
* $1CBE = (120, 181)

after being destroyed, alternating sides.  That (x, y) pair is the
location of the top-left pixel of the full (padded) sprite.  So the
base covers rows 181–189, leaving two unused rows below it.  In Pytch,
want base to have its bottom edge at y=-165 or so.


## Double red line

In D32, drawn starting at location $0AE0 (for the lower one), with
-$40 for the upper one.

* Upper stripe at row 37 --- Pytch y = 103.25; row 76.75 of 480×360 img
* Lower stripe at row 39 --- Pytch y = 106.75; row 80.25 of 480×360 img

So maybe Pytch backdrop image rows 76, 77, 80, 81?  Try that into
background.png file.


## Text

Player 1 SCORE label is drawn with top-left corner at $0640 = (0, 2).

Player 1 score value drawn (24, 2)

Top line of text covers rows 2–6 incl.

HIGH SCORE text and value covers rows 10–14 incl.  Label drawn with
top-left corner at $0747 = (28, 10).
