import os
import json
import re
import sys
import requests
from PIL import Image
from io import BytesIO

# The modules are now in the same 'backend' directory, so direct import is fine
from content import gemini # Import gemini from content.py

def generate_image_prompts(blog_title):
    """
    Generates image prompts using the gemini model based on a blog title.
    (Copied from main.py for standalone testing/usage in this file)
    """
def generate_image_prompts(blog_title):
    """
    Generates image prompts using the gemini model based on a blog title.
    The prompts will include a light blue and white theme.
    """
    system_prompt = """
You are an AI that generates vivid, highly visual, text-free image prompts for generative models.

Your task:
- Output exactly 3 short image prompts based strictly on the given blog title.
- DO NOT include any text, labels, or logos in the scene.
- DO NOT mention the blog title.
- Each prompt must be unique, describing a visual concept or scene that is *directly and concretely* relevant to the blog topic. Avoid overly abstract metaphors.
- Ensure the theme is consistently **light blue and white**.
- Use styles like cinematic, macro photography, isometric, watercolor, surreal, vector art, etc.
- Return the output ONLY as a valid Python list of 3 string prompts like:
["prompt 1", "prompt 2", "prompt 3"]
No extra text. No explanation.
"""
    user_prompt = f"Blog Title: {blog_title}\nNow generate 3 short visual-only image prompts that are directly relevant to this topic, with a light blue and white theme."

    for _ in range(2):
        try:
            response = gemini(user_prompt, system_prompt)
            match = re.search(r"\[(.*?)\]", response, re.DOTALL)
            if match:
                prompts_raw = "[" + match.group(1).strip() + "]"
                prompts = eval(prompts_raw)
                if isinstance(prompts, list) and len(prompts) == 3: # Changed to 3 prompts
                    return prompts
        except Exception:
            continue
    return [f"A symbolic visual scene for: {blog_title}, light blue and white theme"] * 3 # Changed to 3 prompts


def download_and_crop_image(image_url, save_path, crop_percentage=20):
    """
    Downloads an image from a URL, crops it from the bottom, and saves it.

    Args:
        image_url (str): The URL of the image to download.
        save_path (str): The local path to save the cropped image.
        crop_percentage (int): The percentage to crop from the bottom (0-100).

    Returns:
        str or None: The save_path if successful, None otherwise.
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status() # Raise an exception for bad status codes

        img = Image.open(BytesIO(response.content))

        # Calculate crop dimensions
        width, height = img.size
        crop_height_px = int(height * (crop_percentage / 100))
        cropped_img = img.crop((0, 0, width, height - crop_height_px))

        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Save the cropped image
        cropped_img.save(save_path)
        print(f"Downloaded, cropped, and saved image to {save_path}")
        return save_path

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing image from {image_url}: {e}")
        return None


# Function to generate image URLs, download, crop, and save them
def generate_image_urls(prompts, blog_slug):
    """
    Generates image URLs, downloads, crops, and saves them locally.

    Args:
        prompts (list): A list of image prompts (strings).
        blog_slug (str): The slug of the blog post for naming saved images.

    Returns:
        list: A list of local image file paths (strings).
    """
    base_url = "https://pollinations.ai/p/"
    width = 640 # Keep width for 16:9 aspect ratio
    height = 360 # Keep height for 16:9 aspect ratio
    seed = 42 # Using a fixed seed for now, can be made dynamic
    model = 'turbo' # Changed model to 'gptimage'

    local_image_paths = []
    for i, prompt in enumerate(prompts):
        # Construct the URL for each prompt
        current_seed = seed + i
        import urllib.parse
        encoded_prompt = urllib.parse.quote_plus(prompt)
        image_url = f"{base_url}{encoded_prompt}?width={width}&height={height}&seed={current_seed}&model={model}"
        print(f"Generated URL for prompt '{prompt[:50]}...': {image_url}")

        # Define local save path in a temporary directory
        temp_dir = os.path.join('temp_images', blog_slug) # Use blog_slug for unique temp subfolder
        os.makedirs(temp_dir, exist_ok=True) # Ensure temp directory exists
        image_filename = f"{blog_slug}_image_{i+1}.jpg"
        save_path = os.path.join(temp_dir, image_filename)

        # Download, crop, and save the image
        saved_path = download_and_crop_image(image_url, save_path, crop_percentage=20)
        if saved_path:
            local_image_paths.append(saved_path)

    return local_image_paths

if __name__ == "__main__":
    # Example usage: Generate prompts, then generate, download, crop, and save images
    test_blog_title = "The Benefits of Regular Exercise"
    test_blog_slug = "benefits-regular-exercise"
    print(f"Generating prompts for blog title: {test_blog_title}")
    generated_prompts = generate_image_prompts(test_blog_title)
    print(f"Generated Prompts: {generated_prompts}")

    print("Generating, downloading, cropping, and saving images...")
    local_paths = generate_image_urls(generated_prompts, test_blog_slug)
    print("Saved Images Locally:", local_paths)
