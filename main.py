import os
import time
from fastapi import FastAPI, BackgroundTasks
from groq import Groq
from supabase import create_client

app = FastAPI()

# Environment Variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 50+ Trending AI Tools List
TOOLS_LIST = [
    {"name": "ChatGPT", "cat": "AI Chatbot", "url": "https://chat.openai.com"},
    {"name": "Claude AI", "cat": "AI Assistant", "url": "https://claude.ai"},
    {"name": "Midjourney", "cat": "Image Gen", "url": "https://midjourney.com"},
    {"name": "Perplexity AI", "cat": "AI Search", "url": "https://perplexity.ai"},
    {"name": "Suno AI", "cat": "AI Music", "url": "https://suno.com"},
    {"name": "Leonardo AI", "cat": "AI Art", "url": "https://leonardo.ai"},
    {"name": "ElevenLabs", "cat": "AI Voice", "url": "https://elevenlabs.io"},
    {"name": "Gamma App", "cat": "Presentation", "url": "https://gamma.app"},
    {"name": "HeyGen", "cat": "AI Video", "url": "https://heygen.com"},
    {"name": "Luma Dream Machine", "cat": "Video Gen", "url": "https://lumalabs.ai"},
    {"name": "Jasper AI", "cat": "AI Writing", "url": "https://jasper.ai"},
    {"name": "Copy AI", "cat": "Marketing", "url": "https://copy.ai"},
    {"name": "Descript", "cat": "Video Editor", "url": "https://descript.com"},
    {"name": "Fireflies AI", "cat": "Transcription", "url": "https://fireflies.ai"},
    {"name": "Relume", "cat": "Web Design", "url": "https://relume.io"},
    {"name": "Sora", "cat": "Video Gen", "url": "https://openai.com/sora"},
    {"name": "Pika Labs", "cat": "Video Gen", "url": "https://pika.art"},
    {"name": "Runway Gen-3", "cat": "Video Gen", "url": "https://runwayml.com"},
    {"name": "Frammer AI", "cat": "Web Design", "url": "https://framer.com"},
    {"name": "Canva Magic", "cat": "Graphic Design", "url": "https://canva.com"}
]

def run_automation():
    print("Automation Started...")
    for tool in TOOLS_LIST:
        slug = tool["name"].lower().replace(" ", "-")
        
        # Check if already exists to avoid duplicates
        existing = supabase.table("ai_tools").select("id").eq("slug", slug).execute()
        if existing.data:
            continue

        try:
            prompt = f"Write a professional 300-word SEO review for '{tool['name']}' in category '{tool['cat']}'. Highlight its top features and benefits."
            chat = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            review = chat.choices[0].message.content

            data = {
                "name": tool["name"], "slug": slug, "category": tool["cat"],
                "description": review, "website_url": tool["url"], "affiliate_url": tool["url"]
            }
            supabase.table("ai_tools").insert(data).execute()
            print(f"✅ Added: {tool['name']}")
            time.sleep(5) # Rate limiting safe
        except Exception as e:
            print(f"❌ Error with {tool['name']}: {e}")

@app.get("/")
def home():
    return {"status": "AIVault Engine Online"}

@app.get("/start-bulk")
def start_bulk(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_automation)
    return {"message": "Automation started in background. Check your website in 10 minutes!"}
