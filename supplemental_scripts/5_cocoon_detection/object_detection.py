import cv2
import numpy as np
import argparse
import sys
import math
import warnings

parser = argparse.ArgumentParser(description='Detect mason bee cocoons and calculate width, length and surface area')
parser.add_argument('in_image', help='path for input image')
parser.add_argument('out_image', help='path for output image')
parser.parse_args()

img_path = sys.argv[1]
img_out = sys.argv[2]

# Set pixel intensity threshold (everything below this value is detected as part of some form of contour)
# Increase to detect more contours, decrease to be more conservative
THRESHOLD = 180
#print("Using threshold value: " + str(THRESHOLD))

# Leftmost and rightmost part on the horizontal axis to disregard for detecting contours (0.1 = 10%).
HORIZONTAL_BORDER_CUTOFF = 0.1

#Correct detected contours through a calculated convex hull
USE_CONVEX_HULL = True

#Print average pixel intensity of central circle to Std. Err. 
#to standardise measurements for cameras that can not fix the ISO value 
#Cocoon measurments Oct 2022: Threshold = 150, Average pixel intensity = 230
PRINT_CIRCLE_PX_INTENSITY = True

# reading image
img = cv2.imread(img_path)

# converting image into grayscale image
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#blurred = cv2.GaussianBlur(gray, (3, 3), 0)

# setting threshold of gray image
_, threshold = cv2.threshold(gray, THRESHOLD, 255, cv2.THRESH_BINARY)

# using a findContours() function
contours, _ = cv2.findContours(
	threshold, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

right_bound = img.shape[1] - (img.shape[1] * HORIZONTAL_BORDER_CUTOFF)
left_bound = img.shape[1] - (img.shape[1] * (1 - HORIZONTAL_BORDER_CUTOFF))

cocoon_contours = []
px_per_mm = float("inf")

img_area = abs(img.shape[0] * img.shape[1])
for contour in contours:
	rect = cv2.minAreaRect(contour)
	area = cv2.contourArea(contour, True)
	if rect[0][0] > rect[0][1]:
		if rect[0][0] > right_bound or rect[0][0] < left_bound:
			continue
	else:
		if rect[0][1] > right_bound or rect[0][1] < left_bound:
			continue
	if abs(area) > 0.3 * img_area and abs(area) < 0.8 * img_area:
		circle_contour = contour
		if rect[1][0] < rect[1][1]:
			circle_diameter = rect[1][0]
		else:
			circle_diameter = rect[1][1]
		px_per_mm = circle_diameter / 120

		#calculate average pixel intensity of circle contour
		perimeter = cv2.arcLength(contour, True)
		epsilon = 0.002 * perimeter
		approx = cv2.approxPolyDP(contour, epsilon, True)
		blank_image = np.zeros(gray.shape, np.uint8)
		cv2.drawContours(blank_image, [approx], -1, (255, 255, 255), -1)
		blank_image2 = cv2.resize(blank_image, (blank_image.shape[1] // 4, blank_image.shape[0] // 4))
		mask_contour = blank_image == 255
		intensity = np.mean(gray[mask_contour])
		if PRINT_CIRCLE_PX_INTENSITY:
			sys.stderr.write("File " + img_path + " : Avg. px. intensity of circle contour: " + str(intensity) + "\n")
	elif area > img.shape[1] * 2 and area < img.shape[1] * 30:
		if USE_CONVEX_HULL :
			cocoon_contours.append(cv2.convexHull(contour))
		else:
			cocoon_contours.append(contour)

cocoon_contours = tuple(cocoon_contours)

sys.stderr.write("File " + img_path + " : Pix/mm = " + str(px_per_mm) + "\n")

if len(cocoon_contours) != 10:
	sys.stderr.write("File " + img_path + " : WARNING: " + str(len(cocoon_contours)) + " cocoons detected instead of 10!\n")
if math.isinf(px_per_mm):
	sys.stderr.write("File " + img_path + " : WARNING: No border circle detected\n")
else:
	cv2.drawContours(img, [circle_contour], 0, (0, 255, 0), 5)

i = 1
for contour in cocoon_contours:

	rect = cv2.minAreaRect(contour)

	if rect[1][0] < rect[1][1]:
		print(i, rect[1][0] / px_per_mm, rect[1][1] / px_per_mm, 
		cv2.contourArea(contour, True) / px_per_mm**2, sep = "\t")
	else:
		print(i, rect[1][1] / px_per_mm, rect[1][0] / px_per_mm, 
		cv2.contourArea(contour, True) / px_per_mm**2, sep = "\t")
	
	box = cv2.boxPoints(rect)
	box = np.int0(box)
	cv2.drawContours(img, [box], 0, (255, 0, 0), 5)

	# cv2.approxPloyDP() function to approximate the shape
	approx = cv2.approxPolyDP(
		contour, 0.01 * cv2.arcLength(contour, True), True)
	
	# using drawContours() function
	cv2.drawContours(img, [contour], 0, (0, 0, 255), 5)

	# finding center point of shape
	M = cv2.moments(contour)
	if M['m00'] != 0.0:
		x = int(M['m10']/M['m00'])
		y = int(M['m01']/M['m00'])

	# putting shape name at center of each shape
	cv2.putText(img, 'Cocoon_' + str(i), (x, y),
				cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 0), 5)
	i += 1

# displaying the image after drawing contours

#img = cv2.resize(img, (img.shape[1] // 4, img.shape[0] // 4))

cv2.imwrite(img_out, img)
