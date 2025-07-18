from typing import Any


class Decoder:
    @staticmethod
    def decode_text(text_data: Any) -> str:
        if isinstance(text_data, bytes):
            return text_data.decode("utf-16be", errors="ignore")
        elif isinstance(text_data, str):
            return text_data
        return str(text_data)
