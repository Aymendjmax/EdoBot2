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

# ------ ثوابت البحث ------
SEARCHING = 1
DZEXAMS_URL = "https://www.dzexams.com"
EDDIRASA_URL = "https://www.eddirasa.com"
MIN_VIEWS = 1000  # أقل عدد مشاهدات لليوتيوب

# ------ قوائم الفلترة ------
ALLOWED_SUBJECTS = [
    "رياضيات", "علوم", "فيزياء", "كيمياء",
    "لغة عربية", "لغة فرنسية", "لغة إنجليزية",
    "تاريخ", "جغرافيا", "تربية إسلامية", "إعلام آلي"
]

BANNED_WORDS = [
    "مسلسل", "فلم", "أغنية", "كرة", "رياضة",
    "سياسة", "جنس", "حب", "غرام", "شات"
]

# =================================================================
#                         وظائف البحث                          
# =================================================================
async def search_dzexams(query: str) -> str:
    """البحث في موقع DzExams"""
    try:
        search_url = f"{DZEXAMS_URL}/search?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for item in soup.select(".result-item")[:3]:
            title = item.select_one(".title").text.strip()
            link = item.select_one("a")["href"]
            if not link.startswith("http"):
                link = f"{DZEXAMS_URL}{link}"
            results.append(f"• {title}\n🔗 {link}")
        
        return "📚 نتائج DzExams:\n\n" + "\n\n".join(results) if results else None
        
    except Exception as e:
        logger.error(f"خطأ في DzExams: {e}")
        return None

async def search_eddirasa(query: str) -> str:
    """البحث في موقع Eddirasa"""
    try:
        search_url = f"{EDDIRASA_URL}/search?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for item in soup.select(".search-result")[:3]:
            title = item.select_one(".result-title").text.strip()
            link = item.select_one("a")["href"]
            if not link.startswith("http"):
                link = f"{EDDIRASA_URL}{link}"
            results.append(f"• {title}\n🔗 {link}")
        
        return "📝 نتائج Eddirasa:\n\n" + "\n\n".join(results) if results else None
        
    except Exception as e:
        logger.error(f"خطأ في Eddirasa: {e}")
        return None

async def search_youtube(query: str) -> str:
    """البحث في يوتيوب"""
    try:
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY
        )
        
        search_response = youtube.search().list(
            q=f"{query} السنة الرابعة متوسط",
            part="snippet",
            type="video",
            maxResults=3,
            relevanceLanguage="ar"
        ).execute()
        
        results = []
        for item in search_response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            stats = youtube.videos().list(part="statistics", id=video_id).execute()
            view_count = int(stats["items"][0]["statistics"]["viewCount"])
            
            if view_count >= MIN_VIEWS:
                url = f"https://youtu.be/{video_id}"
                results.append(f"▶️ {title}\n👁️ {view_count:,} مشاهدة\n🔗 {url}")
        
        return "🎥 نتائج يوتيوب:\n\n" + "\n\n".join(results) if results else None
        
    except Exception as e:
        logger.error(f"خطأ في يوتيوب: {e}")
        return None

# =================================================================
#                         أوامر البوت                          
# =================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /start"""
    await update.message.reply_text(
        "🎓 **مرحباً! أنا بوت المنهاج الدراسي**\n"
        "▫️ متخصص في **السنة الرابعة متوسط (الجيل الثاني)**\n\n"
        "📌 **الأوامر المتاحة:**\n"
        "/search - بحث في المنهج\n"
        "/who - تعريف بالبوت\n"
        "/creator - معلومات المطور\n"
        "/job - وظيفة البوت\n"
        "/reset - إعادة التعيين"
    )

async def who_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /who"""
    await update.message.reply_text(
        "🤖 **أنا بوت تعليمي ذكي**\n"
        "- الاسم: EduBot 4AM\n"
        "- الوظيفة: مساعدتك في البحث عن المواد الدراسية\n"
        "- المميزات:\n"
        "  ✓ بحث في الدروس والتمارين\n"
        "  ✓ فلترة المحتوى غير التعليمي\n"
        "  ✓ دعم متعدد المصادر"
    )

async def creator_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /creator"""
    await update.message.reply_text(
        "👨💻 **معلومات المطور:**\n"
        "- الاسم: Aymen DJ Max\n"
        "- الموقع: https://adm-web.ct.ws\n"
    )

async def job_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /job"""
    await update.message.reply_text(
        "📚 **وظائف البوت:**\n"
        "1. البحث في:\n"
        "   - موقع DzExams (نماذج الامتحانات)\n"
        "   - موقع Eddirasa (الدروس)\n"
        "   - يوتيوب (شروحات فيديو)\n"
        "2. فلترة النتائج غير الدراسية تلقائياً\n"
        "3. توفير روابط مباشرة للمصادر"
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /reset"""
    context.user_data.clear()
    await update.message.reply_text("🔄 تمت إعادة ضبط جميع الإعدادات!")

# =================================================================
#                         نظام البحث                          
# =================================================================
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء عملية البحث"""
    await update.message.reply_text(
        "🔍 أدخل موضوع البحث الدراسي:\n"
        "مثال: 'معادلات رياضية' أو 'ملخص درس التنفس'"
    )
    return SEARCHING

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة طلب البحث"""
    query = update.message.text
    
    # فلترة المحتوى غير المرغوب
    query_lower = query.lower()
    if any(word in query_lower for word in BANNED_WORDS):
        await update.message.reply_text("⛔ هذا السؤال غير مسموح به")
        return ConversationHandler.END
    
    if not any(subject in query_lower for subject in ALLOWED_SUBJECTS):
        await update.message.reply_text("⚠️ الرجاء استخدام مصطلحات من المنهج الدراسي")
        return ConversationHandler.END
    
    await update.message.reply_text("⏳ جاري البحث في المصادر التعليمية...")
    
    # جمع النتائج من جميع المصادر
    results = []
    for func in [search_dzexams, search_eddirasa, search_youtube]:
        try:
            result = await func(query)
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"خطأ في {func.__name__}: {e}")
    
    # إرسال النتائج
    if results:
        final_response = "\n\n".join(results)
        for i in range(0, len(final_response), 4096):
            await update.message.reply_text(final_response[i:i+4096])
    else:
        await update.message.reply_text("❌ لم يتم العثور على نتائج")
    
    return ConversationHandler.END

# =================================================================
#                         التشغيل الرئيسي                        
# =================================================================
def main():
    app = Application.builder().token(TOKEN).build()
    
    # تسجيل الأوامر
    commands = [
        ("start", start),
        ("who", who_command),
        ("creator", creator_command),
        ("job", job_command),
        ("reset", reset_command),
    ]
    
    for cmd, func in commands:
        app.add_handler(CommandHandler(cmd, func))
    
    # إعداد محادثة البحث
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("search", search_command)],
        states={SEARCHING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)]},
        fallbacks=[]
    ))
    
    # التشغيل
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
