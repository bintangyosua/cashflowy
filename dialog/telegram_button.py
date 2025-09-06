class TelegramButton:
    """
    Class to represent a button in a Telegram message (inline keyboard).
    """
    def __init__(self, button_id, title):
        self.button_id = button_id
        self.title = title

    def to_dict(self):
        return {
            "text": self.title,
            "callback_data": self.button_id
        }
