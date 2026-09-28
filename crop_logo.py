from PIL import Image
import os

def crop_assets():
    # Create img directory if it doesn't exist
    os.makedirs('assets/img', exist_ok=True)
    
    # Open the uploaded image
    img_path = r'C:\Users\praty\.gemini\antigravity-ide\brain\24bc92a0-afa6-4ea6-b485-0783e50756d5\.user_uploaded\media_1790586202340.jpg'
    try:
        img = Image.open(img_path)
    except FileNotFoundError:
        print("Image not found.")
        return

    # Image is 1024x682
    # The top right quadrant has the favicon and app icon.
    # The top left quadrant has the main logo.
    
    # 1. Crop Main Logo (approximate top-left area)
    # Left: 50, Upper: 50, Right: 600, Lower: 300
    logo = img.crop((50, 50, 600, 300))
    logo.save('assets/img/logo.png')
    
    # 2. Crop Favicon (approximate top-right area, the 180x180 app icon)
    # Left: 830, Upper: 60, Right: 980, Lower: 210
    favicon = img.crop((830, 60, 980, 210))
    favicon.save('assets/img/favicon.png')
    
    # Also save a small version for actual favicon
    favicon_small = favicon.resize((32, 32))
    favicon_small.save('assets/img/favicon.ico')
    
    print("Assets cropped and saved!")

if __name__ == "__main__":
    crop_assets()
