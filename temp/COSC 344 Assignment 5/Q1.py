import numpy as np
import numpy.fft as fft
import matplotlib.pyplot as plt
import cv2 as cv

d = np.array([
    [0,   1/4, 0  ],
    [1/4, 0,   1/4],
    [0,   1/4, 0  ]
])

def freqz2(fn, N=64):
    """
    Compute the 2D frequency response of a spatial filter.
    Parameters:
        fn: 2D array
            The spatial-domain filter/kernel.
        N: int, optional
            The size of the frequency-domain response (default is 64).
            The filter is zero-padded or truncated to this size.
    Returns:
        f: 1D array
            Frequency coordinates (centered).
        h: 2D array
            2D frequency response of the filter (centered).
    """
    h = fft.fftshift(fft.fft2(fn, [N, N]))
    f = fft.fftshift(fft.fftfreq(N))  
    return f, h

img = cv.imread('cameraman.tif', cv.IMREAD_GRAYSCALE).astype(np.float32) # read image

img_a = cv.filter2D(img, -1, d) # spatial domain filtering

f, H = freqz2(d, N=256) # compute frequency response
F1, F2 = np.meshgrid(f, f)
Habs = np.abs(H) 

F = fft.fft2(img)
Hpad = fft.fft2(d, s=img.shape)
img_b = np.real(fft.ifft2(F * Hpad)) # frequency domain filtering

complete = plt.figure(figsize=(8, 8)) # plotting

ax1 = complete.add_subplot(2, 2, 1)
ax1.imshow(img, cmap='gray')
ax1.set_title("Original Image")
ax1.axis("off")

ax2 = complete.add_subplot(2, 2, 2)
ax2.imshow(img_a, cmap='gray')
ax2.set_title("Filtering in Spatial Domain")
ax2.axis("off")

ax3 = complete.add_subplot(2,2,3, projection='3d')
ax3.plot_surface(F1, F2, Habs, cmap='viridis', edgecolor='none')
ax3.set_title("Filter Frequency Response")
ax3.set_xlabel("Fx")
ax3.set_ylabel("Fy")
ax3.set_zlabel("Magnitude")

ax4 = complete.add_subplot(2, 2, 4)
ax4.imshow(img_b, cmap='gray')
ax4.set_title("Filtering in Frequency Domain")
ax4.axis("off")

plt.show()