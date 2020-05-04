#!/usr/bin/env python
from datetime import datetime
from time import sleep
from grovepi import *
import picamera
import os
import tinys3
import yaml

# Connect the Grove Ultrasonic Ranger to digital port D4
# SIG,NC,VCC,GND

ultrasonic_ranger = 4
Relay_pin = 2

pinMode(Relay_pin,"OUTPUT")

# testing
with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# photo props
image_width = cfg['image_settings']['horizontal_res']
image_height = cfg['image_settings']['vertical_res']
file_extension = cfg['image_settings']['file_extension']
file_name = cfg['image_settings']['file_name']
photo_interval = cfg['image_settings']['photo_interval'] # Interval between photo (in seconds)
image_folder = cfg['image_settings']['folder_name']

# camera setup
camera = picamera.PiCamera()
camera.resolution = (image_width, image_height)
camera.awb_mode = cfg['image_settings']['awb_mode']

# verify image folder exists and create if it does not
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

# camera warm-up time
sleep(2)

while True:
    try:
        # Read distance value from Ultrasonic
        distant = ultrasonicRead(ultrasonic_ranger)
        print(distant,'cm')
        if distant <= 250:
            digitalWrite(Relay_pin,1)
            filepath = image_folder + '/' + file_name + file_extension
            if cfg['debug'] == True:
                print("Taking photo and saving to path")

            # Take Photo
            camera.capture(filepath)
    
            if cfg['debug'] == True:
                print("Uploading to s3")

            # Upload to S3
            conn = tinys3.Connection(cfg['s3']['access_key_id'], cfg['s3']['secret_access_key'])
            print("done connecting") 		
            f = open(filepath, 'rb')
            print("read file")		
            conn.upload(filepath, f, cfg['s3']['bucket_name'],
               headers={
               'x-amz-meta-cache-control': 'max-age=60'
               })

            # Cleanup
            if os.path.exists(filepath):
                os.remove(filepath)
		
        else:
            digitalWrite(Relay_pin,0)

        # sleep
        #sleep(photo_interval)

    except TypeError:
        print("Type Error")
    except IOError as err: 
        print("IO Error", err)



