import sys
import numpy as np
import cv2

test_img_fn = sys.argv[1]

cascade_fn = sys.argv[2]

cascade = cv2.CascadeClassifier(cascade_fn)

img = cv2.imread(test_img_fn)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

detected_objs = cascade.detectMultiScale(gray, 1.3, 5)

for (x,y,w,h) in detected_objs:
    cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
    roi_gray = gray[y:y+h, x:x+w]
    roi_color = img[y:y+h, x:x+w]

cv2.imshow('img', img)
cv2.waitKey(0)
cv2.destroyAllWindows()
