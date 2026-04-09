import requests
import time

# Aapka Render Backend URL
BACKEND_URL = "https://aivault-faqc.onrender.com/add-tool"

# Massive List of Popular AI Tools
tools_list = [
    {"name": "ChatGPT", "cat": "Chatbot", "url": "https://chatgpt.com"},
    {"name": "Claude AI", "cat": "Assistant", "url": "https://claude.ai"},
    {"name": "Midjourney", "cat": "Image Gen", "url": "https://midjourney.com"},
    {"name": "Perplexity", "cat": "Search", "url": "https://perplexity.ai"},
    {"name": "Jasper", "cat": "Writing", "url": "https://jasper.ai"},
    {"name": "Suno AI", "cat": "Music", "url": "https://suno.com"},
    {"name": "Luma Dream Machine", "cat": "Video Gen", "url": "https://lumalabs.ai"},
    {"name": "Leonardo AI", "cat": "Image Gen", "url": "https://leonardo.ai"},
    {"name": "Gamma", "cat": "Presentation", "url": "https://gamma.app"},
    {"name": "Relume", "cat": "Web Design", "url": "https://relume.io"},
    {"name": "CapCut Desktop", "cat": "Video Editor", "url": "https://capcut.com"},
    {"name": "Descript", "cat": "Podcast AI", "url": "https://descript.com"},
    {"name": "Fireflies AI", "cat": "Meeting Notes", "url": "https://fireflies.ai"},
    {"name": "HeyGen", "cat": "Avatar Video", "url": "https://heygen.com"},
    {"name": "Sora", "cat": "Video Gen", "url": "https://openai.com/sora"}
    # Aap isme aur bhi tools add kar sakte hain
]

print(f"🚀 Launching Bulk Upload for {len(tools_list)} tools...")

for tool in tools_list:
    params = {"name": tool["name"], "cat": tool["cat"], "url": tool["url"]}
    try:
        response = requests.get(BACKEND_URL, params=params)
        if response.status_code == 200:
            print(f"✅ Added: {tool['name']}")
        else:
            print(f"❌ Failed: {tool['name']}")
    except Exception as e:
        print(f"⚠️ Error: {e}")
    
    # 5 seconds wait taaki API block na ho
    time.sleep(5)

print("🎉 Process Complete! Check your website now.")
