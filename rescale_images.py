from PIL import Image
import os

def rescale_image(input_path, output_path, resolution):
    try:
        with Image.open(input_path) as img:
            img = img.resize(resolution)
            img.save(output_path)
            print(f"Image saved to {output_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    input_path = "assets/parkour_dash_background.jpg"  # Replace with your input image path
    output_path = "assets/parkour_dash_background.jpg"  # Replace with your desired output path
    resolution = (1000, 700)  # Replace with your desired resolution (width, height)

    rescale_image(input_path, output_path, resolution)