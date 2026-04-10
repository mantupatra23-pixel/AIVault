import os
import time
import re
from fastapi import FastAPI, BackgroundTasks
from supabase import create_client, Client
import groq

app = FastAPI()

# 1. API KEYS & CLIENTS
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = groq.Client(api_key=GROQ_API_KEY)

# 2. 50+ TOP AI TOOLS LIST (Target: 10Cr Traffic)
AI_TOOLS_LIST = [
    {"name": "ChatGPT", "url": "https://chatgpt.com", "cat": "Chatbot"},
    {"name": "Claude AI", "url": "https://claude.ai", "cat": "Chatbot"},
    {"name": "Midjourney", "url": "https://midjourney.com", "cat": "Image Gen"},
    {"name": "Sora", "url": "https://openai.com/sora", "cat": "Video Gen"},
    {"name": "Perplexity", "url": "https://perplexity.ai", "cat": "Search Engine"},
    {"name": "Jasper", "url": "https://jasper.ai", "cat": "Writing"},
    {"name": "Grammarly", "url": "https://grammarly.com", "cat": "Assistant"},
    {"name": "Luma Dream Machine", "url": "https://lumalabs.ai", "cat": "Video Gen"},
    {"name": "Suno AI", "url": "https://suno.com", "cat": "Music"},
    {"name": "Udio", "url": "https://udio.com", "cat": "Music"},
    {"name": "Leonardo AI", "url": "https://leonardo.ai", "cat": "Art"},
    {"name": "ElevenLabs", "url": "https://elevenlabs.io", "cat": "Voice"},
    {"name": "HeyGen", "url": "https://heygen.com", "cat": "Video Gen"},
    {"name": "Runway Gen-3", "url": "https://runwayml.com", "cat": "Video Gen"},
    {"name": "Gamma App", "url": "https://gamma.app", "cat": "Presentation"},
    {"name": "Canva Magic", "url": "https://canva.com", "cat": "Graphic Design"},
    {"name": "Vercel V0", "url": "https://v0.dev", "cat": "Coding"},
    {"name": "Cursor AI", "url": "https://cursor.com", "cat": "Coding"},
    {"name": "Github Copilot", "url": "https://github.com/features/copilot", "cat": "Coding"},
    {"name": "Replicate", "url": "https://replicate.com", "cat": "Developer Tool"},
    {"name": "Hugging Face", "url": "https://huggingface.co", "cat": "Developer Tool"},
    {"name": "Groq Cloud", "url": "https://groq.com", "cat": "Developer Tool"},
    {"name": "Adobe Firefly", "url": "https://adobe.com/firefly", "cat": "Image Gen"},
    {"name": "DALL-E 3", "url": "https://openai.com/dall-e-3", "cat": "Image Gen"},
    {"name": "Descript", "url": "https://descript.com", "cat": "Video Editor"},
    {"name": "Fireflies AI", "url": "https://fireflies.ai", "cat": "Transcription"},
    {"name": "Otter AI", "url": "https://otter.ai", "cat": "Transcription"},
    {"name": "Copy AI", "url": "https://copy.ai", "cat": "Marketing"},
    {"name": "Writesonic", "url": "https://writesonic.com", "cat": "Marketing"},
    {"name": "Quillbot", "url": "https://quillbot.com", "cat": "Writing"},
    {"name": "Character AI", "url": "https://character.ai", "cat": "Entertainment"},
    {"name": "Pika Labs", "url": "https://pika.art", "cat": "Video Gen"},
    {"name": "Relume", "url": "https://relume.io", "cat": "Web Design"},
    {"name": "Framer AI", "url": "https://framer.com", "cat": "Web Design"},
    {"name": "Murf AI", "url": "https://murf.ai", "cat": "Voice"},
    {"name": "Pictory", "url": "https://pictory.ai", "cat": "Video Gen"},
    {"name": "Synthesia", "url": "https://synthesia.io", "cat": "Video Gen"},
    {"name": "Kling AI", "url": "https://klingai.com", "cat": "Video Gen"},
    {"name": "Phind", "url": "https://phind.com", "cat": "Coding Search"},
    {"name": "Tabnine", "url": "https://tabnine.com", "cat": "Coding"},
    {"name": "Beautiful AI", "url": "https://beautiful.ai", "cat": "Presentation"},
    {"name": "Tome AI", "url": "https://tome.app", "cat": "Presentation"},
    {"name": "Rose AI", "url": "https://rose.ai", "cat": "Data Science"},
    {"name": "SheetAI", "url": "https://sheetai.app", "cat": "Excel/Sheets"},
    {"name": "Formula Bot", "url": "https://formulabot.com", "cat": "Excel/Sheets"},
    {"name": "Rewind AI", "url": "https://rewind.ai", "cat": "Productivity"},
    {"name": "Mem AI", "url": "https://mem.ai", "cat": "Productivity"},
    {"name": "Notion AI", "url": "https://notion.so/product/ai", "cat": "Writing"},
    {"name": "Typefully", "url": "https://typefully.com", "cat": "Social Media"},
    {"name": "Brandmark", "url": "https://brandmark.io", "cat": "Logo Design"}
]

