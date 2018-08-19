import split_event
import cv2
import numpy as np
from const import *

DOOR_H = split_event.TemplateMatch("d/door_h.png")
DOOR_V = split_event.TemplateMatch("d/door_v.png")
DOOR_V2 = split_event.TemplateMatch("d/door_v2.png")
DOOR_V_LONG = split_event.TemplateMatch("d/longdoor_v.png")
DOOR_V_SHORT = split_event.TemplateMatch("d/shortdoor_v.png")
VARIA_FACE = split_event.TemplateMatch("d/varia.png")
DOOR_C = split_event.TemplateMatch("d/door_c.png")
FADE_BLACK = split_event.ColorMatch((0, 0, 0))


class Split(object):
    def __init__(self, name, split_event, sleep_time=1.9, condition=None):
        self.name = name
        self.event = split_event
        self.sleep_time = sleep_time
        self.time = -1
        self.condition = condition

    def reset(self):
        self.time = -1

    def skip(self):
        self.time = 0

    def set_split_time(self, frame_time, start_time):
        if not start_time:
            self.time = 0
        else:
            self.time = frame_time - start_time

    def test(self, frame, frame_time, start_time):
        #return tuple (nb of split to skip, sleep_time)
        r = self.event.frame_test(frame)
        if r:
            if self.condition:
                c_r = self.condition.test(r, frame_time)  # return
                if c_r:
                    self.set_split_time(self.condition.interpolated_time, start_time)
                return self.condition.get_state()
            else:
                self.set_split_time(frame_time, start_time)
                return 1, self.sleep_time
        return 0, 0


