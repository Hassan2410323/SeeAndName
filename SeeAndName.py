# rename_by_ocr.py
import os
import cv2
from PIL import Image
import pytesseract

# ---- SET THIS: path to tesseract.exe on your PC ----
# Example: r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---- SET THIS: folder with your images ----
FOLDER = r"D:\Brand Logos"

# acceptable image extensions
EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')

def clean_filename(s):
    s = s.strip()
    # keep letters, numbers, space, dash, underscore, dot
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_()."
    out = "".join(ch for ch in s if ch in allowed)
    out = out.replace(" ", "_")  # replace spaces with underscore
    out = out.strip("_.-")
    return out[:200]  # limit length

def preprocess_for_ocr(path):
    img = cv2.imread(path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # invert if mostly white background
    mean_val = cv2.mean(gray)[0]
    if mean_val > 180:  # very light background
        gray = 255 - gray  # invert colors

    # increase contrast
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    gray = cv2.GaussianBlur(gray, (3,3), 0)

    # threshold to make text clear
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # upscale for better OCR reading
    h, w = thresh.shape
    if w < 1000:
        scale = 1000.0 / w
        thresh = cv2.resize(thresh, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)

    return Image.fromarray(thresh)


def main():
    if not os.path.isdir(FOLDER):
        print("Folder does not exist:", FOLDER)
        return

    files = [f for f in os.listdir(FOLDER) if f.lower().endswith(EXTS)]
    files.sort()

    used_names = {}
    for fname in files:
        full = os.path.join(FOLDER, fname)
        print("Processing:", fname)
        pre = preprocess_for_ocr(full)
        if pre is None:
            print("  Could not open", fname); continue

        # OCR: try to get text
        text = pytesseract.image_to_string(pre, lang='eng').strip()
        if not text:
            print("  No text found, skipping.")
            continue

        # simplify: take first line(s)
        lines = [ln for ln in (l.strip() for l in text.splitlines()) if ln]
        if not lines:
            print("  No usable lines, skipping.")
            continue

        # choose best candidate: join first two lines
        candidate = " ".join(lines[:2])
        base = clean_filename(candidate)
        if not base:
            print("  Cleaned name empty, skipping.")
            continue

        ext = os.path.splitext(fname)[1]
        new_name = f"{base}{ext}"

        # handle duplicates
        idx = 1
        while new_name.lower() in used_names or os.path.exists(os.path.join(FOLDER, new_name)):
            new_name = f"{base}_{idx}{ext}"
            idx += 1

        src = full
        dst = os.path.join(FOLDER, new_name)
        os.rename(src, dst)
        used_names[new_name.lower()] = True
        print("  Renamed to:", new_name)

if __name__ == "__main__":
    main()
