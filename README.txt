Proof on concept for an auto splitter

Use opencv and mss to capture a part of the screen and try to match to the condition of the current split
The condition of the current split would be determined by the user(template matching/whole screen of a color)
Considering the amount of feature and the quality of current split timer tools, this program shouldn't be seen as more than a proof on concept
In its current state the script is hard coded to use Snes9x and use splits for Super Metroid (old route)

some stuff I would like to explore further
    template movement matching to get more split option and also interpolation to better compare splits from different runs
    handling noisy input (capture card footage/some snes have a bright vertical line in the middle...)