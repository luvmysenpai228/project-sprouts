import cv2
import numpy as np
import sys
import os


def calculate_brightness(image):
    """Расчет средней яркости изображения в HSV пространстве"""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    return np.mean(hsv[:, :, 2])


def classify_image_by_brightness(brightness_value):
    """
    Классификация изображения по яркости
    brightness_value: среднее значение яркости (0-255)
    """
    if brightness_value < 100:
        return "very_dark"
    elif brightness_value < 130:
        return "dark"
    elif brightness_value < 180:
        return "normal"
    else:
        return "bright"


def get_parameters_by_brightness(brightness_value):
    """
    Автоматический подбор параметров в зависимости от яркости изображения
    """
    img_type = classify_image_by_brightness(brightness_value)

    # Базовые параметры для нормального изображения
    params = {
        'h_min': 20, 'h_max': 85, 's_min': 100, 's_max': 255,
        'v_min': 110, 'v_max': 255, 'min_area': 50,
        'erode_iter': 1, 'dilate_iter': 2, 'blur_size': 5
    }

    # Корректировки в зависимости от яркости
    if img_type == "very_dark":
        params.update({
            'h_min': 15, 'h_max': 90, 's_min': 80, 's_max': 255,
            'v_min': 60, 'v_max': 220, 'min_area': 40,
            'erode_iter': 1, 'dilate_iter': 3, 'blur_size': 7
        })
    elif img_type == "dark":
        params.update({
            'h_min': 18, 'h_max': 88, 's_min': 90, 's_max': 255,
            'v_min': 80, 'v_max': 230, 'min_area': 45,
            'erode_iter': 1, 'dilate_iter': 2, 'blur_size': 5
        })
    elif img_type == "bright":
        params.update({
            'h_min': 25, 'h_max': 80, 's_min': 120, 's_max': 255,
            'v_min': 130, 'v_max': 250, 'min_area': 55,
            'erode_iter': 2, 'dilate_iter': 1, 'blur_size': 3
        })

    return params, img_type


