import os
import logging
import re
import requests
from bs4 import BeautifulSoup
import googleapiclient.discovery
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler

# تكوين التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توكن البوت - يجب استبداله بالتوكن الخاص بك
TOKEN = "TELEGRAM_BOT_TOKEN"

# مفتاح API لـ YouTube - يجب استبداله بالمفتاح الخاص بك
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"

# حالات المحادثة
SEARCHING = 1

# قائمة المواقع للبحث
DZEXAMS_URL = "https://www.dzexams.com"
EDDIRASA_URL = "https://www.eddirasa.com"

# المصطلحات العلمية والدروس
SCIENTIFIC_TERMS = [
    "التنمية المستدامة", "الثورة الصناعية", "الكتلة الحيوية", "التوازن البيئي", 
    "الاحتباس الحراري", "النهضة الأوروبية", "الحرب الباردة", "الاستعمار", 
    "العولمة", "الانقراض", "الدورة الدموية", "التحليل الكهربائي", 
    "المعادلة الكيميائية", "الطاقة الحركية", "المتتاليات العددية", 
    "المثلثات المتشابهة", "الاستعارة", "الطباق", "الاستدلال", "البرهنة بالتراجع"
]

# عناوين الدروس حسب المواد
SUBJECTS_LESSONS = {
    "التاريخ": [
        "الاحتلال الفرنسي للجزائر والكفاح من أجل الاستقلال",
        "المقاومة الوطنية 1830-1954",
        "الحركة الوطنية الجزائرية",
        "الثورة التحريرية الكبرى 1954-1962",
        "الجزائر المستقلة وبناء الدولة الحديثة"
    ],
    "الجغرافيا": [
        "الجزائر الموقع والخصائص الطبيعية",
        "الموارد الطبيعية في الجزائر",
        "السكان في الجزائر",
        "المدن والنشاطات الاقتصادية في الجزائر",
        "التنمية في الجزائر"
    ],
    "التربية المدنية": [
        "المجتمع الجزائري",
        "الحقوق والواجبات",
        "الدولة الجزائرية",
        "المؤسسات الدستورية",
        "المواطنة"
    ],
    "العلوم الفيزيائية": [
        "المقاربة الكمية لتحول كيميائي",
        "التحليل الكهربائي",
        "الظواهر الكهربائية",
        "الميكانيك",
        "الطاقة وتحولاتها"
    ],
    "علوم الطبيعة والحياة": [
        "التغذية عند الإنسان",
        "الدورة الدموية",
        "التنفس",
        "الإخراج",
        "التكاثر عند الإنسان"
    ],
    "الرياضيات": [
        "الأعداد والحساب",
        "الجبر",
        "الهندسة",
        "الإحصاء",
        "الاحتمالات"
    ],
    "اللغة العربية": [
        "النصوص الأدبية",
        "القواعد النحوية",
        "البلاغة",
        "التعبير الكتابي",
        "العروض"
    ],
    "اللغة الفرنسية": [
        "Compréhension de l'écrit",
        "Expression écrite",
        "Grammaire",
        "Vocabulaire",
        "Orthographe"
    ],
    "اللغة الإنجليزية": [
        "Reading Comprehension",
        "Writing",
        "Grammar",
        "Vocabulary",
        "Listening Comprehension"
    ],
    "التربية الإسلامية": [
        "العقيدة الإسلامية",
        "العبادات",
        "الأخلاق الإسلامية",
        "السيرة النبوية",
        "المعاملات في الإسلام"
    ],
    "الإعلام الآلي": [
        "مكونات الحاسوب",
        "نظم التشغيل",
        "معالجة النصوص",
        "الجداول الإلكترونية",
        "الإنترنت"
    ],
    "التربية الفنية": [
        "التصميم",
        "الرسم",
        "النحت",
        "الخط العربي",
        "التذوق الفني"
    ],
    "التربية الموسيقية": [
        "المقامات الموسيقية",
        "الإيقاع",
        "الآلات الموسيقية",
        "الأنماط الموسيقية",
        "التذوق الموسيقي"
    ]
}

# تجميع كل الدروس في قائمة واحدة للبحث
ALL_LESSONS = []
for subject, lessons in SUBJECTS_LESSONS.items():
    ALL_LESSONS.extend(lessons)

# وظائف مساعدة

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة عند تشغيل الأمر /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"مرحباً {user.first_name}! أنا البوت التعليمي 'edo' للسنة الرابعة متوسط 🤖\n\n"
        "يمكنك استخدام الأوامر التالية:\n"
        "/who - من أنت\n"
        "/creator - المطور\n"
        "/job - وظيفتي\n"
        "/reset - إعادة تعيين\n"
        "/search - بحث في المنهاج\n\n"
        "أو يمكنك أن تسألني مباشرة عن أي موضوع في منهاج السنة الرابعة متوسط! ✨"
    )

