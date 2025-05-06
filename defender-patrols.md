# Defender patrols

Starting at loaded address $2DEF, there are 14 pointers into video
RAM, corresponding to the last bytes of various rows.  Recall that the
video RAM is interpreted as a 128-column by 192-row raster.  Each row
consists of 32 bytes; each byte describes 4 pixels; each pixel can be
one of four colours as per the palette 0=G, 1=Y, 2=B, 3=R.

Actual RGB colours for these (for simulated PAL output), taken from
screengrabs of the web version of xroar, are

00 = Green  = #1dae15
01 = Yellow = #ffff83
10 = Blue   = #1b166b
11 = Red    = #6d0e24

In the order they are stored, these rows are:

    40, 102, 137, 66, 84, 93, 48, 117, 157, 75, 57, 127, 147

A right-to-left patrol occurs with the top row of the defender on the
given row, but a left-to-right patrol occurs on the next row down.  We
might not replicate this piece of behaviour.

Sorted (from highest-on-screen row to lowest), this list is:

    40, 48, 57, 66, 75, 84, 93, 102, 117, 127, 137, 147, 157

(So the bottom patrol, when travelling left-to-right, covers rows
158–164 (inclusive).  Cf the defender base which covers rows 181–189
(inclusive).  Gap of 16 rows, confirmed by screengrab.)

Gaps are:

    40   48   57   66   75   84   93  102  117  127  137  147  157
       8    9    9    9    9    9    9   15   10   10   10   10

and recall that both defender sprites (blue/red) are 7 rows tall in
D32 (and 12 rows tall in Pytch).  That 15 stride is just big enough
for a defender plus the player, bearing in mind that the defenders
patrol on different rows L-to-R vs R-to-L.

State is maintained as to which row is due to have a patrol next,
wrapping round.  If a row is busy, the next row (in the stored order)
is examined, and so on.

There are at most 11 defenders on patrol at once.

In Pytch, we have a 480×360 screen rather than a 128×192 one.  And the
defender sprites are 12 rows tall.

We are leaving a border, and then scaling the display area by 7/4 to
get 448×336.  Just naive scaling and rounding gives (sorted top to
bottom):

patrol_ys = [104, 90, 74, 58, 43, 27, 11, -4, -31, -48, -66, -83, -101]

with diffs

14 : 16 : 16 : 15 : 16 : 16 : 15 : 27 : 17 : 18 : 17 : 18

Adjust to

14 : 16 : 16 : 16 : 16 : 16 : 16 : 27 : 17 : 17 : 17 : 17

The 27 stride is big enough for defender (12) plus player (10).  Final
list, in "scrambled" order:

[104, -6, -67, 58, 26, 10, 90, -33, -101, 42, 74, -50, -84]
