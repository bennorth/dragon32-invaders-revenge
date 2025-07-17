# Graphics assets

Original dimensions of true image (i.e., excluding any padding down
the edge/s) given as width×height in D32 pixels.  A D32 pixel is twice
as wide as it is high.


## Sprites

### Standard defender

Blue unless exploding.  8×7 in D32 version; 28×12 in Pytch version.

✓ $2D7A 8×7 Standard defender (blue)

✓ $3AF9 8×7 Standard defender (yellow)

✓ $3B07 8×7 Standard defender (red with yellow eyes)

✓ $2F1A 8×7 Square-ish explosion --- used when standard defender destroyed

When making new graphics, I changed the explosion to be symmetrical.
Not sure whether original asymmetry was intentional but think it might
look better symmetrical.

### Special defender

Red unless exploding.  8×7 in D32 version; 28×12 in Pytch version.

✓ $2D6C 8×7 Special defender (red)

✓ $3B15 8×7 Special defender (yellow)

✓ $3B23 8×7 Special defender (red with yellow eyes)

✓ $2F64 8×7 Red and yellow sparks --- used when special defender destroyed

### Player (invader)

Yellow including when exploding.  Non-exploding is 9×6 in D32 version;
32×10 in Pytch version.  Only one graphic needed for Pytch.  Exploding
is 14×8 in D32; 50×16 in Pytch.

✓ $31C1 9×6 Player (in more rightwards position in byte grid)

✓ $31D3 9×6 Player (in more leftwards position in byte grid)

✓ $353A 14×8 Yellow exploding player

Two variants of exploding player done.  Not sure which I prefer.

### Defender base

Blue unless exploding.  7×9 in D32 version; 26×16 in Pytch version.

✓ $3378 7×9 Defender base (blue)

✓ $3B31 7×9 Red with yellow sparks defender base

✓ $3B43 7×9 Yellow with red sparks defender base

When making new graphics, I changed the exploding variants to be
symmetrical.  Not sure whether original asymmetry was intentional but
think it might look better symmetrical.

### Explosions

7×5 in D32 version; 26×10 in Pytch version.

✓ $34BC 7×5 Red "asterisk" explosion

✓ $34C6 7×5 Yellow "asterisk" explosion

### Converted to Pytch scale

Good if both dimensions are even, so when we position them at integer
coordinates, the images fit the pixel grid.


## Text as graphics

$2FAE "SHOTS"

$2FC8 "SPEED"

$2FE2 " [1-5]"

$3001 "SELECT "

$3065 "PAUSE" (blue)

$3084 "PAUSE" (mixed colours)

$365E "HIGH "

$3677 "SCORE"

$3691 "0"

$3696 "1"

$369B "2"

$36A0 "3"

$36A5 "4"

$36AA "5"

$36AF "6"

$36B4 "7"

$36B9 "8"

$36BE "9"

Only made Pytch versions of the digits.  The other pieces of text are
for questions that the Pytch version doesn't ask.  (How many shots
allowed at once?  What speed do the defenders move?)