async def who_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر who"""
    await update.message.reply_text(
        "أنا 'edo'، بوت ذكاء اصطناعي يساعدك في البحث السريع عن المعلومات التعليمية للسنة الرابعة متوسط. 🤖📚"
    )

async def creator_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر creator"""
    await update.message.reply_text(
        "تم تصميمي بواسطة Aymen dj max. يمكنك زيارة موقعه على الرابط التالي: adm-web.ct.ws 💻👨‍💻"
    )

async def job_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر job"""
    await update.message.reply_text(
        "وظيفتي هي مساعدتك في الدراسة والإجابة على أسئلتك المتعلقة بالمنهاج الدراسي للسنة الرابعة متوسط الجزائرية. "
        "أستطيع البحث عن نماذج الفروض والاختبارات، وتقديم الملخصات والقوانين، وإيجاد الفيديوهات التعليمية! 📚🧠"
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إعادة تعيين المحادثة"""
    # مسح بيانات المحادثة
    if 'user_data' in context.user_data:
        context.user_data.clear()
    
    await update.message.reply_text("تم إعادة تعيين بيانات المحادثة بنجاح! ✅")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء عملية البحث في المنهاج"""
    await update.message.reply_text(
        "ما هو الموضوع الذي تبحث عنه في منهاج السنة الرابعة متوسط؟ 🔍\n"
        "اكتب سؤالك أو موضوعك بالتفصيل للحصول على أفضل النتائج."
    )
    return SEARCHING

async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة استعلام البحث"""
    query = update.message.text
    
    # إرسال رسالة "جاري البحث..."
    processing_message = await update.message.reply_text("جاري البحث... ⏳")
    
    # البحث في المصادر المختلفة
    result = await search_query(query)
    
    # حذف رسالة "جاري البحث..."
    await processing_message.delete()
    
    # إرسال النتيجة
    if result:
        await update.message.reply_text(result, disable_web_page_preview=False)
    else:
        await update.message.reply_text(
            "عذراً، لم أتمكن من العثور على معلومات حول هذا الموضوع. 😕\n"
            "تأكد من أن سؤالك يتعلق بمنهاج السنة الرابعة متوسط الجزائرية أو حاول صياغة السؤال بطريقة مختلفة."
        )
    
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الرسائل العادية"""
    text = update.message.text
    
    # إرسال رسالة "جاري البحث..."
    processing_message = await update.message.reply_text("جاري البحث... ⏳")
    
    # البحث في المصادر المختلفة
    result = await search_query(text)
    
    # حذف رسالة "جاري البحث..."
    await processing_message.delete()
    
    # إرسال النتيجة
    if result:
        await update.message.reply_text(result, disable_web_page_preview=False)
    else:
        subjects_list = ", ".join(list(SUBJECTS_LESSONS.keys()))
        await update.message.reply_text(
            f"عذراً، لم أتمكن من العثور على معلومات حول هذا الموضوع. 😕\n"
            f"أنا متخصص فقط في المنهاج الدراسي للسنة الرابعة متوسط الجزائرية في المواد التالية:\n"
            f"{subjects_list}\n\n"
            "يمكنك محاولة صياغة سؤالك بطريقة مختلفة أو استخدام أمر /search للبحث المتخصص."
        )

async def search_query(query: str) -> str:
    """البحث عن استعلام في المصادر المختلفة"""
    # تحليل الاستعلام
    query_lower = query.lower()
    
    # التحقق مما إذا كان الاستعلام يتعلق بالفيديو
    if any(keyword in query_lower for keyword in ["فيديو", "يوتيوب", "youtube", "شرح", "فيديوهات"]):
        return await search_youtube(query)
    
    # التحقق مما إذا كان الاستعلام يتعلق بنماذج الفروض والاختبارات
    if any(keyword in query_lower for keyword in ["فرض", "اختبار", "نموذج", "امتحان", "bem", "نماذج", "حلول", "تمارين"]):
        dzexams_result = await search_dzexams(query)
        if dzexams_result:
            return dzexams_result
    
    # البحث في موقع eddirasa
    eddirasa_result = await search_eddirasa(query)
    if eddirasa_result:
        return eddirasa_result
    
    # إذا لم يتم العثور على نتائج، التحقق من المصطلحات العلمية والدروس
    for term in SCIENTIFIC_TERMS + ALL_LESSONS:
        if term.lower() in query_lower or query_lower in term.lower():
            # محاولة البحث في المصادر الأخرى
            combined_query = f"{term} السنة الرابعة متوسط"
            dzexams_result = await search_dzexams(combined_query)
            if dzexams_result:
                return dzexams_result
                
            eddirasa_result = await search_eddirasa(combined_query)
            if eddirasa_result:
                return eddirasa_result
                
            youtube_result = await search_youtube(combined_query)
            if youtube_result:
                return youtube_result
    
    # إذا لم يتم العثور على أي نتائج
    return None

async def search_dzexams(query: str) -> str:
    """البحث في موقع DzExams"""
    try:
        search_url = f"{DZEXAMS_URL}/search?q={query.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن النتائج
        results = soup.find_all("div", class_="result-item")
        
        if not results or len(results) == 0:
            return None
            
        # استخراج أول 3 نتائج
        result_text = "نتائج البحث من DzExams 📝:\n\n"
        
        for i, result in enumerate(results[:3], 1):
            title_element = result.find("h3", class_="title")
            link_element = title_element.find("a") if title_element else None
            
            if title_element and link_element:
                title = title_element.text.strip()
                link = link_element.get("href")
                if not link.startswith("http"):
                    link = f"{DZEXAMS_URL}{link}"
                
                result_text += f"{i}. {title}\n{link}\n\n"
        
        return result_text
    except Exception as e:
        logger.error(f"خطأ في البحث في DzExams: {e}")
        return None

async def search_eddirasa(query: str) -> str:
    """البحث في موقع Eddirasa"""
    try:
        search_url = f"{EDDIRASA_URL}/search?q={query.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن النتائج
        results = soup.find_all("div", class_="search-result")
        
        if not results or len(results) == 0:
            return None
            
        # استخراج أول 3 نتائج
        result_text = "نتائج البحث من Eddirasa 📚:\n\n"
        
        for i, result in enumerate(results[:3], 1):
            title_element = result.find("h3", class_="result-title")
            link_element = title_element.find("a") if title_element else None
            
            if title_element and link_element:
                title = title_element.text.strip()
                link = link_element.get("href")
                if not link.startswith("http"):
                    link = f"{EDDIRASA_URL}{link}"
                
                result_text += f"{i}. {title}\n{link}\n\n"
        
        return result_text
    except Exception as e:
        logger.error(f"خطأ في البحث في Eddirasa: {e}")
        return None

async def search_youtube(query: str) -> str:
    """البحث في يوتيوب"""
    try:
        # إضافة "السنة الرابعة متوسط" إلى الاستعلام إذا لم تكن موجودة
        if "السنة الرابعة متوسط" not in query and "4am" not in query.lower():
            query += " السنة الرابعة متوسط"
        
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY
        )
        
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=3,
            relevanceLanguage="ar"
        )
        
        response = request.execute()
        
        if not response.get("items"):
            return None
            
        result_text = "نتائج البحث من يوتيوب 📺:\n\n"
        
        for i, item in enumerate(response["items"], 1):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # الحصول على إحصائيات الفيديو للتحقق من عدد المشاهدات
            video_request = youtube.videos().list(
                part="statistics",
                id=video_id
            )
            
            video_response = video_request.execute()
            view_count = int(video_response["items"][0]["statistics"]["viewCount"])
            
            # إضافة الفيديو فقط إذا كان عدد المشاهدات أكثر من 1000
            if view_count >= 1000:
                result_text += f"{i}. {title}\nالقناة: {channel}\nعدد المشاهدات: {view_count:,}\n{video_url}\n\n"
        
        return result_text
    except Exception as e:
        logger.error(f"خطأ في البحث في يوتيوب: {e}")
        return None

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء المحادثة وإعادة تعيينها"""
    await update.message.reply_text("تم إلغاء البحث! 🚫")
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الأخطاء"""
    logger.error(f"حدث خطأ: {context.error}")

def main() -> None:
    """دالة التشغيل الرئيسية"""
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()

    # إضافة معالج المحادثة للبحث
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search_command)],
        states={
            SEARCHING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("who", who_command))
    application.add_handler(CommandHandler("creator", creator_command))
    application.add_handler(CommandHandler("job", job_command))
    application.add_handler(CommandHandler("reset", reset_command))
    
    # معالج الرسائل العادية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    application.run_polling()

# للحفاظ على تشغيل البوت 24/7 باستخدام Render
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    # إعداد webhook إذا كان يعمل على Render
    if 'RENDER' in os.environ:
        # استخدام webhook للحفاظ على التشغيل 24/7
        from telegram.ext import Updater
        
        webhook_url = os.environ.get('WEBHOOK_URL')
        
        if webhook_url:
            application = Application.builder().token(TOKEN).build()
            application.run_webhook(
                listen="0.0.0.0",
                port=port,
                url_path=TOKEN,
                webhook_url=webhook_url + TOKEN
            )
        else:
            main()
    else:
        # تشغيل البوت محلياً
        main()
