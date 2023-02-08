# -*- coding: utf-8 -*-
"""
Originally Created on Tue Jun  8 18:37:18 2021

@author: Professor https://www.linkedin.com/in/olufemi-victor-tolulope/
"""

import json
import tempfile
# first import the needed fastapi libraries
from importlib.metadata import files

# Bring in OpenCV to handle the post detection Aesthetics
import cv2
# basic necessities 
import numpy as np
#import requests to make the post
import requests
# Unlike Flask, Fastapi needs uvicorn to handle server stuffs
import uvicorn
from cv2 import FONT_HERSHEY_PLAIN, putText, rectangle
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image

#setup the URL & other things i need to help interprete response.
url = "https://agrobotfarms-crop-analysis-v1.azurewebsites.net/predict" # we could hide this in the environment but there's no fuss
_MARGIN = 10  # pixels
_ROW_SIZE = 10  # pixels
_FONT_SIZE = 1
_FONT_THICKNESS = 1
_TEXT_COLOR = (0, 0, 255)  # red


# import pathlib, i needed this during the test on my local pc, we can comment it out for production.
import pathlib

# quicly set poxipath for my testing.
#temp = pathlib.PosixPath
#pathlib.PosixPath = pathlib.WindowsPath



# start the backend, an intersting mix of Fastapi and Jinja 2.
app = FastAPI() # call fastapi
app.mount("/static", StaticFiles(directory="static"), name="static") #we'll need fastapi to locate the static folder, that's where important stuff is.
templates = Jinja2Templates(directory="templates") # Jinja 2 needs to know where the HTML code is


# Homepage Routing

@app.get('/', response_class = HTMLResponse) # this means when i call the home page, by default it loads the home.
async def index(request:Request):
    #return ("This guy works well")
    return templates.TemplateResponse("index.html", {"request": request, "user_image":"/static/web_images/broken-image.png"})


# Time to infer from the model
@app.post('/predict',response_class = HTMLResponse)
async def predict(request:Request, file:UploadFile = File(...), use_case: str = Form(...), threshold: str = Form(...)): #Get important details from Header
    if file.content_type[:5] == "image": # confirm that uploaded file is an image
        print("##########################")

        print("##############################")
        file_suffix = "".join(file.filename.partition(".")[1:]) # split filename by the "."

        with tempfile.NamedTemporaryFile(mode="w+b", suffix=file_suffix, delete=False) as file_on_disk: # Pick uploaded temporary file from RAM
            file_contents = await file.read() #read the content
            file_on_disk.write(file_contents) #rewrite the image on disk - This will be depreciated later, not efficient at all.
            temp_image_path = file_on_disk.name # get the filename from disk
            print(temp_image_path) #See it for yourself
            file_on_disk.close() #close the file writer

# Converting image to an Array for OpenCV to draw on
        im = Image.open(temp_image_path).convert('RGB') #convert in case we have a wierd number of channels in the image.
        im.thumbnail((512, 512), Image.ANTIALIAS) # Resize the image
        image = np.asarray(im) # let numpy convert to an array, this is for OpenCV to draw on


########################################################################### POSTING ########################################################################

        payload={} # the Payload
        files = {'image': open(temp_image_path, 'rb')} # the File itself
        headers = {                                     # the headers
        'threshold': (threshold),
        'use_case': use_case
        }

        response = requests.request("POST", url, headers=headers, data=payload, files=files) #request makes the post
        print(response.text) # I want to see response during development

        list_of_bounding_boxes = json.loads(response.text)["bounding_box_details"] #load response as json format

############################################# OpenCV draws on Image #################################################################################

        for bounding_box in list_of_bounding_boxes: #pick each bounding box received in the response
            # Draw bounding_box
            left, right, top, bottom,class_name,probability = bounding_box
            start_point = (left, top)
            end_point = (right, bottom)
            rectangle(image, start_point, end_point, _TEXT_COLOR, 3) # draw the rectangle

            # Draw label and score
            result_text = class_name + ' (' + str(probability) + ')'
            text_location = (_MARGIN + left,
                            _MARGIN + _ROW_SIZE + top)
            putText(image, result_text, text_location, FONT_HERSHEY_PLAIN,
                        _FONT_SIZE, _TEXT_COLOR, _FONT_THICKNESS)
        image_path = "static/tmp/temporary.jpg"
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        cv2.imwrite(image_path, image) #i'll have to save the image temporarily to display in my HTML code
            
        
        return templates.TemplateResponse("predict.html", {"request": request,"prediction_text": "We found {} in your image".format(class_name), "resultText": "{}".format(class_name), "user_image":image_path}) #Jae(frontend): I added a result text i.e 'class_name' and new template is predict.html 
    else:
        return templates.TemplateResponse('predict.html', {"request": request,"prediction_text":"I'm not sure you've selected any picture yet, i didn't find anything.", "user_image":"/static/web_images/broken-image.png"}) #new template is predict.html
        
# LET UVICORN RUN THE WHOLE THING.

if __name__ == '__main__':
    uvicorn.run(app)