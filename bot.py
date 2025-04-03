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

# ------ مصادر بديلة للبحث ------
EDUCATIONAL_SOURCES = {
    "دروس": [
        {"title": "شرح معادلات الدرجة الأولى", "url": "https://example.com/math"},
        {"title": "البناء الضوئي في النبات", "url": "https://example.com/science"}
    ],
    "نماذج": [
        {"title": "نموذج امتحان الرياضيات 2023", "url": "https://example.com/exam1"},
        {"title": "فرض علوم الفصل الثاني", "url": "https://example.com/exam2"}
    ]
}

# =================================================================
#                         وظائف البحث البديلة                    
# =================================================================
async def search_locally(query: str) -> str:
    """بحث في قاعدة البيانات المحلية عندما تفشل الخدمات الخارجية"""
    results = []
    query_lower = query.lower()
    
    for category, items in EDUCATIONAL_SOURCES.items():
        for item in items:
            if query_lower in item["title"].lower():
                results.append(f"• {item['title']}\n🔗 {item['url']}")
    
    if results:
        return "🔍 نتائج البحث:\n\n" + "\n\n".join(results[:3])
    else:
        return "⚠️ لم أجد نتائج. حاول صياغة السؤال بشكل آخر أو استخدم مصطلحات من المنهج."

# =================================================================
#                          أوامر البوت                          
# =================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎓 مرحباً! أنا بوت البحث التعليمي\n"
        "استخدم /search للبحث في المنهج الدراسي"
    )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "أدخل موضوع البحث:\n"
        "مثال: 'معادلات رياضية' أو 'البناء الضوئي'"
    )
    return 1

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.message.text
    await update.message.reply_text("⏳ جاري البحث...")
    
    # محاولة البحث الخارجي أولاً
    try:
        result = await search_with_mistral(query)  # يمكنك إضافة هذه الدالة لاحقاً
    except:
        result = await search_locally(query)  # البحث المحلي كبديل
    
    await update.message.reply_text(result)
    return ConversationHandler.END

# ... (بقية الأوامر creator, who, job, reset تبقى كما هي)

# =================================================================
#                         التشغيل الرئيسي                        
# =================================================================
def main():
    app = Application.builder().token(TOKEN).build()
    
    # إعداد الأوامر
    commands = [
        ("start", start),
        ("creator", lambda u,c: u.message.reply_text("المطور: Aymen DJ Max")),
        ("search", search_command),
        ("who", lambda u,c: u.message.reply_text("بوت تعليمي للصف الرابع متوسط")),
        ("job", lambda u,c: u.message.reply_text("وظيفتي: مساعدتك في الدراسة")),
        ("reset", lambda u,c: u.message.reply_text("تمت إعادة الضبط"))
    ]
    
    for cmd, func in commands:
        app.add_handler(CommandHandler(cmd, func))
    
    # إعداد محادثة البحث
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("search", search_command)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)]},
        fallbacks=[]
    ))
    
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
