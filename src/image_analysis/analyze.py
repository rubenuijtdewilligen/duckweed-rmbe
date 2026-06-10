import cv2
import numpy as np
import os
import argparse
import re
import glob

def calculate_duckweed_coverage(image_path, show_preview=True):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image '{image_path}'.")
        return None

    lower_water = np.array([90, 90, 90])
    upper_water = np.array([255, 255, 255])
    
    mask_water = cv2.inRange(img, lower_water, upper_water)
    mask_plants = cv2.bitwise_not(mask_water)

    total_pixels = mask_plants.size
    green_pixels = cv2.countNonZero(mask_plants)
    coverage_percent = (green_pixels / total_pixels) * 100

    file_name = os.path.basename(image_path)
    print(f"{file_name} -> {coverage_percent:.2f}%")

    if show_preview:
        max_dimension = 500
        h_orig, w_orig = img.shape[:2]
        scale_factor = max_dimension / h_orig if h_orig > w_orig else max_dimension / w_orig
        w_new = int(w_orig * scale_factor)
        h_new = int(h_orig * scale_factor)

        preview_img = cv2.resize(img, (w_new, h_new), interpolation=cv2.INTER_AREA)
        preview_mask = cv2.resize(mask_plants, (w_new, h_new), interpolation=cv2.INTER_AREA)
        preview_mask_3ch = cv2.cvtColor(preview_mask, cv2.COLOR_GRAY2BGR)
        
        combined_preview = np.hstack((preview_img, preview_mask_3ch))

        window_title = f"QC: {file_name} (Press any key to close)"
        cv2.imshow(window_title, combined_preview)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return total_pixels, green_pixels, coverage_percent

def log_results(results_list):
    log_file = "data/image_analysis_log.csv"
    data_dict = {}
    header = "container,day,total_pixels,green_pixels,coverage_percent\n"
    
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

    for res in results_list:
        file_name = os.path.basename(res['path'])
        container_match = re.search(r"container(\d+)", file_name, re.IGNORECASE)
        day_match = re.search(r"day(\d+)", file_name, re.IGNORECASE)
        
        container = container_match.group(1) if container_match else "unknown"
        day = day_match.group(1) if day_match else "unknown"
        
        key = (container, day)
        data_dict[key] = f"{container},{day},{res['total']},{res['green']},{res['percentage']:.4f}"

    with open(log_file, "w") as f:
        f.write(header)
        for key in sorted(data_dict.keys(), key=lambda x: (int(x[0]) if x[0].isdigit() else 999, int(x[1]) if x[1].isdigit() else 999)):
            f.write(data_dict[key] + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quantify duckweed surface area coverage.")
    parser.add_argument("--image", type=str, help="Path to a single target image file.")
    parser.add_argument("--dir", type=str, help="Path to a directory containing multiple images.")
    parser.add_argument("--no-preview", action="store_true", help="Disable the interactive OpenCV preview window.")
    
    args = parser.parse_args()
    
    pending_results = []

    if args.dir:
        if os.path.isdir(args.dir):
            search_pattern = os.path.join(args.dir, "*container*_day*.png")
            image_paths = glob.glob(search_pattern)
            
            if not image_paths:
                print(f"Geen bestanden gevonden die voldoen aan het patroon in: {args.dir}")
            else:
                for path in sorted(image_paths):
                    metrics = calculate_duckweed_coverage(path, show_preview=not args.no_preview)
                    if metrics:
                        total, green, pct = metrics
                        pending_results.append({'path': path, 'total': total, 'green': green, 'percentage': pct})
                
                if pending_results:
                    log_results(pending_results)
        else:
            print(f"Error: Folder '{args.dir}' does not exist.")

    elif args.image:
        if os.path.exists(args.image):
            metrics = calculate_duckweed_coverage(args.image, show_preview=not args.no_preview)
            if metrics:
                total, green, pct = metrics
                log_results([{'path': args.image, 'total': total, 'green': green, 'percentage': pct}])
        else:
            print(f"Error: File '{args.image}' does not exist.")

    else:
        print("Error: Please provide --image or --dir to start the script.")