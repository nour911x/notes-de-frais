import os
import json
import base64
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

BASE_DIR = Path(__file__).parent
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
EXPECTED_FIELDS = ("type_document", "fournisseur", "date", "montant_ttc", "tva", "devise", "description", "confiance")

load_dotenv()


class ExpenseAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.context = self.read_file("context.txt")
        self.prompt = self.read_file("prompt.txt")

    @staticmethod
    def read_file(filename: str) -> str:
        return (BASE_DIR / filename).read_text(encoding="utf-8")

    @staticmethod
    def encode_image(image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")

    def extract_from_bytes(self, image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
        base64_image = self.encode_image(image_bytes)
        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": self.context},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{base64_image}"}},
                    ],
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        data = json.loads(response.choices[0].message.content)
        result = {field: data.get(field) for field in EXPECTED_FIELDS}
        result["devise"] = result.get("devise") or "EUR"
        return result


if __name__ == "__main__":
    import sys
    import mimetypes

    image_path = sys.argv[1] if len(sys.argv) > 1 else "ticket.jpg"
    media_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    image_bytes = Path(image_path).read_bytes()
    result = ExpenseAgent().extract_from_bytes(image_bytes, media_type=media_type)
    print(json.dumps(result, indent=2, ensure_ascii=False))
