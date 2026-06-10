import io
import os
from pathlib import Path
from datetime import datetime

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

BASE_DIR = Path(__file__).parent
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
WORKSHEET_NAME = "Notes de frais"

load_dotenv()


class GoogleSheetsClient:
    def __init__(self):
        creds_path = BASE_DIR / os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        self.credentials = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
        self.gc = gspread.authorize(self.credentials)
        self.sheet = self.gc.open_by_key(os.getenv("GOOGLE_SHEET_ID")).worksheet(WORKSHEET_NAME)
        self.drive = build("drive", "v3", credentials=self.credentials)

    def upload_image(self, image_bytes: bytes, media_type: str = "image/jpeg") -> str:
        name = f"note-de-frais-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype=media_type)
        file = self.drive.files().create(body={"name": name}, media_body=media, fields="id").execute()
        file_id = file["id"]
        self.drive.permissions().create(fileId=file_id, body={"role": "reader", "type": "anyone"}).execute()
        return f"https://drive.google.com/uc?export=view&id={file_id}"

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
