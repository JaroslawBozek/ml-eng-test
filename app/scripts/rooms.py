import numpy as np
from pdf2image import convert_from_path
import cv2
import pandas as pd
import json

class Rooms():
    def __init__(self, temp_file_path):
    
        self.filename = temp_file_path.split('/')[-1][:-4]
        self.im = None
        if temp_file_path.endswith('.pdf'):
            pages = convert_from_path(temp_file_path, grayscale = True)
            self.im = np.array(pages[0])
        elif temp_file_path.endswith('.png') or temp_file_path.endswith('.jpg'):
            self.im = cv2.imread(temp_file_path, 0)
            
            
        self.im_x, self.im_y = self.im.shape
        self.im2 = np.zeros((self.im_x, self.im_y), np.uint8)
        self.im2.fill(255)
        
    def imshow(self):
        im3 = cv2.resize(self.im, (0,0), fx=0.25, fy=0.25)
        cv2.imshow('im3', im3)

    def prepare_json(self):
    
        room1 = {
            "roomId": "room1",
            "vertices": [
            { "x": None, "y": None},
            { "x": None, "y": None},
            { "x": None, "y": None},
            { "x": None, "y": None}
            ]
        }
        room2 = {
            "roomId": "room2",
            "vertices": [
            { "x": None, "y": None},
            { "x": None, "y": None},
            { "x": None, "y": None},
            { "x": None, "y": None}
            ]
        }
        rooms = [room1, room2]
        detectionResults = {
            "rooms": rooms
        }
        data_out = {
            "type": "rooms",
            "imageId": self.filename,
            "detectionResults": detectionResults
        }
        
        return data_out
    def detect_rooms(self):
        
        
        
        data_out = self.prepare_json()
        return data_out
    
def main(temp_file_path):

    rooms = Rooms(temp_file_path)
    data_out = rooms.detect_rooms()
    
    return(data_out)

        
