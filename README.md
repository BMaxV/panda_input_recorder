# panda_input_recorder

WASD moves the box.

There are 6 buttons: 
 
    * start recording
    * stop recording
    * start playing a recording
    * toggle pause playback (not done yet)
    * set playing from inputs (recalculates data based on input)
    * set playing from data (no input recalculation, just apply the data that was saved)
    
It uses my xml save file format, which is not ideal, but it works.
It also uses my interface button creation thing, which is not needed. You can also just use directButtons or whatever else you want to trigger the behavior, like hotkeys etc..

# Mechanically Challenged

This project was submitted to "mechanically challenged" https://mechanicallychallenged.org/

The written explanation for how things work is overe here: Mechanically_Challenged.md

## important-ish timey whimye wibbly wobbly nonsense

Probably really worth considering if you want to have a "playback" feature in your game, think about this (also as a docstring in my "get_play_inputs" function:

```

this is multiple timeline wibbly wobbly confusing stuff. so bear with me.

I have a recorded time line and a time that's currently progressing, as the engine as a playback device tries to render the record.

recording |-----------|
engine    |-----------|

They will probably play at different speeds.

if the engine is faster than the recording

recording |----|  ----| 
            r1
engine    |--|--|--|--|
           e1 e2

I keep track of sum ( e_i )
until the engine_delta_t is bigger than my recorded delta_t

then I pretend that " sum ( e_i ) == r "

and I advance both engine playback time by sum (e_i) and the recording playbacktime by the recorded delta t

if the engine is slower than the recording, the program CANNOT
play the recording at the desired speed

recording |--|--|--| 
           r1 r2 r3
engine    |-------|
             e1 

there is nothing I can do about that, since the game still has 
to process the recorded inputs.

input tick by input tick

The data that's produced probably depends on delta t
AND data that's inside of the data itself.

e.g. if my movement is 

    orientation_1 * speed * delta_t_1 
  + orientation_2 * speed * delta_t_2

I still have to do that operation iteratively and step by step,
I can't pretend that orientation will remain constant and just

    orientation_1 * speed * (delta_t_1 + delta_t_2)

since 

    orientation_1 * speed * delta_t_1 

may put the object inside of or outside of a relevant zone
at some relevant point in time.

Also, different inputs can be held for different lengths in time 
in the recording. If I move for 3 ticks but I only hold a 
charge attack for 1

I would have to analyze my inputs, do math and then pass e.g.

    move_delta_t = delta_t_1 + delta_t_2 + delta_t_3
    orientation_1 * speed * move_delta_t 

    hold_delta_t = delta_t_2
    charge * delta_t_2

and all my game functions kind of assume I have one delta_t

```
