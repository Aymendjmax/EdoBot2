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
MIN_VIEWS = 1000  # أقل عدد مشاهدات مقبول لليوتيوب

# ------ فلترة النتائج غير الدراسية ------
BLACKLIST = ["ترفيه", "أغاني", "رياضة", "سياسة", "كورة", "موسيقى"]

# =================================================================
#                          وظائف البحث                          
# =================================================================

async def search_dzexams(query: str) -> str:
    """البحث في موقع DzExams مع فلترة النتائج"""
    try:
        search_url = f"{DZEXAMS_URL}/search?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
            
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for item in soup.select(".result-item"):
            title = item.select_one(".title").text.strip()
            link = item.select_one("a")["href"]
            if not link.startswith("http"):
                link = f"{DZEXAMS_URL}{link}"
                
            if not any(word in title.lower() for word in BLACKLIST):
                results.append(f"• {title}\n🔗 {link}")
        
        return "📚 نتائج DzExams:\n\n" + "\n\n".join(results[:3]) if results else None
        
    except Exception as e:
        logger.error(f"خطأ في DzExams: {e}")
        return None

async def search_eddirasa(query: str) -> str:
    """البحث في موقع Eddirasa مع فلترة النتائج"""
    try:
        search_url = f"{EDDIRASA_URL}/search?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
            
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for item in soup.select(".search-result"):
            title = item.select_one(".result-title").text.strip()
            link = item.select_one("a")["href"]
            if not link.startswith("http"):
                link = f"{EDDIRASA_URL}{link}"
                
            if not any(word in title.lower() for word in BLACKLIST):
                results.append(f"• {title}\n🔗 {link}")
        
        return "📝 نتائج Eddirasa:\n\n" + "\n\n".join(results[:3]) if results else None
        
    except Exception as e:
        logger.error(f"خطأ في Eddirasa: {e}")
        return None

async def search_youtube(query: str) -> str:
    """البحث في يوتيوب مع فلترة المشاهدات والمحتوى"""
    try:
        if "السنة الرابعة متوسط" not in query.lower() and "4am" not in query.lower():
            query += " السنة الرابعة متوسط"
        
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY
        )
        
        search_response = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=5,
            relevanceLanguage="ar",
            regionCode="DZ"
        ).execute()
        
        results = []
        for item in search_response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            
            stats = youtube.videos().list(
                part="statistics",
                id=video_id
            ).execute()
            
            view_count = int(stats["items"][0]["statistics"].get("viewCount", 0))
            
            if (view_count >= MIN_VIEWS and 
                not any(word in title.lower() for word in BLACKLIST)):
                url = f"https://youtu.be/{video_id}"
                channel = item["snippet"]["channelTitle"]
                results.append(
                    f"▶️ {title}\n"
                    f"👤 {channel}\n"
                    f"👁️ {view_count:,} مشاهدة\n"
                    f"🔗 {url}"
                )
        
        return "🎬 نتائج يوتيوب:\n\n" + "\n\n".join(results[:3]) if results else None
        
    except Exception as e:
        logger.error(f"خطأ في يوتيوب: {e}")
        return None

# =================================================================
#                          أوامر البوت                          
# =================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"مرحباً {user.first_name}! 👋\n"
        "أنا بوت البحث التعليمي للسنة الرابعة متوسط\n\n"
        "📌 الأوامر المتاحة:\n"
        "/who - من أنا؟\n"
        "/creator - المطور\n"
        "/job - وظيفتي\n"
        "/reset - إعادة تعيين\n"
        "/search - بحث في المنهج"
    )

async def who_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /who"""
    await update.message.reply_text(
        "🤖 أنا بوت تعليمي ذكي مصمم لمساعدة طلاب السنة الرابعة متوسط في:\n"
        "- البحث عن الدروس والنماذج\n"
        "- إيجاد شروحات فيديو\n"
        "- توفير مصادر تعليمية موثوقة"
    )

async def creator_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /creator"""
    await update.message.reply_text(
        "👨‍💻 المطور: Aymen DJ Max\n"
        "🌐 الموقع: adm-web.ct.ws\n"
    )

async def job_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /job"""
    await update.message.reply_text(
        "📚 وظيفتي الرئيسية:\n"
        "1. البحث عن الدروس والنماذج الامتحانية\n"
        "2. توفير شروحات فيديو عالية الجودة\n"
        "3. مساعدتك في فهم المنهج الدراسي\n"
        "4. تصفية النتائج غير التعليمية تلقائياً"
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /reset"""
    if 'user_data' in context.user_data:
        context.user_data.clear()
    await update.message.reply_text(
        "♻️ تم إعادة تعيين البوت بنجاح\n"
        "جميع البيانات المؤقتة تم مسحها"
    )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء عملية البحث"""
    await update.message.reply_text(
        "🔍 أرسل موضوع البحث (درس، نموذج، سؤال):\n"
        "مثال: 'تحليل معادلة رياضية' أو 'نموذج امتحان علوم'"
    )
    return 1

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة طلب البحث"""
    query = update.message.text
    await update.message.reply_text(f"⏳ جاري البحث عن: {query}")
    
    # البحث في جميع المصادر
    sources = {
        "DzExams": search_dzexams,
        "Eddirasa": search_eddirasa,
        "YouTube": search_youtube
    }
    
    results = []
    for name, func in sources.items():
        try:
            result = await func(query)
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"خطأ في {name}: {e}")
    
    # إرسال النتائج
    if results:
        response = "\n\n".join(results)
        # تقطيع الرسالة إذا كانت طويلة
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(
            "⚠️ لم أجد نتائج مناسبة\n"
            "حاول:\n"
            "- تغيير كلمات البحث\n"
            "- التأكد من صيغة الطلب\n"
            "- استخدام مصطلحات من المنهج"
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء البحث"""
    await update.message.reply_text("تم إلغاء عملية البحث")
    return ConversationHandler.END

# =================================================================
#                         التشغيل الرئيسي                        
# =================================================================

def main():
    """إعداد وتشغيل البوت"""
    app = Application.builder().token(TOKEN).build()
    
    # محادثة البحث
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search_command)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=120
    )
    
    # تسجيل الأوامر
    commands = [
        ("start", start),
        ("who", who_command),
        ("creator", creator_command),
        ("job", job_command),
        ("reset", reset_command)
    ]
    
    for cmd, func in commands:
        app.add_handler(CommandHandler(cmd, func))
    
    app.add_handler(conv_handler)
    
    # معالجة الرسائل العادية
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        lambda update, ctx: update.message.reply_text("استخدم /search للبحث")
    ))
    
    # تشغيل البوت
    if os.getenv('RENDER'):
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
            drop_pending_updates=True
        )
        logger.info("✅ البوت يعمل على Render (Webhook)")
    else:
        app.run_polling()
        logger.info("✅ البوت يعمل محلياً (Polling)")

if __name__ == "__main__":
    main()
