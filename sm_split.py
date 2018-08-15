import cv2
import numpy as np
import matplotlib
#matplotlib.use("Agg")
from matplotlib import pyplot as plt
import cProfile
import pygame
import mss
import time
import route
from win32 import win32gui  ## pywinauto???

SM_HUD_HEIGHT = 31*4  # when scaled 4x31
CROP_BOTTOM = 20*4  # remove slice where input/info are drawn
SM_SIZE = (1196, 896)  # 4*(16*16*7/6, 16*14) when scaled 4x in 4:3 from 8:7
SCAN_SIZE = (16*16, 16*14 - SM_HUD_HEIGHT//4 - CROP_BOTTOM//4)
scale = (SCAN_SIZE[0]/SM_SIZE[0], SCAN_SIZE[1]/(SM_SIZE[1] - SM_HUD_HEIGHT))
color = {"found": (198, 44, 90),
         "not_found": (154, 112, 218)}
transition_time = {"vertical": 58, "horizontal": 65}


def track_window_position(monitor_dict):
    hwnd = monitor_dict["hwnd"]
    rw = win32gui.GetWindowRect(hwnd)
    rc = win32gui.GetClientRect(hwnd)
    window_width = rw[2] - rw[0]
    border_width = window_width - rc[2]  # the client's right side is before the end of the window
    border_width -= 9  # ???
    window_height = rw[3] - rw[1]
    border_height = window_height - rc[3]
    border_height -= 8  # ?
    # border_height =
    monitor_dict["left"] = rw[0] + border_width
    monitor_dict["top"] = rw[1] + border_height + SM_HUD_HEIGHT
    # monitor_dict["width"] = rc[2] + 1
    monitor_dict["width"] = SM_SIZE[0]
    # monitor_dict["height"] = rc[3] - SM_HUD_HEIGHT
    monitor_dict["height"] = SM_SIZE[1] - SM_HUD_HEIGHT - CROP_BOTTOM


def callback(hwnd, monitor_dict):
    if win32gui.GetWindowText(hwnd) == "Snes9X v1.54.1 for Windows":
        monitor_dict["hwnd"] = hwnd
        track_window_position(monitor_dict)

monitor = {}
win32gui.EnumWindows(callback, monitor)
if not monitor:
    raise EOFError("couldn't find Snes9x")

#TODO: define a class for templates to check for and preload them
#template = cv2.imread("d/door_h.png", 0)
#th, tw = template.shape

"""img = cv2.imread("d/7.png", 0)  # (flag 0 returns a greyscale image) img is a numpy array
img2 = img.copy()  # ?
template = cv2.imread("d/door_h.png", 0)
h, w = template.shape
methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
            'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']"""


#https://stackoverflow.com/questions/35097837/capture-video-data-from-screen-in-python
#https://stackoverflow.com/questions/24129253/screen-capture-with-opencv-and-python-2-7
#https://pypi.org/project/pyscreenshot/
#mss  <----
#https://stackoverflow.com/questions/7142342/get-window-position-size-with-python
#-> enumWindows

def time_str(f_sec):
    h = str(int(f_sec//3600))
    m = int((f_sec%3600)//60)
    if m < 10:
        m = "0" + str(m)
    else:
        m = str(m)
    s = int(f_sec%60)
    if s < 10:
        s = "0" + str(s)
    else:
        s = str(s)
    c = int((f_sec%1)*100)
    if c < 10:
        c = "0" + str(c)
    else:
        c = str(c)
    return h + ":" + m + ":" + s + "." + c


def draw(surface, ox, oy, current_time, route, split_id):
    number_of_line = 7
    surface.fill((0, 0, 0))
    x = ox
    y = oy
    if split_id <= number_of_line:
        first_id = 0
    elif split_id >= len(route) - number_of_line:
        first_id = len(route) - number_of_line - 1
    else:
        first_id = split_id - number_of_line
    for s in route[first_id:]:
        surf = font.render(s.name, True, color["not_found"])
        surface.blit(surf, (x, y))
        if s.time >= 0:
            surf = font.render(time_str(s.time), True, color["not_found"])
            surface.blit(surf, (surface.get_width() - font_spacing - surf.get_width(), y))
        else:
            surf = font.render(time_str(current_time), True, color["not_found"])
            surface.blit(surf, (surface.get_width() - font_spacing - surf.get_width(), y))
            break
        y += font_spacing + surf.get_height()
    pygame.display.flip()

"""
def template_test(frame):  #, template):
    #for m in methods:
    method = cv2.TM_CCORR_NORMED
    res = cv2.matchTemplate(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), template, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    #if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
    #    top_left = min_loc
    #else:

    top_left = max_loc
    bottom_right = (top_left[0] + tw, top_left[1] + th)
    print(min_val, max_val)

    cv2.rectangle(img, top_left, bottom_right, 255, 2)

    #plt.subplot(121), plt.imshow(res, cmap='gray')
    #plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
    plt.subplot(122), plt.imshow(img, cmap='gray')
    plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
    #plt.suptitle(m + " " + str(min_val) + ", " + str(max_val))

    plt.show()
    return max_val"""

pygame.init()
font = pygame.font.SysFont("fangsong", 24)
font_spacing = 8
#screen = pygame.display.set_mode([int(scale[0]*monitor["width"]), int(scale[1]*monitor["height"])])  #, pygame.NOFRAME)

"""
screen = pygame.display.set_mode([SCAN_SIZE[0], SCAN_SIZE[1]])  #, pygame.NOFRAME)
screen.fill((0, 0, 0))
with mss.mss() as sct:
    #sct.monitors[1]
    img = np.array(sct.grab(monitor))
img = cv2.resize(img, SCAN_SIZE)
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img = np.rot90(img)
img = np.flip(img, 0)
pygame.surfarray.blit_array(screen, img)
pygame.display.flip()"""

screen = pygame.display.set_mode((256 + 128, 512))
screen.fill(color["not_found"])

running = True
run_finish = False
split_id = 0
#test = ColorMatch((0, 0, 0))
start_time = None
sleep_time = 0
with mss.mss() as sct:
    while running:
        if not win32gui.IsWindowEnabled(monitor["hwnd"]):
            break  # tracked window closed
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    if split_id > 0:
                        if split_id == 1:
                            start_time = None
                        if run_finish:
                            run_finish = False
                            route.route[split_id].reset()
                        split_id -= 1
                        route.route[split_id].reset()
                        sleep_time = 0
                        print("new_split ", split_id)
                elif event.key == pygame.K_DOWN:
                    if start_time:
                        if split_id < len(route.route):
                            route.route[split_id].skip()
                            split_id += 1

        if sleep_time:
            t = min(0.016, sleep_time - time.perf_counter())
            if t > 0:
                time.sleep(t)
                if time.perf_counter() >= sleep_time:
                    sleep_time = 0
                else:
                    if start_time:
                        current_time = time.perf_counter() - start_time
                    else:
                        current_time = 0
                    draw(screen, font_spacing, font_spacing, current_time, route.route, split_id)
                    continue
            else:
                sleep_time = 0
        if win32gui.IsIconic(monitor["hwnd"]):
            time.sleep(0.05)
            continue
        #last_time = time.time()
        track_window_position(monitor)
        img = np.array(sct.grab(monitor))
        img = cv2.resize(img, SCAN_SIZE)
        #test.frame_test(img)
        if not run_finish:
            current_split = route.route[split_id]
            match_value = current_split.event.frame_test(img)
            if match_value:
                if not start_time:
                    start_time = time.perf_counter()
                    current_split.time = 0
                else:
                    current_split.time = time.perf_counter() - start_time
                if split_id < len(route.route):
                    split_id += 1
                else:
                    run_finish = True
                sleep_time = current_split.time + start_time + current_split.sleep_time
        #print(match_value)
        if start_time:
            current_time = time.perf_counter() - start_time
        else:
            current_time = 0
        draw(screen, font_spacing, font_spacing, current_time, route.route, split_id)


pygame.quit()

if __name__ == "__main__":
    pass
    #import timeit
    #print(timeit.timeit("test_func()", setup="from __main__ import test_func", number=1000))   ## tm_ccorr
    #main()
    #cProfile.run("test_func()")
