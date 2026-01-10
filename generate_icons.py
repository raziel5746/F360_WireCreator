"""
Generate icon folders for Fusion 360 ButtonRowCommandInput.
Creates folder structure with 16x16.png and 32x32.png for each number.
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_number_icon(number, size, output_path):
    """Create a simple icon with a number."""
    # Create image with white background
    img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a system font
    try:
        font = ImageFont.truetype("arial.ttf", int(size * 0.7))
    except:
        font = ImageFont.load_default()
    
    # Get text bounding box for centering
    text = str(number)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calculate position to center the text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]
    
    # Draw the number
    draw.text((x, y), text, fill='black', font=font)
    
    # Save
    img.save(output_path, 'PNG')
    print(f"Created: {output_path}")

if __name__ == "__main__":
    resources_dir = r"c:\Users\razie\Desktop\My Fusion Add-ins\WireCreator\Resources"
    
    # Create folder structure for each number
    for num in [1, 2, 3]:
        folder_path = os.path.join(resources_dir, f"midpoint_{num}")
        os.makedirs(folder_path, exist_ok=True)
        
        # Create 16x16 and 32x32 icons
        create_number_icon(num, 16, os.path.join(folder_path, "16x16.png"))
        create_number_icon(num, 32, os.path.join(folder_path, "32x32.png"))
    
    print("\nDone! Icon folders created.")
