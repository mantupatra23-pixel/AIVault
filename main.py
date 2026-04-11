import os
import time
import re
import requests
import feedparser
from fastapi import FastAPI, BackgroundTasks
from supabase import create_client, Client
import groq

app = FastAPI()

# --- 1. CONFIGURATION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY") # NEW: For Newsletters
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = groq.Client(api_key=GROQ_API_KEY)

# --- 2. ADVANCED HELPERS ---
def create_slug(name):
    # Smart Cleanup: Remove emojis and extra tags from Product Hunt titles
    clean_name = re.sub(r'[^\x00-\x7F]+', '', name) 
    slug = re.sub(r"[^\w\s-]", "", clean_name).strip().lower()
    return re.sub(r"[-\s]+", "-", slug)

def get_related_tools(category):
    """SEO Booster: Dhoondho related tools internal linking ke liye"""
    try:
        res = supabase.table("ai_tools").select("name, slug").eq("category", category).limit(2).execute()
        if res.data:
            return ", ".join([f"{item['name']} (https://ai-vault-frontend-blue.vercel.app/tool/{item['slug']})" for item in res.data])
    except: pass
    return "our AI directory"

def send_newsletter(tool_list):
    """Auto-Email Digest: Subscribers ko update bhejo"""
    if not RESEND_API_KEY: return
    
    html_content = f"<h1>Today's Top 10 AI Tools</h1><ul>"
    for t in tool_list:
        html_content += f"<li><a href='https://ai-vault-frontend-blue.vercel.app/tool/{t['slug']}'>{t['name']}</a> - {t['category']}</li>"
    html_content += "</ul><p>Check all at AIVault.</p>"

    try:
        requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={
                "from": "AIVault Updates <updates@yourdomain.com>",
                "to": "subscribers@example.com", # Aap database se emails fetch karke yahan loop chala sakte hain
                "subject": "🚀 10 New AI Tools Added to Vault",
                "html": html_content
            }
        )
    except: print("Newsletter Failed")

# --- 3. AI ENGINE (Model: Llama 3.3 + Internal Linking) ---
def generate_master_review(tool_name, tool_url, related_context):
    prompt = f"""
    Act as a Senior AI Tech Journalist & SEO Expert. Analyze '{tool_name}' from {tool_url}.
    
    Internal Linking Context: {related_context}
    (If relevant, mention these tools naturally in the content).

    Format Strictly:
    CATEGORY: [Standardize as: Chatbot/Image Gen/Video Gen/Coding/Productivity/Marketing]
    PRICING: [Free/Freemium/Paid]
    SEO_META: [150-char meta description]

    ## CONTENT ##
    [3 professional paragraphs with keywords and internal links]

    ## Pros & Cons
    Pros: [3] | Cons: [3]

    ## Frequently Asked Questions
    Q: [Question] A: [Answer]

    ## Mantu's Take (Hinglish)
    [2 lines in Hinglish]
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        return response.choices[0].message.content
    except: return None

# --- 4. THE 10-NEW-TOOLS AUTONOMOUS WORKFLOW ---
def process_vault_automation():
    print("🌐 Discovery Mode: Scanning for 10 FRESH tools...")
    feed = feedparser.parse("https://www.producthunt.com/feed")
    
    vaulted_this_run = []
    new_tools_found = 0
    target = 10

    for entry in feed.entries:
        if new_tools_found >= target: break
            
        name = entry.title
        slug = create_slug(name)
        
        check = supabase.table("ai_tools").select("id").eq("slug", slug).execute()
        if check.data: continue

        # Smart Tagging: Pehle category guess karo for linking
        # (Yahan hum default 'Productivity' bhej rahe hain for first fetch)
        related_links = get_related_tools("Productivity")
        
        print(f"🔥 Processing New Tool ({new_tools_found+1}/{target}): {name}")
        output = generate_master_review(name, entry.link, related_links)

        if output and "## CONTENT ##" in output:
            try:
                header = output.split("## CONTENT ##")[0]
                body = output.split("## CONTENT ##")[1]
                
                cat = re.search(r"CATEGORY:\s*(.*)", header).group(1).strip()
                price = re.search(r"PRICING:\s*(.*)", header).group(1).strip()
                meta = re.search(r"SEO_META:\s*(.*)", header).group(1).strip()
                
                desc = body.split("## Pros & Cons")[0].strip()
                pros_cons = body.split("## Pros & Cons")[1].split("##")[0].strip() if "## Pros & Cons" in body else ""
                faq = body.split("## Frequently Asked Questions")[1].split("##")[0].strip() if "## Frequently Asked Questions" in body else ""

                data = {
                    "name": name, "slug": slug, "category": cat,
                    "description": desc, "pros_cons": pros_cons, "faq": faq,
                    "meta_description": meta, "website_url": entry.link,
                    "image_url": f"https://www.google.com/s2/favicons?domain={entry.link.split('//')[-1].split('/')[0]}&sz=128",
                    "pricing": price
                }

                supabase.table("ai_tools").upsert(data, on_conflict="slug").execute()
                
                vaulted_this_run.append({"name": name, "slug": slug, "category": cat})
                new_tools_found += 1
                
                time.sleep(10) # Groq Protection
            except Exception as e: print(f"Error: {e}")

    if vaulted_this_run:
        # Newsletter blast after 10 tools are added
        send_newsletter(vaulted_this_run)
        send_telegram_update(f"📢 <b>BULK UPDATE:</b> {new_tools_found} new tools added to Vault today!")

# --- 5. API ENDPOINTS ---
@app.get("/auto-pilot")
def start_auto(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_vault_automation)
    return {"message": "10-Tool Discovery + Newsletter Automation Started."}

@app.get("/")
def health():
    return {"status": "Engine v7.0 Online"}
