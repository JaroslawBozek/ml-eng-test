import numpy as np
from img2table.document import Image
from img2table.ocr import TesseractOCR
from pdf2image import convert_from_path
import cv2
import pandas as pd
import json

class Table():
    def __init__(self, temp_file_path):
    
        self.filename = temp_file_path.split('/')[-1][:-4]
        self.im = None
        if temp_file_path.endswith('.pdf'):
            pages = convert_from_path(temp_file_path, grayscale = True)
            self.im = np.array(pages[0])
        if temp_file_path.endswith('.png') or temp_file_path.endswith('.jpg'):
            self.im = cv2.imread(temp_file_path, 0)
        
        self.tables_corners = {} #x,y,w,h

    def find_tables(self):
    
        #find contours
        ret, thresh = cv2.threshold(self.im, 127, 255, 0)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        #get contour areas
        areas = self.get_areas(contours)
        #evaluate the contours by analyzing their hierarchy, areas and locations
        scores = self.get_scores(contours, hierarchy, areas)
        #analyze the scores and extract tables' corners locations
        tables = self.get_tables_corners(contours, scores)
        
        #visualize
        
    def get_areas(self, contours):
    
        areas = {}
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            areas[i] = area
        return areas
    
    def get_scores(self, contours, hierarchy, areas):
    
        scores = {}
        for area in areas:
            scores[area] = 0
        
        for area in areas:

            child_vertices = cv2.approxPolyDP(contours[area], 0.005 * cv2.arcLength(contours[area], True), True)
            parent_id = hierarchy[0][area][3]
            parent_vertices = cv2.approxPolyDP(contours[parent_id], 0.005 * cv2.arcLength(contours[parent_id], True), True)
            
            #check if the contour is quadrangular (usually table or cell)            
            if len(child_vertices) == 4 and len(parent_vertices) == 4:
                if areas[area] <= areas[parent_id] * 0.5:
                    #parents receive points depending how close their children are to them and how big they are
                    c_x,c_y,c_w,c_h = cv2.boundingRect(contours[area])
                    p_x,p_y,p_w,p_h = cv2.boundingRect(contours[parent_id])
                    distances = [abs(c_x-p_x), abs(c_y-p_y), abs(c_x+c_w-p_x-p_w), abs(c_y+c_h-p_y-p_h)]
                    min_dist = min(distances)
                
                    score = 0
                    if min_dist <= 0:
                        min_dist = 1

                    score = areas[area]/pow(min_dist,5)
                    scores[parent_id] += score
                   
        return scores
        
    def get_tables_corners(self, contours, scores):
    
        best_i = 0
        best_quotient = 1
        last_score = -1
        scores = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))
        #contours with high scores(tables) get separated from these with low scores
        for i, score in enumerate(scores):
        
            if scores[score] <= 1:
                break
                
            quotient = last_score/scores[score]
            
            if quotient >= best_quotient:
                best_quotient = quotient
                best_i = i
                
            last_score = scores[score]
    
        #get tables' corners
        for score_id, score in list(scores.items())[:best_i]:
        
            x,y,w,h = cv2.boundingRect(contours[score_id])
            self.tables_corners[score_id] = [x,y,w,h]
            
            
            
            
    def read_tables(self):
        
        #Get raw output from img2table
        extracted_tables = self.extract_raw_data()
        #Process the data from img2table - the headers are often separated from data and need to be merged by analyzing their locations on the sheet
        data_merged = self.merge_tables(extracted_tables)
        #Prepare the dictionary ready to be jsonified
        data_out = self.prepare_json(data_merged)
        
        return data_out
        
    def extract_raw_data(self):
    
        extracted_tables = {}
        for table_corners in self.tables_corners:
            
            x,y,w,h = self.tables_corners[table_corners]
            img_table = self.im[y:y+h, x:x+w]
            cv2.imwrite("temp.png", img_table)
            ocr = TesseractOCR(n_threads=8, lang="eng")
            doc = Image("temp.png")
            
            extracted_table = doc.extract_tables(ocr=ocr,
                                      implicit_rows=False,
                                      borderless_tables=False,
                                      min_confidence=50)

            extracted_tables[table_corners] = extracted_table
            
        return extracted_tables
        
    def merge_tables(self, extracted_tables):
    
        tableFeatures = {}
        
        #Table contours get sorted in order to be read from top->bottom and left->right
        sorted_corners = dict(sorted(self.tables_corners.items(), key=lambda item: (item[1][0], item[1][1], item[1][2], item[1][3])))
        
        data_merged = []
        tableName = 'placeholder'
        data = []
        
        #data from previous row
        last_col_count = 0
        last_cell_borders = [1]
        
        is_header = True
        is_tableName = True
        
        #extracted data
        columns = []
        
        for contour_id in sorted_corners:
            
            table_contents = extracted_tables[contour_id]
            if len(table_contents) > 0:
                for id_row, row in enumerate(table_contents[0].content.values()):
                    col_count = 1
                    cell_borders = [1]
                    last_cell = None
                    
                    #Analyze row contents
                    for id_col, cell in enumerate(row):
                        x1 = cell.bbox.x1
                        y1 = cell.bbox.y1
                        x2 = cell.bbox.x2
                        y2 = cell.bbox.y2
                        value = cell.value
                        
                            
                        if last_cell != cell.bbox: #Wider cells are saved multiple times but should be counted as one
                            col_count += 1
                        elif is_header == False: #If cells start repeating themselves (are wider than in the last row), it means that the new header is found and should be counted as another table
                                      
                            last_col_count = 0
                            last_cell_borders = [1]
                            data_merged.append([tableName, data])
                            data = []
                            is_header = True
                            is_tableName = True

                        if is_tableName == True:
                            tableName = value
                            
                        cell_borders.append(x2)
                            
                        last_cell = cell.bbox
                        
                    #If column count starts repeating itself, the header has ended
                    if last_col_count >= col_count:
                        is_header = False
                    
                    #If the header hasn't ended, keep updating the columns count
                    if is_header == True:
                        last_col_count = col_count
                        last_cell_borders = cell_borders

                    #Copy row contents to output
                    row_data = []
                    
                    it_row = 0
                    l_cell = last_cell_borders[0]
                    r_cell = last_cell_borders[1]
                    
                    #The header and data cells can be offset from each other, so the cells that overlap the largest part are assigned to each other
                    for i in range(len(last_cell_borders)-1):
                        
                        if last_cell_borders[i+1] != r_cell:
                            l_cell = last_cell_borders[i]
                            r_cell = last_cell_borders[i+1]    
                         
                        col_score = {}
                            
                        for col_id, col_data in enumerate(row):
                            l_bbox = col_data.bbox.x1
                            r_bbox = col_data.bbox.x2
                            value = col_data.value
                            left_common = max(l_bbox, l_cell)
                            right_common = min(r_bbox, r_cell)
                            score = right_common - left_common
                            col_score[value] = score

                        best_value = max(col_score, key=col_score.get)

                        if col_score[best_value] > 0:
                            row_data.append(best_value)
                        else:
                            row_data.append(None)

                        
                    if is_header == True:
                        row_data = ['header',row_data]
                    else:
                        row_data = ['data',row_data]
                    
                    if is_tableName == False:
                        data.append(row_data)
                        
                    is_tableName = False
            
        data_merged.append([tableName, data])
        
        return data_merged
            

    def prepare_json(self, data_merged):
        
        #Data is unpacked and sorted because img2table reads the table by rows instead of columns
        detection_results = []
        for table in data_merged:
            tableName = table[0]
            rows = table[1]
            col_header = []
            col_rows = []
            
            for i, row in enumerate(rows):
                row_type = row[0]
                data = row[1]
                
                if row_type == "header":
                    col_header.append(data)
                if row_type == "data":
                    col_rows.append(data)
            
            
            if len(col_header) <= 0 or len(col_rows) <= 0:
                continue
            rotated_col_header = [[col[i] for col in col_header] for i in range(len(col_header[0]))]
            rotated_col_rows = [[col[i] for col in col_rows] for i in range(len(col_rows[0]))]
            if len(rotated_col_header) != len(rotated_col_rows):
                continue
            
            columns = []
            for i in range(len(rotated_col_header)):
                header = rotated_col_header[i]
                rows = rotated_col_rows[i]
                column = {
                    "header": header,
                    "rows": rows
                }
                columns.append(column)
                
            detection_result = {
                "tableName": tableName,
                "columns": columns
            }
            
            detection_results.append(detection_result)
            
        data_out = {
            "type": "tables",
            "imageId": self.filename,
            "detectionResults": detection_results
        }
        
        return data_out


def main(temp_file_path):

    table = Table(temp_file_path)
    table.find_tables()
    data_out = table.read_tables()

    return data_out