class DoorDirectionCondition(object):
    #TODO add a stack where you pile "new split"? wouldn't work if you do r->l->r->l and it's not the same doors
    #direction: char in LRUD (left, right, up, down)
    sleep_offset = 0.3

    def __init__(self, direction):
        super().__init__()
        if direction not in "LRUD" or len(direction) != 1:
            raise AttributeError
        self.dx, self.dy = 0, 0
        if direction == "L":
            self.dx = -1
        elif direction == "R":
            self.dx = 1
        elif direction == "U":
            self.dy = -1
        elif direction == "D":
            self.dy = 1
        self.direction = direction
        self.interpolated_time = -1
        self.state = ()
        self._previous_position = None

    def wrong_direction(self):
        self.state = (0, 6)
        self._previous_position = None
        print("wrong door direction transition")

    def get_state(self):
        if self.state:
            if self.state[0]:
                self._previous_position = None
            s = self.state
            self.state = ()
            return s
        else:
            return 0, 0

    @staticmethod
    def time_from_center(cx, cy):
        return ((cx - 256//2)/4)*FRAME_TIME, ((cy - 224//2)/4)*FRAME_TIME

    def test(self, event_result, frame_time):
        #event_result is a pygame rect
        if not self._previous_position:
            self._previous_position = event_result
            self.state = (0, 0)
            return False
        else:
            if self._previous_position.topleft == event_result.topleft:
                self.state = (0, 0)
                return False
            dx = event_result.x - self._previous_position.x
            dy = event_result.y - self._previous_position.y
            if dx < 0:  # move to the left => it's a R door
                if self.dx <= 0:
                    self.wrong_direction()
                    return False
                else:
                    cx = event_result.centerx
                    #t = (cx - (256//2)/4)*FRAME_TIME  # distance from center * 1frame/4px * 1sec/60frames
                    #if t is past the center (left side) (then t is negative (the middle was some frame before))
                    self.interpolated_time = frame_time + self.time_from_center(cx, 0)[0]
                    self.state = (1, (cx/4)*FRAME_TIME + self.sleep_offset)
                    return True
            elif dx > 0:  # move to the right => L door
                if self.dx >= 0:
                    self.wrong_direction()
                    return False
                else:
                    cx = event_result.centerx
                    self.interpolated_time = frame_time - self.time_from_center(cx, 0)[0]
                    self.state = (1, ((256 - cx)/4)*FRAME_TIME + self.sleep_offset)
                    return True
            if dy < 0:  # move to the top => it's a D door
                if self.dy <= 0:
                    self.wrong_direction()
                    return False
                else:
                    cy = event_result.centery + SM_HUD_HEIGHT//4
                    self.interpolated_time = frame_time + self.time_from_center(0, cy)[1]
                    self.state = (1, (cy/4)*FRAME_TIME + self.sleep_offset)
                    return True
            elif dy > 0:  # move to bot => it's a L door
                if self.dy >= 0:
                    self.wrong_direction()
                    return False
                else:
                    cy = event_result.centery + SM_HUD_HEIGHT//4
                    self.interpolated_time = frame_time - self.time_from_center(0, cy)[1]
                    self.state = (1, ((224 - cy)/4)*FRAME_TIME + self.sleep_offset)
            return False

L_DOOR = DoorDirectionCondition("L")
R_DOOR = DoorDirectionCondition("R")
U_DOOR = DoorDirectionCondition("U")
D_DOOR = DoorDirectionCondition("D")


route = [
    Split("Start", FADE_BLACK, 9),
    Split("Ceres Elevator", FADE_BLACK),
    Split("Falling Tiles", DOOR_C, condition=R_DOOR),
    Split("Magnet Stairs", DOOR_C, condition=R_DOOR),
    Split("Dead Scientist", DOOR_C, condition=R_DOOR),
    Split("58", FADE_BLACK, 9),
    Split("Ceres Ridley", FADE_BLACK),
    Split("58 Escape", DOOR_C, condition=L_DOOR),
    Split("Dead Scientist Escape", DOOR_C, condition=L_DOOR),
    Split("Magnet Stairs Escape", DOOR_C, condition=L_DOOR),
    Split("Falling Tiles Escape", FADE_BLACK, 6),
    Split("Ceres Escape", FADE_BLACK, 50),
    Split("Landing Site", DOOR_H, condition=L_DOOR),
    Split("Parlor", DOOR_V, condition=D_DOOR),
    Split("Moonfall Climb", DOOR_H, condition=R_DOOR),  #fast scrolling glitch the door tiles but it's still matched!
    Split("Pit", DOOR_H, condition=R_DOOR),
    Split("Elevator to Morphball", FADE_BLACK),
    Split("Morphball", DOOR_H, condition=R_DOOR),
    Split("Construction", DOOR_H, condition=L_DOOR),
    Split("First Missile", DOOR_H, condition=R_DOOR),
    Split("reConstruction", DOOR_H, condition=L_DOOR),
    Split("Morph Elevator", FADE_BLACK),
    Split("Elevator from Morphball", DOOR_H, condition=L_DOOR),
    Split("Pit Awake", DOOR_H, condition=L_DOOR),
    Split("Climb Awake", DOOR_V, condition=U_DOOR),
    Split("Parlor Awake", DOOR_H, condition=R_DOOR),
    Split("Flyway", DOOR_H, condition=R_DOOR),
    Split("Bomb Torizo", DOOR_H, condition=L_DOOR),
    Split("Flyway from Bomb", DOOR_H, condition=L_DOOR),
    Split("Alcatraz", DOOR_H, condition=L_DOOR),
    Split("Terminator", DOOR_H, condition=L_DOOR),
    Split("Green Pirates", DOOR_H, condition=L_DOOR),
    Split("Mushrooms", DOOR_H, condition=L_DOOR),
    Split("Green Brinstar Elevator", FADE_BLACK),
    Split("Green Brinstar Shaft", DOOR_H, condition=R_DOOR),
    Split("Early Supers", DOOR_H, condition=L_DOOR),
    Split("Green Shaft to Pink", DOOR_H, condition=R_DOOR),
    Split("Dachora", DOOR_H, condition=R_DOOR),
    Split("Big Pink", DOOR_H, condition=R_DOOR),
    Split("Green Hill", DOOR_H, condition=R_DOOR),
    Split("Noob Bridge", DOOR_H, condition=R_DOOR),
    Split("Red Tower", DOOR_H, condition=R_DOOR),
    Split("Bat", DOOR_H, condition=R_DOOR),
    Split("Below Spazer", DOOR_H, condition=R_DOOR),
    Split("Maridia Tube???", DOOR_H, condition=R_DOOR),
    Split("Warehouse Entrance", DOOR_H, condition=R_DOOR),
    Split("Hi Zeela", DOOR_V_LONG, condition=U_DOOR),
    Split("Hi Kihunters", DOOR_H, condition=R_DOOR),
    Split("Hi Baby Kraid", DOOR_H, condition=R_DOOR),
    Split("Hi Kraid Eye Door", FADE_BLACK),
    Split("Hi Kraid", FADE_BLACK),
    Split("Varia", VARIA_FACE),
    Split("Bye Kraid", DOOR_H, condition=L_DOOR),
    #Split("Bye Kraid Eye Door", DOOR_H),  # in the middle of kraid's room everything is black
    Split("Bye Baby Kraid", DOOR_H, condition=L_DOOR),
    Split("Bye Kihunters", DOOR_V_LONG, condition=D_DOOR),
    Split("Bye Zeela", DOOR_H, condition=L_DOOR),
    Split("Norfair Elevator", FADE_BLACK),  #**************
    Split("Business Center to HJ", DOOR_H, condition=R_DOOR),
    Split("HJ ETank", DOOR_H, condition=R_DOOR),
    Split("Hi Jump Boot", DOOR_H, condition=L_DOOR),
    Split("Skip Missile", DOOR_H, condition=L_DOOR),
    Split("Business Center", DOOR_H, condition=R_DOOR),
    Split("Cathedral Entrance", DOOR_H, condition=R_DOOR),
    Split("Cathedral", DOOR_H, condition=R_DOOR),
    Split("Rising Tide", DOOR_H, condition=R_DOOR),
    Split("Bubble Mountain to HJ", DOOR_H, condition=R_DOOR),
    Split("Bat Cave", DOOR_H, condition=R_DOOR),
    Split("Speed Booster Hall", DOOR_H, condition=R_DOOR),
    Split("Speed Booster", DOOR_H, condition=L_DOOR),
    Split("Speed Booster Escape", DOOR_H, condition=L_DOOR),
    Split("Bat Cave Escape", DOOR_H, condition=L_DOOR),
    Split("Bubble Mountain to WB", DOOR_H, condition=R_DOOR),
    Split("Single Chamber to WB", DOOR_H, condition=R_DOOR),
    Split("Double Chamber to WB", DOOR_H, condition=R_DOOR),
    Split("Wave Beam", DOOR_H, condition=L_DOOR),
    Split("Double Chamber", DOOR_H, condition=L_DOOR),
    Split("Single Chamber", DOOR_H, condition=L_DOOR),
    Split("Bubble Mountain", DOOR_H, condition=L_DOOR),
    Split("Upper Norfair Farming", DOOR_H, condition=L_DOOR),
    Split("Frog Speedway", DOOR_H, condition=L_DOOR),
    Split("Frog Savestation", DOOR_H, condition=L_DOOR),
    Split("Business Center to WS", FADE_BLACK),
    Split("Warehouse Entrance to WS", DOOR_H, condition=L_DOOR),
    Split("Maridia Tube to WS", DOOR_H, condition=L_DOOR),
    Split("Below Spazer Spark", DOOR_H, condition=L_DOOR),
    Split("Bat Spark", DOOR_H, condition=L_DOOR),
    Split("Red Tower Climb", DOOR_H, condition=R_DOOR),
    Split("Hellway", DOOR_H, condition=R_DOOR),
    Split("Caterpillar", DOOR_H, condition=L_DOOR),
    Split("Alpha Power Bomb", DOOR_H, condition=R_DOOR),
    Split("Caterpillar PB", FADE_BLACK),
    Split("Red Brinstar Elevator PB", DOOR_V2, condition=U_DOOR),  # **********
    Split("Crateria Kihunter PB", DOOR_H, condition=R_DOOR),
    Split("The Moat", DOOR_H, condition=R_DOOR),  # **********
    Split("Ocean Fly", DOOR_H, condition=R_DOOR),
    Split("Wrecked Ship Entrance", DOOR_H, condition=R_DOOR),
    Split("WS Shaft Asleep", DOOR_V, condition=D_DOOR),
    Split("Basement Asleep", DOOR_H, condition=R_DOOR),
    Split("Phantoon", DOOR_H, condition=L_DOOR),
    Split("Basement Awake", DOOR_V, condition=U_DOOR),
    Split("WS Shaft Awake", DOOR_H, condition=L_DOOR),
    Split("WS Super", DOOR_H, condition=R_DOOR),
    Split("WS Shaft Climb", DOOR_V_SHORT, condition=U_DOOR),
    Split("Attic", DOOR_H, condition=L_DOOR),
    Split("Floating Platforms", DOOR_H, condition=R_DOOR),
    Split("Bowling Approach", DOOR_H, condition=R_DOOR),
    Split("Bowling Alley", DOOR_H, condition=L_DOOR),
    Split("Gravity", DOOR_H, condition=L_DOOR),
    Split("West Ocean", DOOR_H, condition=L_DOOR),
    Split("Moat to Maridia", DOOR_H, condition=L_DOOR),
    Split("Crateria Kihunter to Maridia", DOOR_V2, condition=D_DOOR),
    Split("Elevator to Maridia", FADE_BLACK),
    Split("Caterpillar to Maridia", DOOR_H, condition=L_DOOR),
    Split("Hellway to Maridia", DOOR_H, condition=L_DOOR),
    Split("Red Tower Fall", DOOR_H, condition=R_DOOR),
    Split("Bat to Maridia", DOOR_H, condition=R_DOOR),
    Split("Bellow Spazer to Maridia", DOOR_H, condition=R_DOOR),
    Split("Tube", DOOR_V2, condition=U_DOOR),
    Split("Main Street", DOOR_H, condition=R_DOOR),
    Split("Fish Tank", DOOR_V2, condition=U_DOOR),
    Split("Everest", DOOR_H, condition=R_DOOR),
    Split("Crab Shaft", DOOR_H, condition=R_DOOR),
    Split("Aqueduct", DOOR_V, condition=U_DOOR),
    Split("Botwoon Hallway", DOOR_H, condition=R_DOOR),
    Split("Botwoon", DOOR_H, condition=R_DOOR),
    Split("Botwoon ETank", DOOR_H, condition=R_DOOR),
    Split("Halfie Climb", DOOR_H, condition=R_DOOR),
    Split("Colosseum", DOOR_H, condition=R_DOOR),
    Split("Draygon Eye Door", FADE_BLACK),
    Split("Draygon", DOOR_H, condition=L_DOOR),
    Split("Reverse Halfie", DOOR_H, condition=L_DOOR),
    Split("To Cac Alley", DOOR_H, condition=L_DOOR),
    Split("Cactus Alley", DOOR_H, condition=L_DOOR),
    Split("Cacatac", DOOR_H, condition=L_DOOR),
    Split("Butterfly", DOOR_H, condition=L_DOOR),
    Split("Plasma Spark", DOOR_H, condition=R_DOOR),
    Split("Kassiuz Climb", DOOR_H, condition=R_DOOR),
    Split("Puyo!", DOOR_H, condition=R_DOOR),
    Split("Plasma", DOOR_H, condition=L_DOOR),
    Split("Plasma Tutorial", DOOR_H, condition=L_DOOR),
    Split("Kassiuz Fall", DOOR_H, condition=L_DOOR),
    Split("Oasis", DOOR_H, condition=L_DOOR),
    Split("Sand Hall", DOOR_H, condition=L_DOOR),
    Split("Crab Hole Tunnel", DOOR_H, condition=L_DOOR),  # room too fast?
    Split("Crab Hole", DOOR_H, condition=L_DOOR),
    Split("East Tunnel", DOOR_H, condition=R_DOOR),
    Split("Norfair Elevator to Ice", FADE_BLACK),
    Split("Business Center to Ice", DOOR_H, condition=L_DOOR),
    Split("Ice Shutters", DOOR_H, condition=L_DOOR),
    Split("Ice Acid", DOOR_H, condition=L_DOOR),
    Split("Ice Snake", DOOR_H, condition=R_DOOR),
    Split("Ice Beam", DOOR_H, condition=L_DOOR),
    Split("Ice Snake down", DOOR_H, condition=R_DOOR),
    Split("Ice Acid Mockball", DOOR_H, condition=R_DOOR),
    Split("Ice Shutters Mockball", DOOR_H, condition=R_DOOR),
    Split("Business Center to LN", DOOR_H, condition=R_DOOR),
    Split("Frog Save to LN", DOOR_H, condition=R_DOOR),
    Split("Frog Speedway to LN", DOOR_H, condition=R_DOOR),
    Split("Farming Room to LN", DOOR_H, condition=R_DOOR),
    Split("Bubble Mountain to LN", DOOR_V, condition=D_DOOR),
    Split("Purple Shaft", DOOR_H, condition=R_DOOR),
    Split("Magdollite", DOOR_H, condition=R_DOOR),
    Split("Kronic Boost", DOOR_H, condition=L_DOOR),
    Split("Lava Dive", DOOR_H, condition=L_DOOR),
    Split("Lower Norfair Elevator", FADE_BLACK),
    Split("Main Hall", DOOR_H, condition=R_DOOR),
    Split("Fast Pillars Setup", DOOR_H, condition=R_DOOR),
    Split("Pillar", DOOR_H, condition=R_DOOR),
    Split("WRITG", DOOR_H, condition=R_DOOR),
    Split("Amphitheatre", DOOR_H, condition=R_DOOR),
    Split("Red Kihunter Shaft", DOOR_V, condition=D_DOOR),
    Split("WasteLand", DOOR_H, condition=L_DOOR),
    Split("Metal Pirates", DOOR_H, condition=L_DOOR),
    Split("Plowerhouse", DOOR_H, condition=L_DOOR),
    Split("Ridley's Farming", DOOR_H, condition=L_DOOR),
    Split("Ridley", DOOR_H, condition=R_DOOR),
    Split("Ridley Escape", DOOR_H, condition=R_DOOR),
    Split("Plowerhouse Escape", DOOR_H, condition=R_DOOR),
    Split("Metal Pirates Escape", DOOR_H, condition=R_DOOR),
    Split("WasteLand Escape", DOOR_V, condition=U_DOOR),
    Split("Red Kihunter Shaft Climb", DOOR_H, condition=R_DOOR),
    Split("LN Fireflea", DOOR_H, condition=L_DOOR),
    Split("Spring Ball Maze", DOOR_H, condition=L_DOOR),
    Split("Three Muskateers", DOOR_H, condition=L_DOOR),
    Split("Single Chamber to Tourian", DOOR_H, condition=L_DOOR),
    Split("Bubble Mountain to Tourian", DOOR_H, condition=L_DOOR),
    Split("Farming Room to Tourian", DOOR_H, condition=L_DOOR),
    Split("Frog Speedway to Tourian", DOOR_H, condition=L_DOOR),
    Split("Frog Save to Tourian", DOOR_H, condition=L_DOOR),
    Split("Business Center to Tourian", FADE_BLACK),
    Split("Norfair Elevator to Tourian", DOOR_H, condition=L_DOOR),
    Split("Tube to Tourian", DOOR_V2, condition=U_DOOR),
    Split("Main Street to Tourian", DOOR_H, condition=R_DOOR),
    Split("Fish Tank to Tourian", DOOR_V2, condition=U_DOOR),
    Split("Everest to Tourian", DOOR_V2, condition=U_DOOR),
    Split("Red Fish", DOOR_H, condition=L_DOOR),
    Split("Caterpillar Elevator", FADE_BLACK),
    Split("Red Brinstar Elevator", DOOR_V2, condition=U_DOOR),
    Split("Crateria Kihunter to Tourian", DOOR_H, condition=L_DOOR),
    Split("Landing Site to Tourian", DOOR_H, condition=L_DOOR),
    Split("Parlor to Tourian", DOOR_H, condition=L_DOOR),
    Split("Terminator to Tourian", DOOR_H, condition=L_DOOR),
    Split("Green Pirates to Tourian", DOOR_H, condition=R_DOOR),
    Split("Statues Hallway", DOOR_H, condition=R_DOOR),
    Split("G4", FADE_BLACK),
    Split("Tourian Elevator", DOOR_H, condition=L_DOOR),
    Split("Metroid 1", DOOR_H, condition=L_DOOR),
    Split("Metroid 2", DOOR_H, condition=R_DOOR),
    Split("Metroid 3", DOOR_H, condition=R_DOOR),
    Split("Metroid 4", DOOR_V, condition=D_DOOR),
    Split("Blue Hopper", DOOR_H, condition=L_DOOR),
    Split("Dust Torizo", DOOR_H, condition=L_DOOR),
    Split("Baby Skip", FADE_BLACK),
    Split("Seaweed", DOOR_H, condition=R_DOOR),
    Split("Tourian Eye Door", DOOR_H, condition=R_DOOR),
    Split("Rinka Shaft", DOOR_H, condition=L_DOOR),
    Split("Mother Brain", FADE_BLACK),
    Split("Tourian Escape 1", DOOR_V, condition=D_DOOR),
    Split("Tourian Escape 2", DOOR_H, condition=R_DOOR),
    Split("Tourian Escape 3", DOOR_H, condition=R_DOOR),
    Split("Tourian Escape 4", DOOR_H, condition=R_DOOR),
    Split("Climb Spark Escape", DOOR_V, condition=U_DOOR),
    Split("Save The Animals", DOOR_H, condition=R_DOOR),
    Split("Time", VARIA_FACE)  # get a better frame


]
