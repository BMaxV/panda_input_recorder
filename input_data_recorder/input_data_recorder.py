import time

from direct.showbase.ShowBase import ShowBase
from panda3d.core import KeyboardButton
from direct.gui.DirectFrame import DirectFrame

from panda_interface_glue import panda_interface_glue as pig
from my_save import sxml_main

class InputRecord:
    def __init__(self):
        self.current_record = []
        self.current_time = 0
        self.play_back_time = None
        self.play_back_starttime = None
        self.recording = False
        self.playing = False
        self.current_playback_counter = 0
        self.current_playback_time = None
        self.engine_playback_time = None

        self.engine_too_fast_delta_t = 0

        self.record_inputs = True
        self.record_data = True

    def record(self, inputs, sim_data, delta_t):
        
        if inputs == []:
            inputs = [1]
        self.current_record.append([delta_t, inputs, sim_data])

    def save(self, fn="recordtest.xml"):
        my_data = {"data": self.current_record}
        sxml_main.write(fn, my_data)

    def load(self, fn="recordtest.xml"):
        self.current_record = sxml_main.read(fn)["data"]

    def start_recording(self, *args):
        self.recording = True

    def stop_recording(self, *args):
        self.recording = False
        self.save()

    def start_playback(self, *args):
        self.playing = True
        self.current_playback_counter = 0
        self.current_playback_time = 0
        self.engine_playback_time = 0
        self.load()

    def toggle_pause_playback(self, *args):
        self.playing = not self.playing

    def get_play_inputs(self, engine_delta_t):
        """
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

        """

        if self.playing:
            self.engine_too_fast_delta_t += engine_delta_t

        # see the doc string

        # the basic if / else covers the case that the playback steps > engine steps

        if self.engine_playback_time + self.engine_too_fast_delta_t > self.current_playback_time:
            # if my engine is consistently faster, this is fine.
            if self.current_playback_counter > len(self.current_record)-1:
                self.playing = False
                return 0, [], {}

            delta_t, inputs, game_data = self.current_record[self.current_playback_counter]
            self.current_playback_time += delta_t
            self.current_playback_counter += 1

            self.engine_playback_time += self.engine_too_fast_delta_t
            self.engine_too_fast_delta_t = 0

            # I'm assuming
            # if engine_steps > playback steps, consistently,
            # set the advance of the engine to the advance of the playback

            if self.current_playback_time < self.engine_playback_time:
                self.engine_playback_time = self.current_playback_time

        else:
            self.engine_too_fast_delta_t += engine_delta_t
            delta_t, inputs, game_data = 0, [], {}

        return delta_t, inputs, game_data


class Wrapper:

    def __init__(self):
        self.b = ShowBase()
        self.input_record = InputRecord()

        pig.create_button("start recording", (0.8, 0, 0), 0.05,
                          self.input_record.start_recording, tuple())
        pig.create_button("stop recording", (0.8, 0, -0.1),
                          0.05, self.input_record.stop_recording, tuple())

        pig.create_button("start playback", (0.8, 0, -0.2),
                          0.05, self.start_playback_wrap, tuple())
        pig.create_button("toggle pause playback", (0.8, 0, -0.3),
                          0.05, self.input_record.toggle_pause_playback, tuple())

        pig.create_button("set playback to data", (0.8, 0, -0.4),
                          0.05, self.set_playback_to_data, tuple())

        pig.create_button("set playback to inputs", (0.8, 0, -0.5),
                          0.05, self.set_playback_to_inputs, tuple())

        self.output = []

        self.b.taskMgr.add(move_task, "Move Task",
                           extraArgs=[self], appendTask=True)
        self.bind()

        frameSize = (-0.1, 0.1, -0.1, 0.1)

        self.frame = DirectFrame(pos=(0, 0, 0), frameSize=frameSize)
        self.move_speed = 1

        self.process_inputs = True

    def start_playback_wrap(self, *args):
        # this is for resetting in case I play back inputs
        self.frame.setPos(*(0, 0, 0))
        print(f"processing recorded inputs{self.process_inputs}")
        self.input_record.start_playback()

    def set_playback_to_inputs(self, *args):
        self.process_inputs = True
        print(f"processing recorded inputs{self.process_inputs}")

    def set_playback_to_data(self, *args):
        self.process_inputs = False
        print(f"processing recorded inputs{self.process_inputs}")

    def main(self, delta_t, inputs, apply_data):

        if self.process_inputs:
            org_pos = list(self.frame.getPos())
            if "forward" in inputs:
                org_pos[2] += self.move_speed * delta_t

            if "back" in inputs:
                org_pos[2] += -self.move_speed * delta_t

            if "right" in inputs:
                org_pos[0] += self.move_speed * delta_t

            if "left" in inputs:
                org_pos[0] += -self.move_speed * delta_t
            apply_data = {"framePos": org_pos}

        # either my inputs are live and I apply them and I have data
        # or they are recorded, I apply them and I have data
        # or I just have data

        if "framePos" in apply_data:
            self.frame.setPos(*apply_data["framePos"])

        my_data = {"framePos": list(self.frame.getPos())}
        return my_data

    def bind(self):
        self.buttons_move_actions = {}
        key_action_dict = {
            "w": "forward",
            "a": "left",
            "s": "back",
            "d": "right",
        }

        hold_key_actions = ["forward", "back", "left", "right"]
        for key in key_action_dict:
            if key_action_dict[key] in hold_key_actions:
                nkey = key.encode()
                self.buttons_move_actions.update(
                    {KeyboardButton.ascii_key(nkey): key_action_dict[key]})

    def pass_on(self, my_input, *args):
        self.output.append(my_input)


def move_task(*args):
    # somewhat selfexplanatory? It's the watcher thing that
    # tracks movement inputs

    Task = args[1]
    wrapper = args[0]
    is_down = wrapper.b.mouseWatcherNode.is_button_down

    for mb in wrapper.buttons_move_actions:
        if is_down(mb):
            wrapper.pass_on(wrapper.buttons_move_actions[mb])

    return Task.cont


def main():
    W = Wrapper()
    while True:
        delta_t = globalClock.dt
        W.b.taskMgr.step()
        apply_data = {}

        if W.input_record.playing:
            W.main(*W.input_record.get_play_inputs(delta_t))
        else:
            apply_data = W.main(delta_t, W.output, {})

        if W.input_record.recording:
            W.input_record.record(W.output, apply_data, delta_t)

        W.output = []


if __name__ == "__main__":
    main()
