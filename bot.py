#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تلقرام لتحميل الفيديوهات من منصات التواصل الاجتماعي
المطور: @oytc
"""

import os
import re
import logging
import tempfile
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import yt_dlp

# ─────────────────────────── الإعدادات ───────────────────────────
BOT_TOKEN = "7902360527:AAEPv-9WQNWeeWo9gUC3CtGjtFaUf5ahd48"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 ميقابايت (حد تلقرام)
DEVELOPER_INSTAGRAM = "@oytc"

# ─────────────────────────── السجلات ───────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─────────────────────────── الأنماط ───────────────────────────
URL_PATTERN = re.compile(
    r"https?://(?:www\.|m\.|vm\.|vt\.)?"
    r"(?:youtube\.com|youtu\.be|tiktok\.com|instagram\.com|"
    r"twitter\.com|x\.com|facebook\.com|fb\.watch|"
    r"reddit\.com|vimeo\.com|dailymotion\.com|"
    r"twitch\.tv|snapchat\.com|pinterest\.com|"
    r"linkedin\.com|tumblr\.com|soundcloud\.com|"
    r"bilibili\.com|nicovideo\.jp|"
    r"[a-zA-Z0-9\-]+\.[a-zA-Z]{2,})"
    r"[^\s]*"
)

# ─────────────────── المنصات المدعومة ───────────────────
SUPPORTED_PLATFORMS = {
    "youtube.com": "يوتيوب 🎬",
    "youtu.be": "يوتيوب 🎬",
    "tiktok.com": "تيك توك 🎵",
    "instagram.com": "إنستقرام 📸",
    "twitter.com": "تويتر/إكس 🐦",
    "x.com": "تويتر/إكس 🐦",
    "facebook.com": "فيسبوك 📘",
    "fb.watch": "فيسبوك 📘",
    "reddit.com": "ريديت 🔴",
    "vimeo.com": "فيميو 🎥",
    "dailymotion.com": "ديلي موشن ▶️",
    "twitch.tv": "تويتش 🟣",
    "snapchat.com": "سناب شات 👻",
    "pinterest.com": "بنترست 📌",
}


def get_platform_name(url: str) -> str:
    """استخراج اسم المنصة من الرابط"""
    for domain, name in SUPPORTED_PLATFORMS.items():
        if domain in url.lower():
            return name
    return "منصة مدعومة 🌐"


# ═══════════════════════════════════════════════════════════════
#                        أوامر البوت
# ═══════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر /start - رسالة ترحيبية"""
    user_name = update.effective_user.first_name or "صديقي"

    welcome_text = (
        f"مرحباً بك {user_name}! 👋\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎬 <b>بوت تحميل الفيديوهات</b>\n\n"
        f"أرسل لي رابط أي فيديو وسأحمّله لك فوراً! ⚡\n\n"
        f"📌 <b>المنصات المدعومة:</b>\n"
        f"├ 🎬 يوتيوب (YouTube)\n"
        f"├ 🎵 تيك توك (TikTok)\n"
        f"├ 📸 إنستقرام (Instagram)\n"
        f"├ 🐦 تويتر/إكس (Twitter/X)\n"
        f"├ 📘 فيسبوك (Facebook)\n"
        f"└ 🌐 ومنصات أخرى كثيرة!\n\n"
        f"📝 <b>طريقة الاستخدام:</b>\n"
        f"فقط انسخ رابط الفيديو وأرسله هنا 🔗\n\n"
        f"⚠️ <b>ملاحظة:</b> الحد الأقصى لحجم الفيديو 50 ميقابايت\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👨‍💻 <b>المطور:</b> <a href='https://instagram.com/oytc'>{DEVELOPER_INSTAGRAM}</a>"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "👨‍💻 حساب المطور",
                url="https://instagram.com/oytc",
            )
        ],
        [
            InlineKeyboardButton(
                "📌 المنصات المدعومة",
                callback_data="platforms",
            )
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        parse_mode="HTML",
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر /help - المساعدة"""
    help_text = (
        "📖 <b>المساعدة</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 أرسل رابط الفيديو مباشرة وسأحمّله لك\n"
        "🔹 يمكنك إرسال أكثر من رابط\n"
        "🔹 الحد الأقصى لحجم الفيديو: 50 ميقابايت\n\n"
        "📋 <b>الأوامر المتاحة:</b>\n"
        "├ /start - بدء البوت\n"
        "├ /help - المساعدة\n"
        "└ /platforms - المنصات المدعومة\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👨‍💻 <b>المطور:</b> <a href='https://instagram.com/oytc'>{DEVELOPER_INSTAGRAM}</a>"
    )
    await update.message.reply_text(
        help_text, parse_mode="HTML", disable_web_page_preview=True
    )


async def platforms_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر /platforms - عرض المنصات المدعومة"""
    platforms_text = (
        "🌐 <b>المنصات المدعومة</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎬 يوتيوب (YouTube)\n"
        "🎵 تيك توك (TikTok)\n"
        "📸 إنستقرام (Instagram)\n"
        "🐦 تويتر / إكس (Twitter/X)\n"
        "📘 فيسبوك (Facebook)\n"
        "🔴 ريديت (Reddit)\n"
        "🎥 فيميو (Vimeo)\n"
        "▶️ ديلي موشن (Dailymotion)\n"
        "🟣 تويتش (Twitch)\n"
        "👻 سناب شات (Snapchat)\n"
        "📌 بنترست (Pinterest)\n"
        "🌐 وأي منصة يدعمها yt-dlp!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📎 فقط أرسل الرابط وسأتكفّل بالباقي! 😉"
    )
    await update.message.reply_text(platforms_text, parse_mode="HTML")


# ═══════════════════════════════════════════════════════════════
#                     تحميل الفيديوهات
# ═══════════════════════════════════════════════════════════════

def download_video(url: str, output_dir: str) -> dict:
    """
    تحميل الفيديو باستخدام yt-dlp
    يرجع قاموس يحتوي على معلومات الفيديو ومسار الملف
    """
    output_template = os.path.join(output_dir, "%(title).50s.%(ext)s")

    ydl_opts = {
        "format": "best[filesize<50M]/best[ext=mp4]/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "extractaudio": False,
        "merge_output_format": "mp4",
        "socket_timeout": 30,
        "retries": 3,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        # البحث عن الملف المحمّل (قد يتغير الامتداد بعد الدمج)
        if not os.path.exists(filename):
            base = os.path.splitext(filename)[0]
            for ext in [".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv"]:
                candidate = base + ext
                if os.path.exists(candidate):
                    filename = candidate
                    break

        return {
            "title": info.get("title", "فيديو"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail"),
            "filepath": filename,
            "filesize": os.path.getsize(filename) if os.path.exists(filename) else 0,
            "uploader": info.get("uploader", "غير معروف"),
        }


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الروابط المرسلة من المستخدم"""
    message_text = update.message.text.strip()

    # البحث عن روابط في الرسالة
    urls = URL_PATTERN.findall(message_text)

    if not urls:
        await update.message.reply_text(
            "❌ لم أتمكن من العثور على رابط صالح.\n\n"
            "📎 أرسل رابط فيديو من أي منصة مدعومة.\n"
            "💡 اكتب /help للمساعدة.",
            parse_mode="HTML",
        )
        return

    for url in urls:
        await process_video_url(update, context, url)


async def process_video_url(
    update: Update, context: ContextTypes.DEFAULT_TYPE, url: str
) -> None:
    """معالجة رابط فيديو واحد"""
    platform = get_platform_name(url)

    # رسالة انتظار
    status_msg = await update.message.reply_text(
        f"⏳ جاري تحميل الفيديو من {platform}...\n"
        f"🔗 <code>{url[:60]}{'...' if len(url) > 60 else ''}</code>\n\n"
        f"⏱ يرجى الانتظار قليلاً...",
        parse_mode="HTML",
    )

    tmp_dir = None
    try:
        # إنشاء مجلد مؤقت
        tmp_dir = tempfile.mkdtemp(prefix="tgbot_")

        # تحميل الفيديو في thread منفصل
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, download_video, url, tmp_dir)

        filepath = result["filepath"]
        filesize = result["filesize"]
        title = result["title"]
        duration = result.get("duration", 0)

        # التحقق من وجود الملف
        if not os.path.exists(filepath):
            await status_msg.edit_text(
                "❌ حدث خطأ أثناء تحميل الفيديو.\n"
                "🔄 حاول مرة أخرى لاحقاً.",
                parse_mode="HTML",
            )
            return

        # التحقق من حجم الملف
        if filesize > MAX_FILE_SIZE:
            size_mb = filesize / (1024 * 1024)
            await status_msg.edit_text(
                f"⚠️ <b>الفيديو كبير جداً!</b>\n\n"
                f"📁 حجم الفيديو: <b>{size_mb:.1f} ميقابايت</b>\n"
                f"📏 الحد الأقصى: <b>50 ميقابايت</b>\n\n"
                f"💡 تلقرام لا يسمح بإرسال ملفات أكبر من 50 ميقابايت عبر البوت.\n"
                f"🔗 حاول اختيار فيديو أقصر أو بجودة أقل.",
                parse_mode="HTML",
            )
            return

        # تحديث رسالة الحالة
        await status_msg.edit_text(
            f"📤 جاري رفع الفيديو إلى تلقرام...\n"
            f"🎬 <b>{title[:40]}</b>",
            parse_mode="HTML",
        )

        # تنسيق المدة
        if duration:
            minutes, seconds = divmod(int(duration), 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "غير معروف"

        size_mb = filesize / (1024 * 1024)

        caption = (
            f"🎬 <b>{title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 المنصة: {platform}\n"
            f"⏱ المدة: {duration_str}\n"
            f"📁 الحجم: {size_mb:.1f} MB\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 تم التحميل بواسطة البوت\n"
            f"👨‍💻 المطور: {DEVELOPER_INSTAGRAM}"
        )

        # إرسال الفيديو
        with open(filepath, "rb") as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=caption,
                parse_mode="HTML",
                supports_streaming=True,
                read_timeout=120,
                write_timeout=120,
            )

        # حذف رسالة الانتظار
        await status_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        logger.error(f"خطأ في التحميل: {error_msg}")

        if "Private" in error_msg or "private" in error_msg:
            user_error = "🔒 هذا الفيديو خاص ولا يمكن تحميله."
        elif "unavailable" in error_msg.lower():
            user_error = "🚫 هذا الفيديو غير متاح أو تم حذفه."
        elif "copyright" in error_msg.lower():
            user_error = "©️ هذا الفيديو محمي بحقوق الطبع والنشر."
        elif "age" in error_msg.lower():
            user_error = "🔞 هذا الفيديو يتطلب تسجيل دخول (تقييد عمري)."
        elif "Unsupported URL" in error_msg:
            user_error = "❌ هذا الرابط غير مدعوم."
        else:
            user_error = "❌ لم أتمكن من تحميل هذا الفيديو."

        await status_msg.edit_text(
            f"{user_error}\n\n"
            f"💡 تأكد من أن الرابط صحيح وأن الفيديو متاح للعامة.\n"
            f"🔄 حاول مرة أخرى لاحقاً.",
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        await status_msg.edit_text(
            "❌ حدث خطأ غير متوقع أثناء المعالجة.\n\n"
            "🔄 حاول مرة أخرى لاحقاً.\n"
            "💡 إذا استمرت المشكلة، تواصل مع المطور.",
            parse_mode="HTML",
        )

    finally:
        # تنظيف الملفات المؤقتة
        if tmp_dir and os.path.exists(tmp_dir):
            for f in os.listdir(tmp_dir):
                try:
                    os.remove(os.path.join(tmp_dir, f))
                except OSError:
                    pass
            try:
                os.rmdir(tmp_dir)
            except OSError:
                pass


async def handle_non_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الرسائل التي لا تحتوي على روابط"""
    text = update.message.text or ""
    if text.startswith("/"):
        return  # تجاهل الأوامر غير المعروفة

    # التحقق مما إذا كانت الرسالة تحتوي على رابط
    if URL_PATTERN.search(text):
        await handle_url(update, context)
    else:
        await update.message.reply_text(
            "👋 أهلاً!\n\n"
            "📎 أرسل لي <b>رابط فيديو</b> من أي منصة تواصل اجتماعي "
            "وسأحمّله لك فوراً! ⚡\n\n"
            "💡 اكتب /help للمساعدة.",
            parse_mode="HTML",
        )


# ═══════════════════════════════════════════════════════════════
#                        معالجة الأخطاء
# ═══════════════════════════════════════════════════════════════

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الأخطاء العامة"""
    logger.error(f"خطأ: {context.error}")
    if update and isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "⚠️ حدث خطأ أثناء المعالجة.\n"
            "🔄 حاول مرة أخرى لاحقاً.",
            parse_mode="HTML",
        )


# ═══════════════════════════════════════════════════════════════
#                        تشغيل البوت
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    """تشغيل البوت"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🤖 بوت تحميل الفيديوهات - جاري التشغيل...")
    print(f"👨‍💻 المطور: {DEVELOPER_INSTAGRAM}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()

    # إضافة الأوامر
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("platforms", platforms_command))

    # معالجة الرسائل النصية (الروابط)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_url))

    # معالجة الأخطاء
    app.add_error_handler(error_handler)

    print("✅ البوت يعمل الآن! اضغط Ctrl+C للإيقاف.")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # تشغيل البوت
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
