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
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = groq.Client(api_key=GROQ_API_KEY)

# --- 2. ADVANCED HELPERS ---
def create_slug(name):
    slug = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "-", slug)

def get_logo_url(domain):
    """Smart Image Fallback: Clearbit se try karo, nahi toh Google Favicon"""
    clearbit_url = f"https://logo.clearbit.com/{domain}"
    try:
        response = requests.get(clearbit_url, timeout=5)
        if response.status_code == 200:
            return clearbit_url
    except:
        pass
    # Fallback to Google S2 Favicon Service
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"

def send_telegram_update(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"})
        except:
            print("Telegram Notify Failed")

def get_youtube_link(tool_name):
    query = f"{tool_name} AI tutorial hindi"
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

# --- 3. AI ENGINE (Model: Llama 3.3 70B + SEO Intelligence) ---
def generate_master_review(tool_name, tool_url):
    prompt = f"""
    Act as a Senior AI Tech Journalist & SEO Expert. Analyze '{tool_name}' from {tool_url}.
    
    Format Strictly:
    CATEGORY: [One of: Chatbot, Image Gen, Video Gen, Coding, Productivity, Marketing]
    PRICING: [Free, Freemium, or Paid]
    SEO_META: [Write a catchy 150-character meta description for Google Search]

    ## CONTENT ##
    [Write 3 professional paragraphs. Mention specific use cases for creators.]

    ## Key Features
    * [List 5 technical features]

    ## Pros & Cons
    Pros: [List 3] | Cons: [List 3]

    ## Mantu's Take (Hinglish)
    [Write 2 lines in Hinglish explaining why this is a must-use tool.]
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Groq Error: {e}")
        return None

# --- 4. THE AUTONOMOUS WORKFLOW ---
def process_vault_automation(manual_list=None):
    if not manual_list:
        print("🌐 Discovery Mode: Scanning Product Hunt Feed...")
        feed = feedparser.parse("https://www.producthunt.com/feed")
        tools = [{"name": e.title, "url": e.link} for e in feed.entries][:10]
    else:
        tools = manual_list

    for tool in tools:
        name = tool["name"]
        slug = create_slug(name)
        
        # Check if already exists to save Groq API credits
        check = supabase.table("ai_tools").select("id").eq("slug", slug).execute()
        if check.data:
            print(f"⏩ Skipping {name}: Already in Vault")
            continue

        print(f"🚀 Analyzing & SEO Optimizing: {name}")
        output = generate_master_review(name, tool["url"])

        if output and "## CONTENT ##" in output:
            try:
                header = output.split("## CONTENT ##")[0]
                content = output.split("## CONTENT ##")[1].strip()

                # Regex Extraction for Metadata
                cat = re.search(r"CATEGORY:\s*(.*)", header).group(1).strip()
                price = re.search(r"PRICING:\s*(.*)", header).group(1).strip()
                meta = re.search(r"SEO_META:\s*(.*)", header).group(1).strip()

                domain = tool["url"].split("//")[-1].split("/")[0]
                
                data = {
                    "name": name,
                    "slug": slug,
                    "category": cat,
                    "description": content,
                    "meta_description": meta, # NEW: For Google Ranking
                    "website_url": tool["url"],
                    "image_url": get_logo_url(domain), # NEW: Smart Fallback
                    "pricing": price,
                    "youtube_url": get_youtube_link(name)
                }

                # UPSERT Data
                supabase.table("ai_tools").upsert(data, on_conflict="slug").execute()

                # Notify via Telegram (Auto-Social Posting)
                tg_msg = f"<b>🚀 NEW AI TOOL VAULTED!</b>\n\n<b>Name:</b> {name}\n<b>Price:</b> {price}\n<b>SEO:</b> {meta}\n\n🔗 <a href='https://ai-vault-frontend-blue.vercel.app/tool/{slug}'>Check Full Analysis</a>"
                send_telegram_update(tg_msg)
                
                print(f"✨ Successfully vaulted: {name}")
                time.sleep(10) # Safety Delay

            except Exception as e:
                print(f"❌ Execution Error for {name}: {e}")

# --- 5. API ENDPOINTS ---
@app.get("/")
def health():
    return {"status": "AIVault Engine Online", "mode": "SEO-Optimized"}

@app.get("/auto-pilot")
def start_auto(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_vault_automation)
    return {"message": "AIVault SEO Bot started discovering tools..."}
