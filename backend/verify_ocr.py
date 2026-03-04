import pytesseract
from PIL import Image
import sys
import os

# Path to the uploaded image (using the path provided in metadata)
image_path = "/app/debug_violeta.png"

def test_ocr():
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    print(f"Testing OCR on: {image_path}")
    try:
        image = Image.open(image_path)
        # Using the same languages as in the service
        text = pytesseract.image_to_string(image, lang='spa+eng')
        
        print("\n--- EXTRACTED TEXT (First 500 chars) ---")
        print(text[:500])
        print("\n--- END OF EXTRACTED TEXT ---")
        
        if len(text.strip()) > 0:
            print("\nSUCCESS: Text extracted successfully.")
        else:
            print("\nWARNING: No text extracted.")
            
    except Exception as e:
        print(f"\nERROR: OCR failed: {e}")

if __name__ == "__main__":
    test_ocr()
