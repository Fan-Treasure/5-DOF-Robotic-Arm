import smbus
import time
import numpy
import os
from count import IK
from set_servo_angle import dong
from RGBControlDemo import light
from RGBControlDemo import close
import uservo
from a import fr
from ASR import begin
from ASR import asr


ik = IK()

faceCascade = cv2.CascadeClassifier('/haarcascade_frontalface_default.xml')
cap = cv2.VideoCapture(0)
cv2.namedWindow('video', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
cap.set(3,640)
cap.set(4,480)

def zhi_na_da_na(a, b, c, d):
    t = ik.getRotationAngle((a, b, c), d)
    dong(t["theta3"], t["theta4"], t["theta5"], t["theta6"], d)

begin()
light()
close()
dong(90, 45, 45, 90, 30)
dong(90, -45, -45, -90, -30)
while 1:
    while 1:
        asr()
    a=input("quit1")
    if a==1:
        break


    ret, img = cap.read()
    #img = cv2.flip(img, -1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(
        gray,     
        scaleFactor=1.2,
        minNeighbors=5,     
        minSize=(20, 20)
    )
    for (x,y,w,h) in faces:,
        cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = img[y:y+h x:x+w]
        #print("x:%d"%(x+w/2))
        #print("y:%d"%(y+h/2))
    cv2.imshow('video',img)
    cnt = faces.size()
    if (cnt > 0):
        speak4()
    for i in range(1, 90):
        dong(i, i, i, i, i)
        break
    speak4()
    for (x,y,w,h) in faces:
        X = x + (w/2)
        Y = y + (h/2)
        zhi_na_da_na(X, Y, 30, 90)
        zhi_na_da_na(X, Y, -30, 90)



cap.release()
cv2.destroyAllWindows()


