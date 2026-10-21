"""GPS-free flight's first step (#24): a position from optical flow and the rangefinder, the way
PX4 does it with a flow sensor, but from V's camera pointed down.

From one frame to the next, the ground slides under the camera. Phase correlation (in numpy:
the peak of the two frames' cross-power spectrum) finds how far, to a fraction of a pixel. The
ground point that was under the middle of the first frame is then found in the second, and with
the drone's attitude (from its own IMU, which doesn't need GPS; in the sim the log's attitude
stands in) and its height (from Base's rangefinder), the drone's move over the ground follows:
the same ray, from where the drone is now, has to land on that point. Rotation between frames
is in the attitude, so it doesn't count as movement. Chained frame to frame, that's a position
that drifts, slowly, with no GPS at all.

It needs texture to track: on a featureless ground there's nothing to correlate. A full
visual-inertial odometry package would do better, and isn't installed here.
"""

import numpy as np

from pcs14.smart import ortho

SCALE = 1  # frames can be averaged down by this much before correlating (2 halves the time
# but biases the shift: 7.9% drift on the test path, against 1.4% at full size)


def _gray(picture) -> np.ndarray:
    a = np.asarray(picture, dtype=float)
    return a.mean(axis=2) if a.ndim == 3 else a


def _shrink(a: np.ndarray, k: int) -> np.ndarray:
    h, w = (a.shape[0] // k) * k, (a.shape[1] // k) * k
    return a[:h, :w].reshape(h // k, k, w // k, k).mean(axis=(1, 3))


def _peak_near(cross: np.ndarray, py: float, px: float, half: float, step: float):
    """The correlation's highest point within `half` a pixel of (py, px), on a grid `step`
    apart: the inverse DFT of the cross-power spectrum, evaluated only there."""
    rows, cols = cross.shape
    steps = np.arange(-half, half + step / 2, step)
    ey = np.exp(2j * np.pi * np.outer(py + steps, np.fft.fftfreq(rows)))  # (steps, rows)
    ex = np.exp(2j * np.pi * np.outer(np.fft.fftfreq(cols), px + steps))  # (cols, steps)
    fine = ((ey @ cross) @ ex).real
    ky, kx = np.unravel_index(int(np.argmax(fine)), fine.shape)
    return py + steps[ky], px + steps[kx]


def shift(a, b) -> tuple[float, float]:
    """(rows, columns) the content of `a` moved to be at in `b`, to a hundredth of a pixel: the
    phase correlation's peak, then the correlation itself evaluated on finer and finer grids
    around it by an upsampled DFT (Guizar-Sicairos's method, the one scikit-image's phase
    correlation uses), so no curve is fitted to the peak and nothing pulls it toward a whole
    pixel."""
    a, b = _gray(a), _gray(b)
    window = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    fa, fb = np.fft.fft2((a - a.mean()) * window), np.fft.fft2((b - b.mean()) * window)
    cross = fb * np.conj(fa)
    cross = cross / (np.abs(cross) + 1e-12)
    corr = np.fft.ifft2(cross).real
    rows, cols = corr.shape
    py, px = np.unravel_index(int(np.argmax(corr)), corr.shape)
    py = py - rows if py > rows / 2 else py
    px = px - cols if px > cols / 2 else px
    py, px = _peak_near(cross, py, px, half=1.0, step=0.1)
    py, px = _peak_near(cross, py, px, half=0.1, step=0.01)
    return float(py), float(px)


def track(pictures, attitudes, heights, camera: ortho.Camera, pitch_rad: float,
          offset=(0.0, 0.0, 0.0)) -> np.ndarray:  # fmt: skip
    """(east, north) of the drone at each frame, from the first at (0, 0): the frames (any
    iterable, read one at a time), the drone's attitude at each (x, y, z, w), and the
    rangefinder's height at each."""
    cy, cx = camera.center
    here = np.zeros(2)
    out = [here.copy()]
    before_picture = None
    for k, (picture, attitude, height) in enumerate(
        zip(pictures, attitudes, heights, strict=False)
    ):
        picture = _shrink(_gray(picture), SCALE)
        if k == 0:
            before_picture, before = picture, (attitude, height)
            continue
        pose = ortho.Pose.on_drone((here[0], here[1], before[1]), before[0], offset, pitch_rad)
        # the ground point under the middle of the frame before
        ray = pose.rotation @ np.array([1.0, 0.0, 0.0])
        point = pose.position + ray * (-pose.position[2] / ray[2])
        dy, dx = shift(before_picture, picture)
        row, col = cy + dy * SCALE, cx + dx * SCALE
        # the same point, now at (row, col): from where must the drone see it there?
        now = ortho.Pose.on_drone((0.0, 0.0, height), attitude, offset, pitch_rad)
        d = now.rotation @ np.array([camera.focal_px, -(col - cx), -(row - cy)])
        d = d / np.linalg.norm(d)
        t = (now.position[2]) / -d[2]
        here = point[:2] - now.position[:2] - d[:2] * t
        out.append(here.copy())
        before_picture, before = picture, (attitude, height)
    return np.array(out)
