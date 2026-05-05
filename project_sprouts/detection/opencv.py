import cv2
import numpy as np
import sys
import os

def detect_seedlings(image_path, h_min=20, h_max=85, s_min=100, s_max=255, v_min=110, v_max=255,
                     min_area=50, erode_iter=1, dilate_iter=2, blur_size=5):
    """
            Детектирование саженцев пихт по макушкам.
            Параметры:
                h_min, h_max: оттенок (0-180) рекомендуемые 38-80
                s_min, s_max: насыщенность (0-255) рекомендуемые 60-255
                v_min, v_max: яркость (0-255) рекомендуемые 80-220 (саженцы яркие, мох тусклый)
                min_area: минимальная площадь объекта (рекомендуемые 80)
                erode_iter: итерации эрозии (рекомендуемые 1)
                dilate_iter: итерации дилатации (рекомендуемые 2)
                blur_size: размер размытия (рекомендуемые 5)
    """

    img = cv2.imread(image_path)

    screen_height = 600
    screen_width = 1000

    height, width = img.shape[:2]
    scale = min(screen_width / width, screen_height / height, 1.0)

    if scale < 1.0:
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = cv2.resize(img, (new_width, new_height))

    original = img.copy()

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_green = np.array([h_min, s_min, v_min])
    upper_green = np.array([h_max, s_max, v_max])

    mask_raw = cv2.inRange(hsv, lower_green, upper_green)

    mask_before = mask_raw.copy()
    overlay_before = cv2.cvtColor(mask_before, cv2.COLOR_GRAY2BGR)
    h_before, w_before = overlay_before.shape[:2]
    cv2.rectangle(overlay_before, (5, 5), (350, 55), (0, 0, 0), -1)
    cv2.putText(overlay_before, "Mask before morphology (raw)", (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    kernel = np.ones((5, 5), np.uint8)
    mask_eroded = cv2.erode(mask_raw, kernel, iterations=erode_iter)
    mask_dilated = cv2.dilate(mask_eroded, kernel, iterations=dilate_iter)

    blur_size = blur_size if blur_size % 2 == 1 else blur_size + 1
    mask_blurred = cv2.GaussianBlur(mask_dilated, (blur_size, blur_size), 0)

    _, mask_final = cv2.threshold(mask_blurred, 127, 255, cv2.THRESH_BINARY)

    mask_after = mask_final.copy()
    overlay_after = cv2.cvtColor(mask_after, cv2.COLOR_GRAY2BGR)
    h_after, w_after = overlay_after.shape[:2]
    cv2.rectangle(overlay_after, (5, 5), (350, 55), (0, 0, 0), -1)
    cv2.putText(overlay_after, "Mask after morphology + blur", (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]

    seedling_count = len(valid_contours)

    result = original.copy()
    for cnt in valid_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(result, (x, y), (x + w, y + h), (255, 0, 0), 2)

    text = f"Total count: {seedling_count}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2

    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)

    overlay = result.copy()
    cv2.rectangle(overlay, (10, result.shape[0] - text_height - 20),
                  (10 + text_width + 10, result.shape[0] - 10), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, result, 0.4, 0, result)

    cv2.putText(result, text, (15, result.shape[0] - 15),
                font, font_scale, (255, 255, 255), thickness)

    cv2.imshow("Original image with rectangles", result)
    cv2.imshow("Mask before morphology (black-white)", overlay_before)
    cv2.imshow("Mask after morphology (black-white)", overlay_after)

    print(f"Total count: {seedling_count}")

    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return seedling_count


if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))

    image_path = os.path.join(script_dir, "test1.jpg")

    count = detect_seedlings(image_path)