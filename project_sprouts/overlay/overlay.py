import cv2
import numpy as np


def safe_merge(img1_path, img2_path, output_path="result.jpg"):
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]

    if w1 != w2:
        min_w = min(w1, w2)
        img1 = cv2.resize(img1, (min_w, h1))
        img2 = cv2.resize(img2, (min_w, h2))
        w = min_w
    else:
        w = w1

    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]

    orb = cv2.ORB_create(nfeatures=2000)

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)

    if des1 is not None and des2 is not None:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)[:100]

        if len(matches) >= 10:
            offsets = []
            for match in matches:
                y1 = int(kp1[match.queryIdx].pt[1])
                y2 = int(kp2[match.trainIdx].pt[1])
                offsets.append(y1 - y2)

            best_offset = int(np.median(offsets))
            print(f"Найдено смещение: {best_offset}")
        else:
            best_offset = h1 // 2 - h2 // 2
            print(f"Совпадений мало, использую центр: {best_offset}")
    else:
        best_offset = h1 // 2 - h2 // 2
        print(f"Точек нет, использую центр: {best_offset}")

    if best_offset < 0:
        result_h = h1 + h2 + best_offset
        result = np.zeros((result_h, w, 3), dtype=np.uint8)
        result[:h1, :] = img1

        y_start = h1 + best_offset
        h2_copy = min(h2, result_h - y_start)
        if h2_copy > 0:
            result[y_start:y_start + h2_copy, :] = img2[:h2_copy, :]

        non_zero = np.any(result != 0, axis=2)
        rows = np.any(non_zero, axis=1)
        cols = np.any(non_zero, axis=0)
        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]
        result = result[y_min:y_max + 1, x_min:x_max + 1]

    else:
        result_h = h1 + best_offset + h2
        result = np.zeros((result_h, w, 3), dtype=np.uint8)
        result[:h1, :] = img1
        result[best_offset:best_offset + h2, :] = img2

        non_zero = np.any(result != 0, axis=2)
        rows = np.any(non_zero, axis=1)
        cols = np.any(non_zero, axis=0)
        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]
        result = result[y_min:y_max + 1, x_min:x_max + 1]

    final_h, final_w = result.shape[:2]

    cv2.imwrite(output_path, result)
    print(f"Результат сохранен в {output_path}")
    print(f"Размер после обрезки: {final_w}x{final_h}")

    highlighted = result.copy()
    highlighted = cv2.cvtColor(highlighted, cv2.COLOR_BGR2RGB)

    h1_orig, w1_orig = img1.shape[:2]
    h2_orig, w2_orig = img2.shape[:2]

    if best_offset < 0:
        overlap_start = h1_orig + best_offset
        overlap_end = h1_orig
    else:
        overlap_start = best_offset
        overlap_end = min(h1_orig, best_offset + h2_orig)

    y_offset = y_min

    overlap_start = max(0, overlap_start - y_offset)
    overlap_end = min(final_h, overlap_end - y_offset)

    if overlap_start < overlap_end:
        for y in range(overlap_start, overlap_end):
            highlighted[y, :, 0] = np.clip(highlighted[y, :, 0] + 40, 0, 255)

        cv2.rectangle(highlighted, (0, overlap_start), (final_w, overlap_end), (255, 0, 0), 2)

    highlighted_bgr = cv2.cvtColor(highlighted, cv2.COLOR_RGB2BGR)
    highlighted_path = output_path.replace(".jpg", "_highlighted.jpg").replace(".png", "_highlighted.jpg")
    cv2.imwrite(highlighted_path, highlighted_bgr)

    print(f"Highlighted результат сохранен в {highlighted_path}")
    print(f"Область наложения: {overlap_start} - {overlap_end} пикселей")

    return result, highlighted


safe_merge("half1.jpg", "half2.jpg", "result.jpg")