``` c
Sub_AwardPoints() {
  active_player->score += (100 * a);  // Worked out in BCD

  if (that addition carried into the 10000s) {
    x = active_player->Loc_top_lives_display_ship;
    a = active_player->x_position_fraction;

    // Only award another ship if the player has room for
    // it.  The player can have at most three ships above
    // the double line (and then the one in play).
    if (x > 0x071d) { // 0x071d is pixel at (x=29, y=8)
      active_player->n_lives += 1;
      x -= 7 × 0x20;
      active_player->Loc_top_lives_display_ship = x;
      b = active_player_x_fraction;
      u = active_player_location;
      y = active_player_prev_location;
      active_player_x_fraction = a;  // a = active_player->x_position_fraction
      Sub_14();
      active_player_x_fraction = b;
      active_player_location = u;
      active_player_prev_location = y;
    }
  }

  maybe_increase_difficulty();
  x = active_player->Loc_score_display;
  four_digits_out();
}
```

``` c
Sub_14() {
  redraw_player(loc=x, prev_loc=x);
}
```