# 3. HELPER: SLUG GENERATOR
def create_slug(name):
    slug = re.sub(r'[^\w\s-]', '', name).strip().lower()
    return re.sub(r'[-\s]+', '-', slug)

# 4. SEO-ADVANCED CONTENT GENERATOR
def generate_seo_content(tool_name, category):
    prompt = f"""
    Write a high-quality, professional SEO review for the tool '{tool_name}' in the '{category}' category.
    Google loves structured data, so strictly follow this format:

    [Introduction: 3 paragraphs on what is {tool_name}, its main purpose, and who should use it.]

    ## Key Features
    - [Detail 5 major features with explanations]

    ## Pros & Cons
    ### Pros
    - [2 key strengths]
    ### Cons
    - [2 minor drawbacks]

    ## Frequently Asked Questions
    **Q1: Is {tool_name} free to use?**
    A1: [Explain pricing/free tier]
    **Q2: What is the best alternative to {tool_name}?**
    A2: [Suggest 1 competitor]
    **Q3: Is it suitable for beginners?**
    A3: [Answer]
    """
    
    # Retry logic if API fails
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating content (Attempt {attempt+1}): {e}")
            time.sleep(5)
    return "Review content currently being updated."

# 5. BULK PROCESSING LOGIC
def bulk_process():
    for tool in AI_TOOLS_LIST:
        slug = create_slug(tool["name"])
        
        # Check if tool already exists in database
        exists = supabase.table("ai_tools").select("id").eq("slug", slug).execute()
        if exists.data:
            print(f"Skipping {tool['name']}, already exists.")
            continue

        print(f"Generating Advanced SEO review for {tool['name']}...")
        content = generate_seo_content(tool["name"], tool["cat"])
        
        # Insert into Supabase
        try:
            supabase.table("ai_tools").insert({
                "name": tool["name"],
                "slug": slug,
                "category": tool["cat"],
                "description": content,
                "website_url": tool["url"],
                "affiliate_url": tool["url"], # Replace with your link later
                "is_sponsored": False
            }).execute()
            print(f"Success: {tool['name']} added to Vault.")
        except Exception as e:
            print(f"Database error for {tool['name']}: {e}")
        
        time.sleep(2) # Prevent rate limiting

@app.get("/")
def home():
    return {"status": "AIVault SEO Engine v2.0 is Online"}

@app.get("/start-bulk")
def start_automation(background_tasks: BackgroundTasks):
    background_tasks.add_task(bulk_process)
    return {
        "message": "Automation Started!",
        "count": len(AI_TOOLS_LIST),
        "target": "Google First Page"
    }
