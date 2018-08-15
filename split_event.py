import cv2
import numpy as np


class SplitEvent(object):
    def __init__(self):
        pass

    def frame_test(self, frame):
        raise NotImplementedError


class TemplateMatch(SplitEvent):
    #horizontal, vertical, face
    #TODO: add time correction?
    def __init__(self, file_name):
        super().__init__()
        self.image = cv2.imread(file_name, 0)

    def frame_test(self, frame):
        method = cv2.TM_CCORR_NORMED
        res = cv2.matchTemplate(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), self.image, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        #print(max_val)
        if max_val > 0.98:
            return True
        return False


class ColorMatch(SplitEvent):
    #TODO: add tolerance?
    def __init__(self, bgr_color_tuple):
        super().__init__()
        self.color = bgr_color_tuple

    def frame_test(self, frame):
        h, w = frame.shape[:2]
        area = (w*h)
        pix_sum = cv2.sumElems(frame)
        #print(pix_sum[0]//area, pix_sum[1]//area, pix_sum[2]//area)
        i = 0
        for c in pix_sum[:3]:
            if c//area != self.color[i]:
                return False
        return True
