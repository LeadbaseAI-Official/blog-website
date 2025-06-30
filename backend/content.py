import ast
import google.generativeai as genai
import markdown
import random

genai.configure(api_key="AIzaSyDzVcofu-epzmPwqqGugQeT7Hox5G2Qk1k")
model = genai.GenerativeModel("models/gemma-3n-e4b-it")


#- Use markdown-style formatting (## for H2, ### for H3, etc.)
def gemini(user_prompt, system_prompt=""):
    try:
        full_prompt = f"{system_prompt.strip()}\n\n{user_prompt.strip()}" if system_prompt else user_prompt.strip()
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"[Error] {e}"


def generate_intro_section(blog_title, primary_keywords):
    """Generates the introductory section with a strict question and first-hand feel."""
    system_prompt = """
You are an expert blog writer, skilled in creating extremely short, super practical, super effective, and human-sounding blog content. Your goal is to write blog posts that deeply resonate with readers and provide immediate value.

Your task is to generate ONLY the introductory section of a blog post. This section must:
- Be extremely short, even more concise, and to the point.
- Start immediately with a compelling, strict, and potentially controversial question related to the blog title and primary keywords to hook the reader.
- Be written in a natural, human-like, and conversational tone, giving a strong sense of first-hand experience or real problem-solving insight.
- Be highly engaging and immediately capture the reader's attention.
- Seamlessly transition into the main topic without needing an explicit introductory sentence like "In this blog post...".
- Use markdown format.
- Do NOT include a title, meta description, or any text outside this introductory section.
"""
    user_prompt = f"""
Blog Title: "{blog_title}"
Primary Keywords: {", ".join(primary_keywords)}

Generate the introductory section for this blog post.
"""
    intro_markdown = gemini(user_prompt, system_prompt)
    # Clean markdown code block formatting
    intro_markdown = intro_markdown.replace('```markdown', '').replace('```', '').strip()
    return intro_markdown

def generate_main_body(blog_title, secondary_keywords, long_tail_keywords):
    """Generates the main body of the blog content."""
    system_prompt = """
You are an expert blog writer, skilled in creating extremely short, super practical, super effective, and human-sounding blog content. Your goal is to write blog posts that deeply resonate with readers and provide immediate value.

Your task is to generate ONLY the main body content of a blog post. This section must:
- Be extremely short, even more concise, and to the point.
- Continue seamlessly from an introductory section (which you are NOT generating here).
- Use the provided secondary keywords as headings (H2, H3 where appropriate).
- Use rich, well-researched content and break content into digestible, scannable parts.
- Ensure the content is detailed, conversational, and aligns with search intent.
- Add semantic richness and natural keyword usage — avoid keyword stuffing.
- Make the content Google-friendly and likely to rank on page 1.
- Use the long tailed keywords as embedded questions and provide concise, helpful answers within the article to make it more engaging and interesting.
- **Include bullet points where appropriate to enhance readability and convey practical information quickly.**
- Use markdown format.
- Do NOT include a title, meta description, introductory/concluding remarks, or any text outside this main body content.
"""
    user_prompt = f"""
Blog Title: "{blog_title}"
Secondary Keywords: {", ".join(secondary_keywords)}
Long-Tail Keywords: {", ".join(long_tail_keywords)}

Generate the main body content for a blog post with the title "{blog_title}".
"""
    body_markdown = gemini(user_prompt, system_prompt)
    # Clean markdown code block formatting
    body_markdown = body_markdown.replace('```markdown', '').replace('```', '').strip()
    return body_markdown


def generate_seo_blog(topic):
    """Orchestrates the generation of the full blog post."""
    # Generate keywords directly using Gemini based on the topic
    keyword_system_prompt = """
    You are an AI assistant specialized in generating relevant keywords for blog posts based on a given topic.
    Your task is to identify 5 Primary Keywords, 5 Secondary Keywords, and 5 Long-Tail Keywords.
    Focus on search intent, semantic richness, and keyword quality.
    Do NOT include metadata. Only return three Python lists.

    Output format:
    primary_keywords = ['keyword 1', 'keyword 2']
    secondary_keywords = ['keyword 3', ..., 'keyword 7']
    long_tail_keywords = ['keyword 8', ..., 'keyword 12']

    Do not include any extra output, explanation, or formatting.
    Only valid Python code.
    """
    keyword_user_prompt = f"Generate keywords for the blog topic: '{topic}'"
    
    result_str = gemini(keyword_user_prompt, system_prompt=keyword_system_prompt)
    print('keywords generated')
    # Clean markdown code block formatting from result_str before parsing
    result_str = result_str.replace('```python', '').replace('```', '').strip()
    try:
        lines = result_str.strip().split('\n')
        primary_keywords = ast.literal_eval(lines[0].split('=')[1].strip())
        secondary_keywords = ast.literal_eval(lines[1].split('=')[1].strip())
        long_tail_keywords = ast.literal_eval(lines[2].split('=')[1].strip())
    except Exception as e:
        print(f"[Parsing Error] {e}\nRaw:\n{result_str}")
        # Fallback to generic keywords if parsing fails
        primary_keywords = [topic]
        secondary_keywords = [f"{topic} guide"]
        long_tail_keywords = [f"what is {topic}"]
        # Ensure title and html_output are not None on error
        return "", "", primary_keywords, secondary_keywords, long_tail_keywords # Return empty strings for html_output and blog_title


    # Generate blog title
    bt1 = gemini(
    f"""Give me one clear, SEO-optimized blog title.

It must include at least one of these exact primary keywords: {", ".join(primary_keywords)}.

Make it sound natural and relevant to what real people actually search for — no fluff, no clickbait, no gimmicks.

Avoid symbols, brackets, bolds, or unnatural phrasing. Keep it plain text, human-like, and directly aligned with search intent.

Only return the final blog title — nothing else.
"""
)
    bt2 = gemini(
    f"""Give me just one SEO-friendly blog title.

It must include at least one of these exact primary keywords: {", ".join(primary_keywords)}.

Make it sound natural and human — something someone would search for, but still compelling enough to click.

Avoid clickbait tricks like brackets or over-the-top words. No bolding, no caps. Just plain, well-written text.

Write as if I’m speaking directly to the reader, with a touch of opinion, contradiction, or insight — not robotic, not narrated.

Only return the title. No explanation, no extra lines, just one clean title.
"""
)
    blog_title = random.choice([bt1,bt2])
    print(f"Generated Blog Title: {blog_title}")

    # Generate intro and main body separately
    intro_markdown = generate_intro_section(blog_title, primary_keywords)
    main_body_markdown = generate_main_body(blog_title, secondary_keywords, long_tail_keywords)

    # Combine markdown content
    full_markdown = f"{intro_markdown}\n\n{main_body_markdown}"

    # Convert combined markdown to HTML
    html_output = markdown.markdown(full_markdown)

    return html_output, blog_title, primary_keywords, secondary_keywords, long_tail_keywords
