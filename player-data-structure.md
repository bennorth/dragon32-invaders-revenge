# Player data structure

0 int8 defender_base_fire_cycle_length;
1 int8 defender_movement_cycle_length;
2 int8 n_lives;
3 int8 * Loc_top_lives_display_ship;
5 int16 score;  // in units of 100
7 int16 next_difficulty_increase_score;  // in units of 100
9 int8 * Loc_score_display;
b int8 x_position_fraction;


## Sub_MaybeSpeedUp

``` c
d = active_player->score;
if (d >= active_player->next_difficulty_increase_score) {
  d = active_player->next_difficulty_increase_score;

  // Scores are stored in BCD so the below
  // hex constants mean what they look like
  // in decimal.

  if (d > 0x0040)
      d += 0x0025;
  d += 0x0010;
  if (d <= 0x0150) {
    active_player->next_difficulty_increase_score = d;

    active_player->defender_base_fire_cycle_length -= 1;
    if (active_player->defender_base_fire_cycle_length == 0)
        active_player->defender_base_fire_cycle_length += 1;

    active_player->defender_movement_cycle_length -= 1;
    if (active_player->defender_movement_cycle_length == 0)
        active_player->defender_movement_cycle_length += 1;
  }
}
```


So I think we get difficulty increases at:

3, 13, 23, 33, 43, 78, 113, 148

(times 100 points)


Initialised in memory image:

``` c
player_0 = {
  defender_base_fire_cycle_length: 14,
  defender_movement_cycle_length: 0,
  n_lives: 3,
  Loc_top_lives_display_ship: $07E1, // (4, 15)
  score: 0,
  next_difficulty_increase_score: 3,
  Loc_score_display: $064B, // (44, 2)
  x_position_fraction: 0,
};

player_1 = {
  defender_base_fire_cycle_length: 14,
  defender_movement_cycle_length: 0,
  n_lives: 3,
  Loc_top_lives_display_ship: $07FD, // (116, 15)
  score: 0,
  next_difficulty_increase_score: 3,
  Loc_score_display: $065F, // (124, 2)
  x_position_fraction: -1,
};
```


Main_1

For each player structure,

player->defender_base_fire_cycle_length = Var_b_83
player->defender_movement_cycle_length = Var_b_20

Var_b_83 init'd to 0x0d and never set (unless aliased somewhere)
Var_b_20 init'd to 0x0d and never set (unless aliased somewhere)

player_0 -> Loc_top_lives_display_ship = $07E0 = (0, 15)
player_1 -> Loc_top_lives_display_ship = $071D = (116, 8)

And to get the location correct,

* player-0 lives display ships are drawn with X-fraction = $ff
* player-1 lives display ships are drawn with X-fraction = $00

Ready for when the user is asked about speed and shots, lives-display
ships are drawn at

Player 0: $0700 (0, 8); $08C0 (0, 22); $07E0 (0, 15)
Player 1: $071D (116, 8); $07FD (116, 15); $08DD (116, 22)

and then some further juggling because Player 0 will have their first
ship moved into the play area.
