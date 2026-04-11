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
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = groq.Client(api_key=GROQ_API_KEY)

# --- 2. CORE HELPERS (Must be defined before usage) ---
def send_telegram_update(message):
    """Bina kisi error ke Telegram alerts bhejta hai"""
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, data={
                "chat_id": TELEGRAM_CHAT_ID, 
                "text": message, 
                "parse_mode": "HTML"
            }, timeout=10)
        except Exception as e:
            print(f"⚠️ Telegram Notify Failed: {e}")

def create_slug(name):
    """Clean SEO-friendly slug generation"""
    clean_name = re.sub(r'[^\x00-\x7F]+', '', name) 
    slug = re.sub(r"[^\w\s-]", "", clean_name).strip().lower()
    return re.sub(r"[-\s]+", "-", slug)

def get_logo_url(domain):
    """Broken logo fix: Fallback to Google S2"""
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"

# --- 3. AI SEO ENGINE (Model: Llama 3.3 70B) ---
def generate_master_review(tool_name, tool_url):
    prompt = f"""
    Analyze '{tool_name}' from {tool_url}. Act as a Senior AI Tech Journalist.
    
    Format Strictly:
    CATEGORY: [Chatbot/Image Gen/Video Gen/Coding/Productivity/Marketing]
    PRICING: [Free/Freemium/Paid]
    SCORE: [Give a quality score 1-100]
    TAGS: [#AI, #Automation, #Tech]
    SEO_META: [150-char meta description]

    ## CONTENT ##
    [Write 3 professional paragraphs about the tool.]

    ## Pros & Cons
    Pros: [List 3 points]
    Cons: [List 3 points]

    ## Frequently Asked Questions
    Q: [Question]
    A: [Answer]
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

# --- 4. THE AUTONOMOUS WORKFLOW (10 NEW TOOLS) ---
def process_vault_automation():
    print("🌐 Discovery Mode: Scanning for 10 FRESH unique tools...")
    feed = feedparser.parse("https://www.producthunt.com/feed")
    
    new_tools_count = 0
    target_new = 10

    for entry in feed.entries:
        if new_tools_count >= target_new:
            break
            
        name = entry.title
        slug = create_slug(name)
        
        # Duplicate Check
        check = supabase.table("ai_tools").select("id").eq("slug", slug).execute()
        if check.data:
            print(f"⏩ Skipping {name}: Already in Vault")
            continue

        print(f"🔥 Found New Tool ({new_tools_count+1}/10): {name}")
        output = generate_master_review(name, entry.link)

        if output and "## CONTENT ##" in output:
            try:
                # Advanced Extraction
                header = output.split("## CONTENT ##")[0]
                body = output.split("## CONTENT ##")[1]
                
                cat = re.search(r"CATEGORY:\s*(.*)", header).group(1).strip()
                price = re.search(r"PRICING:\s*(.*)", header).group(1).strip()
                score = re.search(r"SCORE:\s*(\d+)", header).group(1).strip()
                tags = re.search(r"TAGS:\s*(.*)", header).group(1).strip()
                meta = re.search(r"SEO_META:\s*(.*)", header).group(1).strip()

                desc_part = body.split("## Pros & Cons")[0].strip()
                pros_cons = body.split("## Pros & Cons")[1].split("##")[0].strip() if "## Pros & Cons" in body else ""
                faq = body.split("## Frequently Asked Questions")[1].split("##")[0].strip() if "## Frequently Asked Questions" in body else ""

                domain = entry.link.split("//")[-1].split("/")[0]
                
                data = {
                    "name": name,
                    "slug": slug,
                    "category": cat,
                    "description": desc_part,
                    "pros_cons": pros_cons,
                    "faq": faq,
                    "meta_description": meta,
                    "website_url": entry.link,
                    "image_url": get_logo_url(domain),
                    "pricing": price,
                    "score": int(score),
                    "tags": tags
                }

                # Save to Supabase
                supabase.table("ai_tools").upsert(data, on_conflict="slug").execute()
                
                new_tools_count += 1
                
                # Telegram Alert (Using the helper defined above)
                tg_msg = f"🚀 <b>NEW TOOL VAULTED ({new_tools_count}/10)</b>\n\n<b>Name:</b> {name}\n<b>Category:</b> {cat}\n<b>Price:</b> {price}\n\n🔗 <a href='https://ai-vault-frontend-blue.vercel.app/tool/{slug}'>View Analysis</a>"
                send_telegram_update(tg_msg)
                
                print(f"✨ Successfully vaulted: {name}")
                time.sleep(5) # Groq rate limit protection

            except Exception as e:
                print(f"❌ Execution Error for {name}: {e}")

# --- 5. API ENDPOINTS ---
@app.get("/")
def health():
    return {"status": "AIVault Engine Online", "version": "9.0", "mode": "10-Fresh-Tools"}

@app.get("/auto-pilot")
def start_auto(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_vault_automation)
    return {"message": "Discovery started for 10 new unique tools. Telegram will notify upon success."}
