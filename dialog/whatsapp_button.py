class WhatsappButton:
    """
    Class to represent a button in a WhatsApp message.
    """
    def __init__(self, button_id, title):
        self.button_id = button_id
        self.title = title

    def to_dict(self):
        """Konversi button ke format JSON WhatsApp API"""
        return {
            "type": "reply",
            "reply": {"id": self.button_id, "title": self.title}
        }