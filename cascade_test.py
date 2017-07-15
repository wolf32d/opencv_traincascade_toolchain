import sys
import time
import numpy as np
import cv2


cascade_fn = sys.argv[1]
test_img_fns = sys.argv[2:]

cascade = cv2.CascadeClassifier(cascade_fn)


for test_img_fn in test_img_fns:




    img = cv2.imread(test_img_fn)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    print "haar search"
    detected_objs =  cascade.detectMultiScale(gray,
                                              minSize=(0, 0), flags=cv2.cv.CV_HAAR_SCALE_IMAGE)
  #detected_objs = cascade.detectMultiScale(gray, 1.25, 5)

    for (x,y,w,h) in detected_objs:
        cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = img[y:y+h, x:x+w]


    """gray_blur = cv2.medianBlur(gray,9)

    print "hough gradient search"
    tic = time.time()
    circles = cv2.HoughCircles(gray_blur, method=cv2.cv.CV_HOUGH_GRADIENT, dp=10, minDist=30,
                               param1=50, param2=30, minRadius=0, maxRadius=0)

    toc = time.time() - tic
    print "took %.1f s" % toc
    circles = np.uint16(np.around(circles))
    for c in circles[0,:]:
        # draw the outer circle
        cv2.circle(img, (c[0],c[1]),c[2],(0,255,0), 2)
        # draw the center of the circle
        cv2.circle(img, (c[0],c[1]),2,(0,0,255), 3)
    """







    cv2.imshow(test_img_fn, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

