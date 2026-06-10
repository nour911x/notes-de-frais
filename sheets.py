import os
import base64
from pathlib import Path
from datetime import datetime

import gspread
import requests
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

BASE_DIR = Path(__file__).parent
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
WORKSHEET_NAME = "Notes de frais"
IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"

load_dotenv()


class GoogleSheetsClient:
    def __init__(self):
        creds_path = BASE_DIR / os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        self.credentials = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
        self.gc = gspread.authorize(self.credentials)
        self.sheet = self.gc.open_by_key(os.getenv("GOOGLE_SHEET_ID")).worksheet(WORKSHEET_NAME)

    @staticmethod
    def upload_image(image_bytes: bytes, media_type: str = "image/jpeg") -> str:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        response = requests.post(
            IMGBB_UPLOAD_URL,
            data={"key": os.getenv("IMGBB_API_KEY"), "image": encoded},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["data"]["url"]

    def append_expense(self, data: dict, image_url: str = None) -> None:
        row = [
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            data.get("type_document"),
            data.get("fournisseur"),
            data.get("date"),
            data.get("montant_ttc"),
            data.get("tva"),
            data.get("devise") or "EUR",
            data.get("description"),
            data.get("confiance"),
            f'=IMAGE("{image_url}")' if image_url else "",
        ]
        self.sheet.append_row(row, value_input_option="USER_ENTERED")


if __name__ == "__main__":
    import sys
    import mimetypes

    client = GoogleSheetsClient()
    image_url = None
    if len(sys.argv) > 1:
        path = sys.argv[1]
        media_type = mimetypes.guess_type(path)[0] or "image/jpeg"
        image_url = client.upload_image(Path(path).read_bytes(), media_type)
        print("Image uploadee :", image_url)

    fake = {
        "type_document": "restaurant",
        "fournisseur": "Test Bistrot",
        "date": "10/06/2026",
        "montant_ttc": 24.9,
        "tva": 2.27,
        "devise": "EUR",
        "description": "Ligne de test",
        "confiance": "haute",
    }
    client.append_expense(fake, image_url)
    print("Ligne factice ajoutee au Google Sheet.")
