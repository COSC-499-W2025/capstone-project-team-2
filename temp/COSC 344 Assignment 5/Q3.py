import matplotlib.pyplot as plt
import cv2 as cv
import numpy as np
from scipy import ndimage

img = cv.imread("bwimage.png", cv.IMREAD_GRAYSCALE) # read image
_, bw = cv.threshold(img, 127, 1, cv.THRESH_BINARY) # binarize image to 0s and 1s

labels, num = ndimage.label(bw)
labeled_gray = (labels * (255 / labels.max())).astype(np.uint8) # label image in grayscale

scaled = (labels.astype(np.float32) / labels.max() * 255).astype(np.uint8) # scale labels to 0-255

colored = cv.applyColorMap(scaled, cv.COLORMAP_JET) # apply colormap
colored = cv.cvtColor(colored, cv.COLOR_BGR2RGB) # convert BGR to RGB

colored[labels == 0] = [255, 255, 255] # set background to white

cog = []
for i in range(1, num + 1):
    ys, xs = np.where(labels == i)
    cy = int(ys.mean())
    cx = int(xs.mean())
    cog.append((cx, cy)) # center of gravity coordinates
    
marked = colored.copy() 

for cx,cy in cog:
    cv.drawMarker(marked, (cx, cy), (255, 0, 0), markerType=cv.MARKER_CROSS, markerSize=10, thickness=1) # mark centroids
    
plt.figure(figsize=(8, 8))

plt.subplot(2, 2, 1)
plt.imshow(img, cmap='gray')
plt.title("Original Image")
plt.axis("off")

plt.subplot(2, 2, 2)
plt.imshow(labeled_gray, cmap='gray')
plt.title("Labeled Image")
plt.axis("off")

plt.subplot(2, 2, 3)
plt.imshow(colored)
plt.title("Color Labeled Image")
plt.axis("off")

plt.subplot(2, 2, 4)
plt.imshow(marked)
plt.title("Centroid Annotation")
plt.axis("off")

plt.show()
