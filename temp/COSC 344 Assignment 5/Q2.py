import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv

A = cv.imread("blob.png", cv.IMREAD_GRAYSCALE) # read image
_, A = cv.threshold(A, 127, 255, cv.THRESH_BINARY) # binarize image

B = cv.getStructuringElement(cv.MORPH_RECT, (3, 3)) # structuring element
B_hat = cv.flip(cv.flip(B, 0), 1) # reflection of B: flip both axes

# Equation 1: (A ⊖ B)^c = A^c ⊕ B̂

A_erosion = cv.erode(A, B, iterations=1) # A ⊖ B
A_erosion_comp = cv.bitwise_not(A_erosion) # (A ⊖ B)^c

A_comp = cv.bitwise_not(A) # A^c
A_dilation = cv.dilate(A_comp, B_hat, iterations=1) # A^c ⊕ B̂

# Equation 2: A ⊕ B = (A^c ⊖ B̂)^c

A_dilation_2 = cv.dilate(A, B, iterations=1) # A ⊕ B

A_erosion_2 = cv.erode(A_comp, B_hat, iterations=1)
A_erosion_2_comp = cv.bitwise_not(A_erosion_2) # (A^c ⊖ B̂)^c

plt.figure(figsize=(8, 8)) # plotting

plt.subplot(2, 2, 1)
plt.imshow(A_erosion_comp, cmap='gray')
plt.title("Complement of Eroded")
plt.axis("off")

plt.subplot(2, 2, 2)
plt.imshow(A_dilation, cmap='gray')
plt.title("Dilation of Complement")
plt.axis("off")

plt.subplot(2, 2, 3)
plt.imshow(A_dilation_2, cmap='gray')
plt.title("Dilation of Original")
plt.axis("off")

plt.subplot(2, 2, 4)
plt.imshow(A_erosion_2_comp, cmap='gray')
plt.title("Complement of Erosion of Complement")
plt.axis("off")

plt.show()




