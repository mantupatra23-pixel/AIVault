import os
import time
import re
from fastapi import FastAPI, BackgroundTasks
from supabase import create_client, Client
import groq

app = FastAPI()

# 1. API KEYS SETUP (Dono options check karega)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Clients Initialize
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = groq.Client(api_key=GROQ_API_KEY)

# 2. 50+ TOP AI TOOLS LIST
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
    {"name": "Adobe Firefly", "url": "https://adobe.com/firefly", "cat": "Image Gen"},
    {"name": "DALL-E 3", "url": "https://openai.com/dall-e-3", "cat": "Image Gen"},
    {"name": "Descript", "url": "https://descript.com", "cat": "Video Editor"},
    {"name": "Copy AI", "url": "https://copy.ai", "cat": "Marketing"},
    {"name": "Writesonic", "url": "https://writesonic.com", "cat": "Marketing"},
    {"name": "Quillbot", "url": "https://quillbot.com", "cat": "Writing"},
    {"name": "Pika Labs", "url": "https://pika.art", "cat": "Video Gen"},
    {"name": "Framer AI", "url": "https://framer.com", "cat": "Web Design"},
    {"name": "Synthesia", "url": "https://synthesia.io", "cat": "Video Gen"},
    {"name": "Kling AI", "url": "https://klingai.com", "cat": "Video Gen"},
    {"name": "Phind", "url": "https://phind.com", "cat": "Coding Search"},
    {"name": "Notion AI", "url": "https://notion.so/product/ai", "cat": "Writing"},
    {"name": "Brandmark", "url": "https://brandmark.io", "cat": "Logo Design"}
]

# 3. HELPER: SLUG GENERATOR
def create_slug(name):
    slug = re.sub(r'[^\w\s-]', '', name).strip().lower()
    return re.sub(r'[-\s]+', '-', slug)

# 4. SEO CONTENT GENERATOR WITH ERROR CATCHING
def generate_seo_content(tool_name, category):
    prompt = f"""
    Write a high-quality, professional SEO review for '{tool_name}' in category '{category}'.
    Strictly follow this structure:
    - 3 Paragraph detailed review.
    - ## Key Features (5 bullet points)
    - ## Pros & Cons (List form)
    - ## Frequently Asked Questions (3 Q&As)
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        # Agar content bahut chhota hai, toh matlab fail hua
        if len(content) < 200:
            return None
        return content
    except Exception as e:
        print(f"Groq API Error for {tool_name}: {e}")
        return None

# 5. AUTOMATION LOGIC
def bulk_process():
    for tool in AI_TOOLS_LIST:
        slug = create_slug(tool["name"])
        
        # Check if already exists (Avoid Duplicates)
        exists = supabase.table("ai_tools").select("id").eq("slug", slug).execute()
        if exists.data:
            print(f"Skipping {tool['name']}, already in Vault.")
            continue

        print(f"Processing: {tool['name']}...")
        content = generate_seo_content(tool["name"], tool["cat"])
        
        if content:
            supabase.table("ai_tools").insert({
                "name": tool["name"],
                "slug": slug,
                "category": tool["cat"],
                "description": content,
                "website_url": tool["url"],
                "affiliate_url": tool["url"]
            }).execute()
            print(f"Successfully added: {tool['name']}")
            time.sleep(2) # API Respect
        else:
            print(f"Failed to generate content for {tool['name']}. Skipping insert.")

@app.get("/")
def home():
    return {"status": "AIVault Engine Online", "version": "2.1"}

@app.get("/start-bulk")
def start_automation(background_tasks: BackgroundTasks):
    background_tasks.add_task(bulk_process)
    return {"message": "Final SEO automation started! Check Supabase in 5 mins."}
