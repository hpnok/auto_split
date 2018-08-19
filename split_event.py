import cv2
import numpy as np
import pygame


class SplitEvent(object):
    debug_value = 0

    def __init__(self):
        pass

    def frame_test(self, frame):
        raise NotImplementedError


class TemplateMatch(SplitEvent):
    #horizontal, vertical, face
    #TODO: add time correction?
    def __init__(self, file_name, threshold=0.98):
        super().__init__()
        self.image = cv2.imread(file_name, 0)
        self.threshold = threshold

    def frame_test(self, frame):
        method = cv2.TM_CCORR_NORMED
        res = cv2.matchTemplate(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), self.image, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        #print(max_val)
        SplitEvent.debug_value = max_val
        if max_val > self.threshold:
            return pygame.Rect(max_loc, self.image.shape[::-1])  # h, w = template.shape
        return None


class ColorMatch(SplitEvent):
    #TODO: add tolerance?
    def __init__(self, bgr_color_tuple):
        super().__init__()
        self.color = bgr_color_tuple

    def frame_test(self, frame):
        h, w = frame.shape[:2]
        area = (w*h)
        pix_sum = cv2.sumElems(frame)
        SplitEvent.debug_value = [i//area for i in pix_sum[:3]]
        #print(pix_sum[0]//area, pix_sum[1]//area, pix_sum[2]//area)
        return self.color == tuple(c//area for c in pix_sum[:3])
