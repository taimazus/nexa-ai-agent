import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Dict, Any, List, Optional

from agent.integrations.config_manager import ServicesConfigManager

logger = logging.getLogger("NexA.Integrations.Email")


class EmailService:
    """
    Production-grade Email Assistant Engine for NexA AI:
    - IMAP4_SSL: Securely fetches, categorizes (read vs unread), and identifies important emails.
    - Decodes Unicode/Persian subject headers, senders, and plain text message bodies.
    - Generates human-friendly Persian summaries optimized for text-to-speech voice readout.
    - SMTP_SSL / STARTTLS: Composes and sends emails in UTF-8.
    """

    def __init__(self, config_manager: Optional[ServicesConfigManager] = None):
        self.config_manager = config_manager or ServicesConfigManager()

    def _decode_mime_str(self, header_val: Optional[str]) -> str:
        """Decodes MIME encoded header strings (UTF-8, ISO, etc.) into clean Python strings."""
        if not header_val:
            return ""
        try:
            decoded_parts = decode_header(header_val)
            result = []
            for bytes_or_str, encoding in decoded_parts:
                if isinstance(bytes_or_str, bytes):
                    enc = encoding or "utf-8"
                    try:
                        result.append(bytes_or_str.decode(enc, errors="replace"))
                    except Exception:
                        result.append(bytes_or_str.decode("utf-8", errors="replace"))
                else:
                    result.append(str(bytes_or_str))
            return " ".join(result)
        except Exception as exc:
            logger.warning(f"Error decoding MIME header '{header_val}': {exc}")
            return str(header_val)

    def _extract_body_text(self, msg: email.message.Message) -> str:
        """Extracts plain text body from multipart or singlepart email message."""
        body_parts = []
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disp = str(part.get("Content-Disposition"))
                    if content_type == "text/plain" and "attachment" not in content_disp:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body_parts.append(payload.decode(charset, errors="replace"))
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    body_parts.append(payload.decode(charset, errors="replace"))
        except Exception as exc:
            logger.warning(f"Error extracting body text: {exc}")

        full_body = "\n".join(body_parts).strip()
        # Truncate if too long
        return full_body[:500] if full_body else "(بدون متن ساده)"

    def is_configured(self) -> bool:
        """Checks if email address and password are provided."""
        cfg = self.config_manager.get_email_config()
        return bool(cfg.get("email_address") and cfg.get("app_password"))

    def check_emails(
        self,
        folder: str = "INBOX",
        unread_only: bool = True,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Connects to the IMAP server, retrieves emails, categorizes unread/read,
        flags important ones based on smart keywords, and builds an auditory summary.
        """
        cfg = self.config_manager.get_email_config()
        email_addr = cfg.get("email_address", "")
        app_pwd = cfg.get("app_password", "")
        imap_server = cfg.get("imap_server", "imap.gmail.com")
        imap_port = cfg.get("imap_port", 993)
        important_kw = cfg.get("important_keywords", [])

        if not email_addr or not app_pwd:
            return {
                "success": False,
                "is_configured": False,
                "error": "تنظیمات ایمیل هنوز وارد نشده است.",
                "spoken_summary": (
                    "تنظیمات حساب ایمیل شما هنوز ذخیره نشده است. "
                    "لطفاً در پنجره تنظیمات یا در همین چت، آدرس ایمیل و کلمه عبور اختصاصی (App Password) خود را تعیین کنید تا بتوانم ایمیل‌ها را برایتان بخوانم."
                ),
                "guide": {
                    "provider": cfg.get("provider", "gmail"),
                    "current_email": email_addr,
                    "tip": "برای جیمیل، به امنیت حساب گوگل رفته و یک App Password با نام NexA بسازید."
                }
            }

        mail = None
        try:
            logger.info(f"Connecting to IMAP {imap_server}:{imap_port} for {email_addr}...")
            mail = imaplib.IMAP4_SSL(imap_server, int(imap_port))
            mail.login(email_addr, app_pwd)
            mail.select(folder, readonly=True)

            search_criterion = "UNSEEN" if unread_only else "ALL"
            status, response = mail.search(None, search_criterion)

            if status != "OK" or not response or not response[0]:
                return {
                    "success": True,
                    "is_configured": True,
                    "total_found": 0,
                    "unread_count": 0,
                    "important_count": 0,
                    "emails": [],
                    "spoken_summary": "هیچ ایمیل جدید یا خوانده‌نشده‌ای در صندوق ورودی شما وجود ندارد. صندوق ایمیل شما خلوت و به‌روز است! ✨"
                }

            email_ids = response[0].split()
            total_found = len(email_ids)
            # Pick latest emails
            target_ids = email_ids[-limit:]
            target_ids.reverse()

            fetched_emails: List[Dict[str, Any]] = []
            important_emails: List[Dict[str, Any]] = []
            regular_emails: List[Dict[str, Any]] = []

            for e_id in target_ids:
                fetch_res, data = mail.fetch(e_id, "(RFC822.HEADER FLAGS BODY.PEEK[TEXT])")
                if fetch_res != "OK" or not data:
                    continue

                raw_email = None
                flags_str = ""
                for part in data:
                    if isinstance(part, tuple):
                        raw_email = part[1]
                        if len(part) > 0 and isinstance(part[0], bytes):
                            flags_str = part[0].decode("utf-8", errors="ignore")

                if not raw_email:
                    continue

                msg = email.message_from_bytes(raw_email)
                subject = self._decode_mime_str(msg.get("Subject", "(بدون موضوع)"))
                sender = self._decode_mime_str(msg.get("From", "(فرستنده نامشخص)"))
                date_str = msg.get("Date", "")
                snippet = self._extract_body_text(msg)
                is_read = "\\Seen" in flags_str

                # Check importance
                is_important = any(
                    kw.lower() in subject.lower() or kw.lower() in sender.lower()
                    for kw in important_kw
                ) or "\\Flagged" in flags_str

                email_obj = {
                    "id": e_id.decode("utf-8", errors="ignore"),
                    "subject": subject,
                    "sender": sender,
                    "date": date_str,
                    "is_read": is_read,
                    "is_important": is_important,
                    "snippet": snippet[:180] + ("..." if len(snippet) > 180 else "")
                }

                fetched_emails.append(email_obj)
                if is_important:
                    important_emails.append(email_obj)
                else:
                    regular_emails.append(email_obj)

            # Build rich Persian spoken summary
            spoken_lines = []
            unread_count = sum(1 for e in fetched_emails if not e["is_read"])
            spoken_lines.append(f"شما {total_found} ایمیل در صندوق ورودی دارید که {unread_count} مورد از آن‌ها جدید و خوانده‌نشده است.")

            if important_emails:
                spoken_lines.append(f"از میان آن‌ها، {len(important_emails)} ایمیل بسیار مهم شناسایی شد:")
                for imp in important_emails[:3]:
                    spoken_lines.append(f"• از طرف «{imp['sender'][:35]}» با موضوع: «{imp['subject']}»")
            else:
                spoken_lines.append("ایمیل اضطراری یا بحرانی جدیدی یافت نشد.")

            spoken_summary = "\n".join(spoken_lines)

            return {
                "success": True,
                "is_configured": True,
                "total_found": total_found,
                "unread_count": unread_count,
                "important_count": len(important_emails),
                "spoken_summary": spoken_summary,
                "important_emails": important_emails,
                "regular_emails": regular_emails,
                "all_emails": fetched_emails
            }

        except imaplib.IMAP4.error as imap_err:
            logger.error(f"IMAP Auth error: {imap_err}")
            return {
                "success": False,
                "is_configured": True,
                "error": f"خطا در احراز هویت یا اتصال ایمیل: {str(imap_err)}",
                "spoken_summary": "متاسفانه امکان ورود به حساب ایمیل وجود نداشت. لطفاً نام کاربری و رمز عبور برنامه (App Password) را بررسی فرمایید."
            }
        except Exception as exc:
            logger.error(f"Error checking email: {exc}", exc_info=True)
            return {
                "success": False,
                "is_configured": True,
                "error": str(exc),
                "spoken_summary": f"در هنگام بررسی ایمیل‌ها خطایی رخ داد: {str(exc)}"
            }
        finally:
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except Exception:
                    pass

    def send_email(
        self,
        to_address: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Sends an email securely using SMTP with SSL or STARTTLS."""
        cfg = self.config_manager.get_email_config()
        email_addr = cfg.get("email_address", "")
        app_pwd = cfg.get("app_password", "")
        smtp_server = cfg.get("smtp_server", "smtp.gmail.com")
        smtp_port = cfg.get("smtp_port", 587)
        use_ssl = cfg.get("use_ssl", True)

        if not email_addr or not app_pwd:
            return {
                "success": False,
                "error": "حساب ایمیل تنظیم نشده است. ابتدا مشخصات ایمیل را وارد فرمایید."
            }

        try:
            msg = MIMEMultipart()
            msg["From"] = email_addr
            msg["To"] = to_address.strip()
            msg["Subject"] = subject.strip()

            msg.attach(MIMEText(body, "plain", "utf-8"))

            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()

            server.login(email_addr, app_pwd)
            server.sendmail(email_addr, [to_address.strip()], msg.as_string())
            server.quit()

            logger.info(f"Successfully sent email to '{to_address}' with subject '{subject}'")
            return {
                "success": True,
                "to": to_address,
                "subject": subject,
                "message": f"ایمیل با موضوع «{subject}» با موفقیت برای «{to_address}» ارسال شد."
            }
        except Exception as exc:
            logger.error(f"Error sending email: {exc}", exc_info=True)
            return {
                "success": False,
                "error": f"خطا در ارسال ایمیل: {str(exc)}"
            }
