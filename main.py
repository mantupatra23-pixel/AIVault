import os
import time
import re
import requests
import feedparser
from fastapi import FastAPI, BackgroundTasks
from supabase import create_client, Client
import groq

app = FastAPI()

# --- 1. CONFIGURATION (Environment Variables) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") # Optional
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")     # Optional

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = groq.Client(api_key=GROQ_API_KEY)

# --- 2. ADVANCED HELPERS ---
def create_slug(name):
    slug = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "-", slug)

def send_telegram_update(message):
    """Naye tool ki khabar seedha aapke phone par"""
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def get_youtube_link(tool_name):
    """Automatic YouTube tutorial search link generator"""
    query = f"{tool_name} AI tutorial hindi"
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

# --- 3. AI ENGINE (Deep Research & SEO) ---
def generate_master_review(tool_name, tool_url):
    prompt = f"""
    Act as a Senior AI Tech Journalist. Analyze '{tool_name}' (URL: {tool_url}).
    Generate a full SEO review. 
    
    Format:
    CATEGORY: [Chatbot/Image Gen/Video Gen/Coding/Productivity]
    PRICING: [Free/Freemium/Paid]
    
    ## CONTENT ##
    [Write 3 professional paragraphs. Mention other AI tools like ChatGPT or Midjourney for internal linking context if relevant.]
    
    ## Key Features
    * [List 5 technical features]
    
    ## Pros & Cons
    Pros: [List 3] | Cons: [List 3]
    
    ## Mantu's Take (Hinglish)
    [Write 2 lines in Hinglish explaining the real value of this tool for Indians.]
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Groq Error: {e}")
        return None

# --- 4. THE AUTONOMOUS WORKFLOW ---
def process_vault_automation(manual_list=None):
    # Discovery Logic: Internet se naye tools dhoondhna
    if not manual_list:
        print("🌐 Discovery Mode: Scanning Product Hunt & RSS...")
        feed = feedparser.parse("https://www.producthunt.com/feed")
        tools = [{"name": e.title, "url": e.link} for e in feed.entries if "ai" in e.title.lower()][:10]
    else:
        tools = manual_list

    for tool in tools:
        name = tool["name"]
        slug = create_slug(name)
        
        # 1. Duplicate Check
        check = supabase.table("ai_tools").select("id").eq("slug", slug).execute()
        if check.data:
            continue
            
        print(f"🚀 Processing: {name}")
        output = generate_master_review(name, tool["url"])
        
        if output and "## CONTENT ##" in output:
            try:
                # 2. Extract AI Data
                parts = output.split("## CONTENT ##")
                header = parts[0]
                content = parts[1].strip()
                
                cat = re.search(r"CATEGORY:\s*(.*)", header).group(1).strip() if "CATEGORY" in header else "AI Tool"
                price = re.search(r"PRICING:\s*(.*)", header).group(1).strip() if "PRICING" in header else "Free"
                
                # 3. Smart Metadata
                domain = tool["url"].split("//")[-1].split("/")[0]
                logo = f"https://logo.clearbit.com/{domain}"
                yt_link = get_youtube_link(name)

                # 4. Save to Supabase
                supabase.table("ai_tools").insert({
                    "name": name,
                    "slug": slug,
                    "category": cat,
                    "description": content,
                    "website_url": tool["url"],
                    "image_url": logo,
                    "pricing": price, # Make sure to add this column in Supabase
                    "youtube_url": yt_link # Make sure to add this column in Supabase
                }).execute()
                
                # 5. Notify Owner
                send_telegram_update(f"✅ NEW TOOL ADDED!\nName: {name}\nCategory: {cat}\nPrice: {price}\nCheck: aivault.vercel.app/tool/{slug}")
                
                print(f"✨ Successfully vaulted: {name}")
                time.sleep(15) # Stay safe from rate limits
                
            except Exception as e:
                print(f"❌ Execution Error for {name}: {e}")

# --- 5. API ENDPOINTS ---
@app.get("/")
def health():
    return {"status": "AIVault Engine Online", "mode": "Autonomous", "version": "3.0"}

@app.get("/auto-pilot")
def start_auto(background_tasks: BackgroundTasks):
    """Har din naye tools khud dhoondhne ke liye"""
    background_tasks.add_task(process_vault_automation)
    return {"message": "AI Vault Bot is now discovering new tools..."}

@app.post("/add-bulk")
def add_bulk(background_tasks: BackgroundTasks, tools: list):
    """Apni custom list bhejkar process karne ke liye"""
    background_tasks.add_task(process_vault_automation, tools)
    return {"message": "Bulk processing started."}
