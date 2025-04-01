import os
import logging
import requests
from bs4 import BeautifulSoup
import googleapiclient.discovery
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# ------ إعدادات أساسية ------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------ متغيرات البيئة ------
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 5000))

# ------ مصادر البحث ------
DZEXAMS_URL = "https://www.dzexams.com"
EDDIRASA_URL = "https://www.eddirasa.com"
MIN_VIEWS = 1000  # أقل عدد مشاهدات مقبول

# ------ فلترة النتائج غير الدراسية ------
BLACKLIST = ["ترفيه", "أغاني", "رياضة", "سياسة"]

# =================================================================
#                          وظائف البحث                          
# =================================================================

async def search_dzexams(query: str) -> str:
    """البحث في موقع DzExams"""
    try:
        search_url = f"{DZEXAMS_URL}/search?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for item in soup.select(".result-item"):
            title = item.select_one(".title").text.strip()
            link = item.select_one("a")["href"]
            if not link.startswith("http"):
                link = f"{DZEXAMS_URL}{link}"
                
            # فلترة النتائج غير الدراسية
            if not any(word in title.lower() for word in BLACKLIST):
                results.append(f"• {title}\n{link}")
        
        return "نتائج DzExams 📚:\n\n" + "\n\n".join(results[:3]) if results else None
        
    except Exception as e:
        logger.error(f"خطأ في DzExams: {e}")
        return None

async def search_eddirasa(query: str) -> str:
    """البحث في موقع Eddirasa"""
    try:
        search_url = f"{EDDIRASA_URL}/search?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for item in soup.select(".search-result"):
            title = item.select_one(".result-title").text.strip()
            link = item.select_one("a")["href"]
            if not link.startswith("http"):
                link = f"{EDDIRASA_URL}{link}"
                
            # فلترة النتائج غير الدراسية
            if not any(word in title.lower() for word in BLACKLIST):
                results.append(f"• {title}\n{link}")
        
        return "نتائج Eddirasa 📝:\n\n" + "\n\n".join(results[:3]) if results else None
        
    except Exception as e:
        logger.error(f"خطأ في Eddirasa: {e}")
        return None

async def search_youtube(query: str) -> str:
    """البحث في يوتيوب مع فلترة النتائج"""
    try:
        # إضافة "السنة الرابعة متوسط" إذا لم تكن موجودة
        if "السنة الرابعة متوسط" not in query and "4am" not in query.lower():
            query += " السنة الرابعة متوسط"
        
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY
        )
        
        # البحث عن الفيديوهات
        search_response = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=5,
            relevanceLanguage="ar"
        ).execute()
        
        results = []
        for item in search_response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            
            # الحصول على إحصائيات الفيديو
            stats = youtube.videos().list(
                part="statistics",
                id=video_id
            ).execute()
            
            view_count = int(stats["items"][0]["statistics"]["viewCount"])
            
            # الفلترة المزدوجة
            if (view_count >= MIN_VIEWS and 
                not any(word in title.lower() for word in BLACKLIST)):
                url = f"https://youtu.be/{video_id}"
                results.append(f"▫️ {title}\n👁️ {view_count} مشاهدة\n🔗 {url}")
        
        return "نتائج يوتيوب 📺:\n\n" + "\n\n".join(results[:3]) if results else None
        
    except Exception as e:
        logger.error(f"خطأ في يوتيوب: {e}")
        return None

# =================================================================
#                          أوامر البوت                          
# =================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "مرحباً! أنا بوت البحث التعليمي 🎓\n"
        "أرسل /search للبحث في المنهج الدراسي"
    )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🔍 اكتب موضوع البحث:")
    return 1

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.message.text
    await update.message.reply_text("⏳ جاري البحث...")
    
    # البحث في جميع المصادر
    results = []
    for func in [search_dzexams, search_eddirasa, search_youtube]:
        result = await func(query)
        if result:
            results.append(result)
    
    # إرسال النتائج
    if results:
        await update.message.reply_text("\n\n".join(results))
    else:
        await update.message.reply_text("⚠️ لم أجد نتائج مناسبة")
    
    return ConversationHandler.END

# =================================================================
#                         التشغيل الرئيسي                        
# =================================================================

def main():
    app = Application.builder().token(TOKEN).build()
    
    # محادثة البحث
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search_command)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)]},
        fallbacks=[]
    )
    
    # تسجيل الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    
    # تشغيل البوت
    if os.getenv('RENDER'):
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
            drop_pending_updates=True
        )
        logger.info("✅ البوت يعمل على Render!")
    else:
        app.run_polling()
        logger.info("✅ البوت يعمل محلياً!")

if __name__ == "__main__":
    main()
