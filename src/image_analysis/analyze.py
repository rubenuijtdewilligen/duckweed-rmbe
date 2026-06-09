import cv2
import numpy as np
import os
import argparse
import re

def calculate_duckweed_coverage(image_path, show_preview=True):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image '{image_path}'.")
        return None

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_green = np.array([34, 20, 25])    
    upper_green = np.array([85, 255, 255])  

    mask = cv2.inRange(hsv, lower_green, upper_green)

    total_pixels = mask.size
    green_pixels = cv2.countNonZero(mask)
    coverage_percent = (green_pixels / total_pixels) * 100

    print(f"{coverage_percent:.2f}%")

    log_results(image_path, total_pixels, green_pixels, coverage_percent)

    if show_preview:
        max_dimension = 500
        h_orig, w_orig = img.shape[:2]
        scale_factor = max_dimension / h_orig if h_orig > w_orig else max_dimension / w_orig

        w_new = int(w_orig * scale_factor)
        h_new = int(h_orig * scale_factor)

        preview_img = cv2.resize(img, (w_new, h_new))
        preview_mask = cv2.resize(mask, (w_new, h_new))
        preview_mask_3ch = cv2.cvtColor(preview_mask, cv2.COLOR_GRAY2BGR)
        
        combined_preview = np.hstack((preview_img, preview_mask_3ch))

        window_title = f"{os.path.basename(image_path)} (Press any key to close)"
        cv2.imshow(window_title, combined_preview)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return coverage_percent

def log_results(image_path, total, green, percentage):
    log_file = "data/image_analysis_log.csv"
    file_name = os.path.basename(image_path)

    container_match = re.search(r"container(\d+)", file_name, re.IGNORECASE)
    day_match = re.search(r"day(\d+)", file_name, re.IGNORECASE)
    
    container = container_match.group(1) if container_match else "unknown"
    day = day_match.group(1) if day_match else "unknown"
    
    data_dict = {}
    
    if os.path.isfile(log_file):
        with open(log_file, "r") as f:
            lines = f.readlines()
            if lines:
                header = lines[0]
                for line in lines[1:]:
                    parts = line.strip().split(',')
                    if len(parts) >= 5:
                        key = (parts[0], parts[1]) 
                        data_dict[key] = line.strip()
    else:
        header = "container,day,total_pixels,green_pixels,coverage_percent\n"

    current_key = (container, day)
    data_dict[current_key] = f"{container},{day},{total},{green},{percentage:.4f}"

    with open(log_file, "w") as f:
        f.write(header)
        for key in sorted(data_dict.keys(), key=lambda x: (int(x[0]) if x[0].isdigit() else 999, int(x[1]) if x[1].isdigit() else 999)):
            f.write(data_dict[key] + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quantify duckweed surface area coverage from top-down images.")
    parser.add_argument("--image", type=str, required=True, help="Path to the target image file.")
    parser.add_argument("--no-preview", action="store_true", help="Disable the interactive OpenCV preview window.")
    
    args = parser.parse_args()
    
    if os.path.exists(args.image):
        calculate_duckweed_coverage(args.image, show_preview=not args.no_preview)
    else:
        print(f"Error: Target file '{args.image}' does not exist.")