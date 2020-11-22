import numpy as np
import cv2
from skimage.measure import compare_ssim
import imutils
import tqdm

VIDEO_PATH = 'video.mp4'
VIDEO_OUTPUT_PATH = 'output.mp4'


def read_video(path_to_video):
    cap = cv2.VideoCapture(path_to_video)

    if not cap.isOpened():
        raise IOError(f'Could not open {path_to_video}. Check if the path is correct.')

    video_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    video_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)

    res, res2 = [], []
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        res.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        res2.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

    cap.release()
    return res2, (video_width, video_height, fps), res


def save_video(frames, vinfo, output_path):
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    out = cv2.VideoWriter(output_path, fourcc, vinfo[2], (int(vinfo[0]), int(vinfo[1])))

    if not out.isOpened():
        raise IOError(f'Could not open or create the file {output_path}')

    for frame in frames:
        out.write(frame)

    out.release()


class Car:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.coordinates = list()

    def update(self, x, y, w, h):
        self.x = (self.x + x) // 2
        self.y = (self.y + y) // 2
        self.w = (3 * self.w + w) // 4
        self.h = (3 * self.h + h) // 4
        self.coordinates.append((self.x, self.y))

    def update2(self, car):
        self.update(car.x, car.y, car.w, car.h)

    def intersectionArea(self, rect):
        x = max(self.x, rect[0])
        y = max(self.y, rect[1])
        w = min(self.x + self.w, rect[0] + rect[2]) - x
        h = min(self.y + self.h, rect[1] + rect[3]) - y
        if w <= 0 or h <= 0:
            return 0
        else:
            return w * h

    def getArea(self):
        return self.w * self.h

    def getInfo(self):
        return [self.x, self.y, self.w, self.h]

    def getCoordinates(self):
        return self.coordinates

    def isInside(self, pos):
        return (self.x <= pos[0] <= self.x + self.w) and (self.y <= pos[1] <= self.y + self.h)


def markCars(frame, cars):
    for car in cars:
        cv2.rectangle(frame, (car.x, car.y), (car.x + car.w, car.y + car.h), (0, 0, 255), 2)
        poss = car.getCoordinates()
        if len(poss) < 5:
            continue

        d = poss[len(poss) - 1][0] - poss[0][0]
        if d == 0:
            continue
        d = d // abs(d)
        last = -1
        for pos in poss:
            y = (pos[1] + pos[1] + car.h) // 2
            x = pos[0] + car.w if d < 0 else pos[0]
            if x < 0 or x > frame.shape[1]:
                continue
            if last == -1:
                last = x
            else:
                for xx in range(last, x, d):
                    crosses = False
                    for c in cars:
                        if c.isInside((xx, y)):
                            crosses = True
                    if not crosses:
                        cv2.circle(frame, (xx, y), 1, (255, 0, 0), 1)
                last = x

    return frame


def diff_frames(frames, c_frames):

    res = []
    threshold1, threshold2 = 300, 3000
    bridge_y1, bridge_y2 = 130, 240
    boxes = []
    cars = []
    used = []
    kernel = np.ones((5, 5), np.uint8)
    for i in tqdm.tqdm(range(len(frames) - 10)):
        (score, diff) = compare_ssim(frames[i + 10], frames[i], full=True)
        diff = np.uint8(diff * 255)
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)

        for c in contours:
            (x, y, w, h) = cv2.boundingRect(c)
            x += 5
            w -= 5
            boxes.append(w * h)
            if threshold1 <= w * h <= threshold2 and bridge_y1 <= y <= bridge_y2:
                flag = False
                for ind, car in enumerate(cars):
                    if (car.intersectionArea((x, y, w, h)) > car.getArea() * 0.25) and (abs(car.y - y) < car.y * 0.1):
                        flag = True
                        used[ind] += 1
                        car.update(x, y, w, h)
                if not flag:
                    used.append(1)
                    cars.append(Car(x, y, w, h))
        new_cars, new_used = [], []
        for ind, car in enumerate(cars):
            if used[ind] > -5:
                new_cars.append(car)
                new_used.append(used[ind] - 1)
        used, cars = new_used, new_cars
        frame = markCars(c_frames[i], cars)
        res.append(frame)
    return res


if __name__ == '__main__':
    video_frames, info, color_frames = read_video(VIDEO_PATH)
    save_video(diff_frames(video_frames, color_frames), info, output_path=VIDEO_OUTPUT_PATH)
