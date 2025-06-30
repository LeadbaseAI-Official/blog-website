import sys
import os
import re,json
from datetime import datetime
import shutil  # For copying files

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content import gemini, generate_seo_blog
from image import generate_image_urls, generate_image_prompts


def embed_images_in_blog(blog_content, image_filenames):
    """
    Embeds image HTML tags in the blog content using the provided image filenames.
    Assumes images will be in a relative 'images/' directory within the blog folder.
    """
    paragraphs = re.split(r"(</p>)", blog_content)
    embedded_content = []
    image_index = 0

    for i, part in enumerate(paragraphs):
        embedded_content.append(part)
        # Embed an image after every second paragraph
        if part == "</p>" and (i // 2) % 2 == 1 and image_index < len(image_filenames):
            # Use the relative path to the image
            image_html = f"""
<div class="blog-image-cropped">
    <img src="images/{image_filenames[image_index]}"
         alt="Blog Illustration"
         loading="lazy"
         decoding="async"
         fetchpriority="high"
         class="fade-in-img">
</div>
"""
            embedded_content.append(image_html)
            image_index += 1

    return "".join(embedded_content)


def generate_filename(topic):
    """Generates a 4-5 word hyphenated filename based on the topic using Gemini."""
    system_prompt = """
You are an AI that generates short, 4-5 word, hyphenated names suitable for file slugs based on a given topic.

Your task:
- Generate exactly 4 to 5 words related to the topic.
- Join the words with hyphens.
- Ensure the words are lowercase and contain only letters (a-z) and hyphens.
- The name should be descriptive enough to differentiate the topic.
- Return ONLY the 4-5 word hyphenated name. No extra text, no explanation.
"""
    user_prompt = f"Topic: {topic}\nGenerate a 4-5 word hyphenated name for a file slug."

    for _ in range(3):  # Try a few times in case of bad output
        try:
            response = gemini(user_prompt, system_prompt).strip().lower()
            # Basic validation: check for 4 to 5 words separated by hyphens, only letters
            if re.fullmatch(r"^[a-z]+(?:-[a-z]+){3,4}$", response):
                return response
        except Exception:
            continue
    # Fallback if Gemini fails or returns invalid format
    slug = re.sub(r"\W+", "-", topic.lower()).strip("-")
    return "-".join(slug.split("-")[:5]) if slug else "default-filename"


def generate_meta_description(blog_title, primary_keywords):
    """Generates a concise and SEO-friendly meta description using Gemini."""
    system_prompt = """
You are an AI assistant specialized in generating concise and SEO-friendly meta descriptions for blog posts.
The meta description should be around 150-160 characters, summarize the blog post, and include relevant keywords.
It should be engaging and encourage clicks.
Return ONLY the meta description text, no extra formatting or explanation.
"""
    user_prompt = f"""
Blog Title: "{blog_title}"
Primary Keywords: {", ".join(primary_keywords)}
Generate a meta description for this blog post.
"""
    return gemini(user_prompt, system_prompt).strip()


def generate_short_title(full_title):
    """Generates a short, 3-4 word title for the HTML page title."""
    words = full_title.split()
    if len(words) > 4:
        return " ".join(words[:4])
    return full_title


def create_blog_html_file(blog_title, blog_slug, html_content, meta_description, image_filenames, short_blog_title):
    """
    Generates the index.html file for the blog post.
    """
    blogs_dir = "../blogs"
    blog_folder_path = os.path.join(blogs_dir, blog_slug)

    # Embed images into the HTML content using relative paths
    final_html_content = embed_images_in_blog(html_content, image_filenames)

    # Get current date for post-date
    current_date = datetime.now().strftime("%B %d, %Y")

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>LeadBaseAI | {short_blog_title}</title>
  <link rel="icon" href="/static/logo.png" type="image/png" />
  <meta name="description" content="{meta_description}" />
  <link rel="stylesheet" href="/static/blog_style.css" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" />
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet" />
</head>
<body>

  <header>
    <h1>LeadBaseAI Blog</h1>
    <nav class="nav-menu">
      <a href="/">Home</a>
      <a href="/blogs">Blogs</a>
      <a href="/contact">Contact</a>
    </nav>
  </header>

  <main class="container">
    <h2>{blog_title}</h2>
    <p class="post-date">{current_date}</p>
    <article>
      {final_html_content}
    </article>
  </main>

  <footer class="modern-footer">
    <div class="footer-content">
      <p>&copy; {datetime.now().year} LeadSparkAI. All rights reserved.</p>
      <div class="footer-links">
        <a href="mailto:support@leadbaseai.in"><i class="fas fa-envelope"></i> support@leadbaseai.in</a>
        <a href="tel:+918766334584"><i class="fas fa-phone"></i> +91 87663 34584</a>
        <a href="https://www.instagram.com/leadbaseai/" target="_blank"><i class="fab fa-instagram"></i> @leadbaseai</a>
      </div>
    </div>
  </footer>

</body>
</html>"""

    index_html_path = os.path.join(blog_folder_path, "index.html")
    with open(index_html_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"HTML file created for '{blog_slug}'.")


if __name__ == "__main__":
    processed_count = 0
    topics_to_process = []
    remaining_lines = []
    all_topics = []  # Initialize all_topics here

    try:
        with open("../topics.txt", "r") as f:  # Corrected path
            # Read all lines, strip whitespace, and filter out empty lines
            all_topics = [line.strip() for line in f if line.strip()]

            # Process only the first topic for now, similar to the old kd.csv logic
            if all_topics:
                topics_to_process = [all_topics[0]]
                remaining_lines = all_topics[1:]

        if topics_to_process:
            all_metadata = []
            for topic in topics_to_process:
                print(f"Processing topic: {topic}")
                try:
                    # Generate filename (slug)
                    blog_slug = generate_filename(topic)
                    print(f"Generated Blog Slug: {blog_slug}")

                    # --- Create blog folder structure early ---
                    blogs_dir = "../blogs"
                    os.makedirs(blogs_dir, exist_ok=True)
                    blog_folder_path = os.path.join(blogs_dir, blog_slug)
                    os.makedirs(blog_folder_path, exist_ok=True)
                    images_folder_path = os.path.join(blog_folder_path, "images")
                    os.makedirs(images_folder_path, exist_ok=True)
                    print(f"Created blog folder structure.")
                    # --- End early folder creation ---

                    # Generate blog content and keywords
                    html_content, title, primary_keywords, secondary_keywords, long_tail_keywords = generate_seo_blog(topic)
                    print(f"Generated Blog Title: {title}")

                    if title and html_content:  # Ensure both title and content are generated successfully
                        # Generate meta description
                        meta_description = generate_meta_description(title, primary_keywords)
                        print("Meta description generated.")

                        # Generate image prompts
                        image_prompts = generate_image_prompts(title)
                        print("Image prompts generated.")

                        # Generate, download, and save images locally to a temporary location
                        temp_image_paths = generate_image_urls(image_prompts, blog_slug)
                        print("Temporary images generated and saved.")

                        # --- Move images from temp to final blog images folder ---
                        final_image_filenames = []
                        for temp_path in temp_image_paths:
                            filename = os.path.basename(temp_path)
                            destination_path = os.path.join(images_folder_path, filename)
                            shutil.move(temp_path, destination_path)
                            final_image_filenames.append(filename)
                        print("Images moved to final destination.")

                        # Clean up the temporary image directory
                        temp_dir_to_remove = (
                            os.path.dirname(temp_image_paths[0])
                            if temp_image_paths
                            else None
                        )
                        if temp_dir_to_remove and os.path.exists(temp_dir_to_remove):
                            shutil.rmtree(temp_dir_to_remove)
                            print("Temporary image directory cleaned up.")
                        # --- End image move and cleanup ---

                        # Generate short title for HTML <title> tag
                        short_blog_title = generate_short_title(title)
                        print("Short blog title generated.")

                        # Create index.html using the moved images
                        create_blog_html_file(
                            title,
                            blog_folder_path,  # full path created earlier
                            html_content,
                            meta_description,
                            final_image_filenames,
                            short_blog_title,
                        )

                        print(f"HTML file created for '{topic}'.")

                        # Collect metadata
                        metadata_entry = {
                            "title": title,
                            "description": meta_description,
                            "url": f"blogs/{blog_slug}",  # Use blog_slug as the URL
                            "date": datetime.now().strftime("%Y-%m-%d"),  # Format the date
                        }
                        all_metadata.append(metadata_entry)
                        processed_count += 1
                    else:
                        print(
                            f"Skipping blog generation for topic '{topic}' due to missing title or content."
                        )
                except Exception as e:
                    print(f"Error processing topic '{topic}': {e}. Skipping this topic.")
        else:
            print("No topics to process.")

    except FileNotFoundError:
        print("Error: topics.txt not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Rewrite topics.txt with remaining lines
        if all_topics:
            with open("../topics.txt", "w", encoding="utf-8") as f:  # Corrected path
                for line in remaining_lines:
                    f.write(line + "\n")
            print(f"Processed {processed_count} topics. Remaining topics saved to topics.txt.")
        else:
            print("No topics found in topics.txt to rewrite.")

        # Save metadata to JSON file
        metadata_file_path = "../metadata.json"  # Corrected path
        existing_metadata = []
        if os.path.exists(metadata_file_path):
            try:
                with open(metadata_file_path, "r", encoding="utf-8") as f:
                    existing_metadata = json.load(f)
                if not isinstance(existing_metadata, list):
                    existing_metadata = []  # Reset if file content is not a list
            except json.JSONDecodeError:
                existing_metadata = []  # Reset if file is not valid JSON

        combined_metadata = existing_metadata + all_metadata

        with open(metadata_file_path, "w", encoding="utf-8") as f:
            json.dump(combined_metadata, f, indent=2)
        print("Metadata saved.")
