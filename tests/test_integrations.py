import pytest
import json
from unittest.mock import MagicMock, patch
from pathlib import Path

from agent.integrations.config_manager import ServicesConfigManager, PRESET_SERVERS
from agent.integrations.email_client import EmailService
from agent.integrations.social_manager import SocialMediaManager
from agent.engine import AgentEngine
from agent.config import TOOL_DECLARATIONS


class TestServicesAndIntegrations:
    """
    Test suite for NexA Services Config Manager, Email Service, and Instagram Social Manager.
    """

    def test_default_config_generation(self, tmp_path):
        """Verify smart system defaults are generated and saved."""
        fake_cfg = tmp_path / "integrations_test.json"
        manager = ServicesConfigManager(config_path=fake_cfg)

        assert fake_cfg.exists()
        email_cfg = manager.get_email_config()
        assert email_cfg["provider"] == "gmail"
        assert email_cfg["imap_server"] == "imap.gmail.com"
        assert email_cfg["imap_port"] == 993
        assert email_cfg["auto_summarize_important"] is True

        insta_cfg = manager.get_instagram_config()
        assert "caption_tone" in insta_cfg
        assert insta_cfg["reels_duration_target_sec"] == 30

    def test_update_email_config_with_preset_persistence(self, tmp_path):
        """Verify changing provider to Outlook auto-configures servers and persists permanently."""
        fake_cfg = tmp_path / "integrations_update.json"
        manager = ServicesConfigManager(config_path=fake_cfg)

        res = manager.update_email_config(
            provider="outlook",
            email_address="user@outlook.com",
            app_password="secret_app_password_123"
        )
        assert res["success"] is True
        assert res["provider"] == "outlook"
        assert res["imap_server"] == "outlook.office365.com"
        assert res["is_configured"] is True

        # Reload from disk to verify permanent persistence
        manager_reloaded = ServicesConfigManager(config_path=fake_cfg)
        loaded_email = manager_reloaded.get_email_config()
        assert loaded_email["email_address"] == "user@outlook.com"
        assert loaded_email["app_password"] == "secret_app_password_123"
        assert loaded_email["imap_server"] == "outlook.office365.com"

    def test_email_check_unconfigured_guidance(self, tmp_path):
        """Verify check_emails returns clear guidance when credentials are not yet set."""
        fake_cfg = tmp_path / "integrations_empty.json"
        manager = ServicesConfigManager(config_path=fake_cfg)
        service = EmailService(config_manager=manager)

        res = service.check_emails()
        assert res["success"] is False
        assert res["is_configured"] is False
        assert "spoken_summary" in res
        assert "تنظیمات" in res["spoken_summary"]

    @patch("imaplib.IMAP4_SSL")
    def test_email_check_mocked_fetch_and_categorization(self, mock_imap_cls, tmp_path):
        """Verify IMAP connection parses emails, separates read/unread, and flags urgent bank emails."""
        fake_cfg = tmp_path / "integrations_mock.json"
        manager = ServicesConfigManager(config_path=fake_cfg)
        manager.update_email_config(
            email_address="test@gmail.com",
            app_password="test_password"
        )
        service = EmailService(config_manager=manager)

        # Mock IMAP instance
        mock_imap = MagicMock()
        mock_imap_cls.return_value = mock_imap
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])
        mock_imap.search.return_value = ("OK", [b"1 2"])

        # Email 1: Normal email, seen
        raw_msg1 = (
            b"From: newsletter@medium.com\r\n"
            b"Subject: Weekly Articles\r\n"
            b"Date: Sun, 11 Oct 2026 10:00:00 +0330\r\n"
            b"\r\n"
            b"Here are your weekly digests."
        )
        # Email 2: Urgent bank email, unseen
        raw_msg2 = (
            b"From: info@bank-mellat.ir\r\n"
            b"Subject: =?utf-8?b?2KfYtNi52KfYsSDZgdmI2LHbjCDYqNin2YbaqduMINin2K7Yqtin2LE=?=\r\n" # اخطار فوری بانکی اخطار
            b"Date: Sun, 11 Oct 2026 11:30:00 +0330\r\n"
            b"\r\n"
            b"A new login was detected from your IP."
        )

        def mock_fetch(msg_id, query):
            if msg_id == b"2":
                return ("OK", [(b"2 (FLAGS () RFC822.HEADER {120})", raw_msg2)])
            return ("OK", [(b"1 (FLAGS (\\Seen) RFC822.HEADER {120})", raw_msg1)])

        mock_imap.fetch.side_effect = mock_fetch

        res = service.check_emails(unread_only=False, limit=5)
        assert res["success"] is True
        assert res["total_found"] == 2
        assert res["important_count"] >= 1
        assert "spoken_summary" in res

    def test_social_media_manager_reels_planning(self):
        """Verify SocialMediaManager produces complete Instagram Reels package."""
        social = SocialMediaManager()
        res = social.plan_content(topic="معرفی هوش مصنوعی نِکسا")

        assert res["success"] is True
        assert "hook" in res
        assert len(res["scenario"]) >= 3
        assert "caption" in res
        assert "#هوش_مصنوعی" in res["hashtags"]

    def test_engine_tool_dispatch_for_email_and_social(self):
        """Verify AgentEngine dispatches email and instagram tools successfully."""
        engine = AgentEngine(api_key="test_fake_key_12345678901234567890")

        # Configure email via tool dispatch
        res_cfg = engine.dispatch_tool(
            "configure_email_settings",
            {
                "email_address": "mytest@example.com",
                "provider": "outlook"
            }
        )
        assert res_cfg["success"] is True
        assert res_cfg["provider"] == "outlook"

        # Check emails tool dispatch
        res_check = engine.dispatch_tool("check_emails", {"unread_only": True})
        assert "spoken_summary" in res_check

        # Plan Instagram tool dispatch
        res_plan = engine.dispatch_tool("plan_instagram_content", {"topic": "تکنولوژی ویندوز"})
        assert res_plan["success"] is True
        assert "scenario" in res_plan

        # Open Instagram tool dispatch (mocked)
        with patch("agent.tools.open_app_or_url", return_value={"success": True}):
            res_open = engine.dispatch_tool("open_instagram", {"page": "dms"})
            assert res_open["success"] is True
            assert "direct/inbox" in res_open["target_url"]

        # Copy caption tool dispatch (mocked)
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)
            res_copy = engine.dispatch_tool("copy_caption_to_clipboard", {"caption": "تست کپشن"})
            assert res_copy["success"] is True

        # Ensure tools are declared in TOOL_DECLARATIONS
        declared_names = [d["name"] for d in TOOL_DECLARATIONS]
        assert "check_emails" in declared_names
        assert "send_email" in declared_names
        assert "configure_email_settings" in declared_names
        assert "plan_instagram_content" in declared_names
        assert "open_instagram" in declared_names
        assert "copy_caption_to_clipboard" in declared_names

