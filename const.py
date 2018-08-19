SM_HUD_HEIGHT = 31*4  # when scaled 4x31
CROP_BOTTOM = 20*4  # remove slice where input/info are drawn
SM_SIZE = (1196, 896)  # 4*(16*16*7/6, 16*14) when scaled 4x in 4:3 from 8:7
SCAN_SIZE = (16*16, 16*14 - SM_HUD_HEIGHT//4 - CROP_BOTTOM//4)
scale = (SCAN_SIZE[0]/SM_SIZE[0], SCAN_SIZE[1]/(SM_SIZE[1] - SM_HUD_HEIGHT))
color = {"found": (198, 44, 90),
         "not_found": (154, 112, 218)}
transition_time = {"vertical": 58, "horizontal": 65}
FRAME_TIME = 1/60  # snes : 60.09 , snes9x : 59.94