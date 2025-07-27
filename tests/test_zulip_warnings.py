import unittest
from unittest.mock import patch, MagicMock
from running.plugin.runbms.zulip import Zulip
from running.util import MomaReservationStatus, MomaReservaton
from datetime import datetime, timedelta


class TestZulipWarnings(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Mock the zulip client to avoid actual network calls
        with patch('running.plugin.runbms.zulip.zulip.Client'):
            with patch('running.plugin.runbms.zulip.is_dry_run', return_value=True):
                self.zulip_plugin = Zulip(
                    name="test_zulip",
                    config_file="~/.zuliprc",
                    request={"type": "stream", "to": "test-stream", "topic": "test-topic"}
                )

    def test_not_moma_warning_removed(self):
        """Test that NOT_MOMA status no longer generates a warning"""
        # Create a reservation with NOT_MOMA status
        reservation = MomaReservaton(
            status=MomaReservationStatus.NOT_MOMA,
            user=None,
            start=None,
            end=None
        )
        
        # Mock the moma.get_reservation to return our test reservation
        with patch.object(self.zulip_plugin.moma, 'get_reservation', return_value=reservation):
            message = self.zulip_plugin.get_reservation_message()
            
            # Should return empty string instead of warning
            self.assertEqual(message, "")
            self.assertNotIn("not running on a moma machine", message)

    def test_other_reservation_warnings_preserved(self):
        """Test that other reservation warnings are still working"""
        # Test NOT_RESERVED
        reservation = MomaReservaton(
            status=MomaReservationStatus.NOT_RESERVED,
            user=None,
            start=None,
            end=None
        )
        
        with patch.object(self.zulip_plugin.moma, 'get_reservation', return_value=reservation):
            message = self.zulip_plugin.get_reservation_message()
            self.assertIn("Warning: machine not reserved", message)

        # Test RESERVED_BY_OTHERS
        reservation = MomaReservaton(
            status=MomaReservationStatus.RESERVED_BY_OTHERS,
            user="other_user",
            start=datetime.now(),
            end=datetime.now() + timedelta(hours=1)
        )
        
        with patch.object(self.zulip_plugin.moma, 'get_reservation', return_value=reservation):
            message = self.zulip_plugin.get_reservation_message()
            self.assertIn("Warning: machine reserved by other_user", message)

    def test_multiple_users_warning(self):
        """Test that multiple logged-in users generates a Zulip warning"""
        # Mock get_logged_in_users to return multiple users
        with patch('running.plugin.runbms.zulip.get_logged_in_users', return_value={"user1", "user2", "user3"}):
            message = self.zulip_plugin.get_user_warnings()
            self.assertIn("Warning: more than one user logged in", message)
            self.assertIn("user1", message)
            self.assertIn("user2", message)
            self.assertIn("user3", message)

    def test_single_user_no_warning(self):
        """Test that a single logged-in user doesn't generate a warning"""
        # Mock get_logged_in_users to return a single user
        with patch('running.plugin.runbms.zulip.get_logged_in_users', return_value={"single_user"}):
            message = self.zulip_plugin.get_user_warnings()
            self.assertEqual(message, "")

    def test_no_users_no_warning(self):
        """Test that no logged-in users doesn't generate a warning"""
        # Mock get_logged_in_users to return empty set
        with patch('running.plugin.runbms.zulip.get_logged_in_users', return_value=set()):
            message = self.zulip_plugin.get_user_warnings()
            self.assertEqual(message, "")

    def test_combined_warnings_in_message(self):
        """Test that user warnings are included in sent messages"""
        # Mock multiple users scenario
        with patch('running.plugin.runbms.zulip.get_logged_in_users', return_value={"user1", "user2"}):
            # Mock reservation
            reservation = MomaReservaton(
                status=MomaReservationStatus.NOT_RESERVED,
                user=None,
                start=None,
                end=None
            )
            
            with patch.object(self.zulip_plugin.moma, 'get_reservation', return_value=reservation):
                # Mock the client.send_message method
                with patch.object(self.zulip_plugin.client, 'send_message') as mock_send:
                    mock_send.return_value = {"result": "success", "id": 123}
                    
                    # Set dry run to False for this test
                    with patch('running.plugin.runbms.zulip.is_dry_run', return_value=False):
                        self.zulip_plugin.nop = False
                        self.zulip_plugin.send_message("test content")
                    
                    # Verify the message was called with warnings
                    mock_send.assert_called_once()
                    args, kwargs = mock_send.call_args
                    message_data = kwargs.get('message_data', args[0] if args else {})
                    content = message_data.get('content', '')
                    
                    # Should contain both reservation and user warnings
                    self.assertIn("Warning: machine not reserved", content)
                    self.assertIn("Warning: more than one user logged in", content)
                    self.assertIn("test content", content)


if __name__ == '__main__':
    unittest.main()