def detect_seedlings(image_path, h_min=20, h_max=85, s_min=100, s_max=255, v_min=110, v_max=255,
                     min_area=50, erode_iter=1, dilate_iter=2, blur_size=5):
    """
    Основная функция детектирования
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Ошибка: не удалось загрузить изображение {image_path}")
        return 0

    # Изменяем размер для отображения
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

    kernel = np.ones((5, 5), np.uint8)
    mask_eroded = cv2.erode(mask_raw, kernel, iterations=erode_iter)
    mask_dilated = cv2.dilate(mask_eroded, kernel, iterations=dilate_iter)

    blur_size = blur_size if blur_size % 2 == 1 else blur_size + 1
    mask_blurred = cv2.GaussianBlur(mask_dilated, (blur_size, blur_size), 0)

    _, mask_final = cv2.threshold(mask_blurred, 127, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
    seedling_count = len(valid_contours)

    result = original.copy()
    for cnt in valid_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(result, (x, y), (x + w, y + h), (255, 0, 0), 2)

    # Добавляем информацию на изображение
    text = f"Count: {seedling_count}"
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

    # Добавляем параметры в верхний левый угол
    param_text = f"H[{h_min}-{h_max}] S[{s_min}-{s_max}] V[{v_min}-{v_max}]"
    cv2.putText(result, param_text, (10, 25),
                font, 0.5, (0, 255, 0), 1)

    return result, seedling_count


def process_multiple_images(image_list):
    """
    Обработка нескольких изображений с автоматическим подбором параметров
    """
    results = {}
    print("\n" + "=" * 60)
    print("НАЧАЛО ОБРАБОТКИ ИЗОБРАЖЕНИЙ")
    print("=" * 60)

    for i, image_path in enumerate(image_list, 1):
        if os.path.exists(image_path):
            print(f"\n--- Обработка {i}/{len(image_list)}: {os.path.basename(image_path)} ---")

            # Загружаем для анализа яркости
            img = cv2.imread(image_path)
            brightness = calculate_brightness(img)
            img_type = classify_image_by_brightness(brightness)

            print(f"  Яркость: {brightness:.2f}, Тип: {img_type}")

            # Подбираем параметры
            params, _ = get_parameters_by_brightness(brightness)

            print(f"  Параметры: H[{params['h_min']}-{params['h_max']}] "
                  f"S[{params['s_min']}-{params['s_max']}] "
                  f"V[{params['v_min']}-{params['v_max']}]")

            # Обрабатываем
            result_img, count = detect_seedlings(
                image_path,
                h_min=params['h_min'],
                h_max=params['h_max'],
                s_min=params['s_min'],
                s_max=params['s_max'],
                v_min=params['v_min'],
                v_max=params['v_max'],
                min_area=params['min_area'],
                erode_iter=params['erode_iter'],
                dilate_iter=params['dilate_iter'],
                blur_size=params['blur_size']
            )

            results[image_path] = count
            print(f"  Результат: {count} саженцев")

            # Показываем результат
            cv2.imshow(f"{os.path.basename(image_path)}", result_img)
        else:
            print(f"\nОшибка: Файл не найден - {image_path}")
            results[image_path] = None

    # Вывод итогов
    print("\n" + "=" * 60)
    print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 60)
    for i, (path, count) in enumerate(results.items(), 1):
        if count is not None:
            print(f"{i}. {os.path.basename(path)}: {count} саженцев")
        else:
            print(f"{i}. {os.path.basename(path)}: НЕ ЗАГРУЖЕНО")

    print("\n" + "=" * 60)
    print("Нажмите ESC для выхода или любую клавишу для следующего...")
    print("(Все окна закроются после нажатия ESC)")

    # Ожидание закрытия окон
    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == 27:  # ESC
            break

    cv2.destroyAllWindows()

    return results


if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))

    # Автоматическая загрузка трех изображений
    # Вариант 1: img1.jpg, img2.jpg, img3.jpg
    image_paths = [
        os.path.join(script_dir, "img1.jpg"),
        os.path.join(script_dir, "img2.jpg"),
        os.path.join(script_dir, "img3.jpg")
    ]

    # Проверка наличия файлов
    print("Проверка наличия файлов:")
    for path in image_paths:
        if os.path.exists(path):
            print(f"  ✓ {os.path.basename(path)} найден")
        else:
            print(f"  ✗ {os.path.basename(path)} НЕ НАЙДЕН")

    # Если файлы не найдены, пробуем альтернативные имена
    if not all(os.path.exists(path) for path in image_paths):
        print("\nПробуем альтернативные имена файлов...")
        alt_paths = [
            os.path.join(script_dir, "test1.jpg"),
            os.path.join(script_dir, "test2.jpg"),
            os.path.join(script_dir, "test3.jpg")
        ]

        # Проверяем альтернативные имена
        alt_found = True
        for path in alt_paths:
            if not os.path.exists(path):
                alt_found = False
                break

        if alt_found:
            image_paths = alt_paths
            print("Используются test1.jpg, test2.jpg, test3.jpg")
        else:
            print("\nВНИМАНИЕ: Некоторые файлы не найдены!")
            print("Убедитесь, что файлы img1.jpg, img2.jpg, img3.jpg")
            print("или test1.jpg, test2.jpg, test3.jpg находятся в папке:")
            print(script_dir)

    print("\n" + "=" * 60)

    # Обработка всех изображений
    results = process_multiple_images(image_paths)

    # Сохранение результатов в файл
    output_file = os.path.join(script_dir, "results.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Результаты детектирования саженцев\n")
        f.write("=" * 50 + "\n")
        for path, count in results.items():
            if count is not None:
                f.write(f"{os.path.basename(path)}: {count} саженцев\n")
            else:
                f.write(f"{os.path.basename(path)}: ОШИБКА ЗАГРУЗКИ\n")

    print(f"\nРезультаты сохранены в файл: {output_file}")