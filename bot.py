import os
import logging
import requests
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
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 5000))

# ------ قوائم الفلترة الذكية ------
ALLOWED_SUBJECTS = [
    "رياضيات", "علوم", "فيزياء", "كيمياء",
    "لغة عربية", "لغة فرنسية", "لغة إنجليزية",
    "تاريخ", "جغرافيا", "تربية إسلامية", "إعلام آلي"
]

BANNED_WORDS = [
    "مسلسل", "فلم", "أغنية", "كرة", "رياضة", "سياسة",
    "جنس", "حب", "غرام", "شات", "تيك توك", "مشاهير"
]

# =================================================================
#                    فلترة الأسئلة (طبقة حماية مزدوجة)             
# =================================================================
def is_educational(query: str) -> bool:
    """فلترة ذكية للأسئلة غير الدراسية"""
    query_lower = query.lower()
    return (
        not any(word in query_lower for word in BANNED_WORDS) and 
        any(subject in query_lower for subject in ALLOWED_SUBJECTS
    )

# =================================================================
#                البحث باستخدام Mistral-7B (بدون API Key)          
# =================================================================
async def search_with_mistral(query: str) -> str:
    """استخدام نموذج Mistral المجاني بدون توكن"""
    if not is_educational(query):
        return "⚠️ هذا السؤال خارج نطاق المنهج الدراسي"
    
    try:
        API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
        payload = {
            "inputs": f"""<s>[INST] أنت معلم جزائري. أجب باختصار (<80 كلمة) مع التركيز على المنهج الرسمي للسنوات المتوسطة.
            السؤال: {query} 
            الجواب: [/INST]""",
            "parameters": {"max_new_tokens": 250}
        }
        
        response = requests.post(API_URL, json=payload, timeout=10)
        response.raise_for_status()
        answer = response.json()[0]['generated_text'].split('[/INST]')[-1].strip()
        
        return answer if is_educational(answer) else "⚠️ لا يمكن تقديم إجابة عن هذا السؤال"
    
    except Exception as e:
        logger.error(f"خطأ في البحث: {e}")
        return "⏳ جاري تحسين الخدمة. يرجى المحاولة لاحقاً."

# =================================================================
#                          أوامر البوت                          
# =================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /start"""
    await update.message.reply_text(
        "🎓 **مرحباً! أنا بوت المنهاج الدراسي المجاني**\n"
        "▫️ متخصص في **السنة الرابعة متوسط (الجيل الثاني)**\n"
        "▫️ أغطي جميع المواد الأساسية\n\n"
        "📌 **الأوامر المتاحة:**\n"
        "/search - بدء البحث\n"
        "/creator - معلومات المطور\n"
        "/who - تعريف بالبوت\n"
        "/job - كيفية الاستخدام\n"
        "/reset - إعادة الضبط"
    )

async def creator_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /creator"""
    creator_info = """
👨‍💻 **معلومات المطور:**
- الاسم: Aymen DJ Max
- الموقع: [adm-web.ct.ws](https://adm-web.ct.ws)
"""
    await update.message.reply_text(creator_info, disable_web_page_preview=True)

async def who_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /who"""
    await update.message.reply_text(
        "🤖 **أنا بوت تعليمي ذكي**\n"
        "▫️ مصمم خصيصاً لطلاب السنة الرابعة متوسط\n"
        "▫️ أقدم إجابات دقيقة من المنهج الرسمي\n"
        "▫️ أدعم جميع المواد الأساسية"
    )

async def job_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /job"""
    await update.message.reply_text(
        "📚 **وظيفتي:**\n"
        "1. البحث في المنهج الدراسي\n"
        "2. تقديم شروحات مختصرة\n"
        "3. حل المسائل الرياضية والعلمية\n"
        "4. تصفية المحتوى غير التعليمي تلقائياً"
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرد على أمر /reset"""
    if 'user_data' in context.user_data:
        context.user_data.clear()
    await update.message.reply_text("🔄 تمت إعادة ضبط البوت بنجاح")

# ... (بقية الدوال handle_search و search_command تبقى كما هي)

# =================================================================
#                         التشغيل الرئيسي                        
# =================================================================
def main():
    app = Application.builder().token(TOKEN).build()
    
    # تسجيل الأوامر
    commands = [
        ("start", start),
        ("creator", creator_command),  # <-- الأمر الجديد
        ("who", who_command),
        ("job", job_command),
        ("reset", reset_command),
    ]
    
    for cmd, func in commands:
        app.add_handler(CommandHandler(cmd, func))
    
    # إعداد محادثة البحث
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("search", search_command)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)]},
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
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
