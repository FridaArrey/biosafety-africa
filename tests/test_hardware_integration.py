"""
Test hardware integration with mock synthesizer
"""
import unittest
from unittest.mock import patch, MagicMock
from src.hardware_integration import SynthesizerInterface

class TestHardwareIntegration(unittest.TestCase):
    
    @patch('usb.core.find')
    def test_usb_connection(self, mock_usb_find):
        # Mock USB device
        mock_device = MagicMock()
        mock_device.idVendor = 0x1234
        mock_usb_find.return_value = [mock_device]
        
        interface = SynthesizerInterface("usb")
        connected = interface.connect_synthesizer()
        
        self.assertTrue(connected)
        self.assertEqual(interface.connection, mock_device)
    
    def test_sequence_blocking(self):
        interface = SynthesizerInterface()
        interface.connection = MagicMock()  # Mock connection
        
        # Test sequence with assembly patterns
        dangerous_sequence = "ATGGGTCTCAAAGACGCTCTTC"
        result = interface.intercept_synthesis_order(dangerous_sequence)
        
        # Should be blocked due to BsaI/SapI sites
        self.assertTrue('synthesis_blocked' in result)

if __name__ == "__main__":
    unittest.main()
