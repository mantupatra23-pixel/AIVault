import os
from fastapi import FastAPI
from groq import Groq
from supabase import create_client

app = FastAPI()

# Keys Render ke Environment Variables se aayengi
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
def home():
    return {"status": "AIVault Engine is Running"}

@app.get("/add-tool")
def add_tool(name: str, cat: str, url: str):
    slug = name.lower().replace(" ", "-")
    
    # AI se review likhwana
    prompt = f"Write a professional 300-word SEO review for '{name}' in '{cat}' category for AIVault."
    chat = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    review = chat.choices[0].message.content

    data = {
        "name": name, "slug": slug, "category": cat,
        "description": review, "website_url": url, "affiliate_url": url
    }
    
    supabase.table("ai_tools").insert(data).execute()
    return {"message": f"{name} added successfully!"}
