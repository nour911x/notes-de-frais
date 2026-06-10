import base64
from pathlib import Path
from html import escape

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend import ExpenseAgent
from sheets import GoogleSheetsClient

BASE_DIR = Path(__file__).parent
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
TYPE_OPTIONS = ("restaurant", "transport", "hotel", "autre")
CONFIANCE_OPTIONS = ("haute", "moyen", "basse")
CONFIANCE_CLASS = {"haute": "badge-high", "moyen": "badge-medium", "basse": "badge-low"}

app = FastAPI(title="Gestion des Notes de Frais")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

agent = ExpenseAgent()
sheets = GoogleSheetsClient()


def select_options(options: tuple, selected) -> str:
    selected = str(selected or "").lower()
    return "".join(
        f'<option value="{escape(o)}"{" selected" if o == selected else ""}>{escape(o)}</option>'
        for o in options
    )


def value_of(data: dict, key: str, default: str = "") -> str:
    value = data.get(key)
    return escape(str(value)) if value is not None else default


def build_form_fragment(data: dict, image_data: str) -> str:
    confiance = str(data.get("confiance") or "moyen").lower()
    badge_class = CONFIANCE_CLASS.get(confiance, "badge-medium")
    return f"""
<div class="form-header">
  <img class="receipt-thumb" src="{escape(image_data)}" alt="Justificatif">
  <div class="form-header-info">
    <h2>Informations extraites</h2>
    <span class="badge {badge_class}">Confiance&nbsp;: {escape(confiance)}</span>
  </div>
</div>
<form id="expense-form" hx-post="/api/submit" hx-target="#confirmation-container" hx-swap="innerHTML">
  <input type="hidden" name="image_data" value="{escape(image_data)}">
  <label class="full">Type de document
    <select name="type_document">{select_options(TYPE_OPTIONS, data.get("type_document"))}</select>
  </label>
  <label class="full">Fournisseur
    <input type="text" name="fournisseur" value="{value_of(data, "fournisseur")}">
  </label>
  <label>Date
    <input type="text" name="date" value="{value_of(data, "date")}" placeholder="JJ/MM/AAAA">
  </label>
  <label>Montant TTC (€)
    <input type="number" step="0.01" name="montant_ttc" value="{value_of(data, "montant_ttc")}">
  </label>
  <label>TVA (€)
    <input type="number" step="0.01" name="tva" value="{value_of(data, "tva")}">
  </label>
  <label>Devise
    <input type="text" name="devise" value="{value_of(data, "devise", "EUR")}">
  </label>
  <label class="full">Description
    <input type="text" name="description" value="{value_of(data, "description")}">
  </label>
  <label class="full">Confiance
    <select name="confiance">{select_options(CONFIANCE_OPTIONS, data.get("confiance"))}</select>
  </label>
  <button type="submit">Envoyer vers le Google Sheet</button>
</form>
"""


@app.exception_handler(HTTPException)
async def htmx_exception_handler(request: Request, exc: HTTPException):
    return HTMLResponse(
        content=f'<p class="message message-error">Erreur {exc.status_code} : {exc.detail}</p>',
        status_code=exc.status_code,
    )


@app.get("/", response_class=FileResponse)
async def serve_frontend():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.post("/api/analyze", response_class=HTMLResponse)
async def analyze_expense(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(415, detail="Type de fichier non supporté. Veuillez envoyer une image.")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, detail=f"Format non supporté : {file.content_type}. Formats acceptés : JPEG, PNG, WEBP, GIF.")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(413, detail="Image trop volumineuse (maximum 10 Mo).")

    try:
        data = agent.extract_from_bytes(image_bytes, media_type=file.content_type)
    except Exception as e:
        raise HTTPException(500, detail=f"Erreur du modèle : {str(e)}")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data = f"data:{file.content_type};base64,{image_b64}"
    return HTMLResponse(content=build_form_fragment(data, image_data))


@app.post("/api/submit", response_class=HTMLResponse)
async def submit_expense(
    type_document: str = Form(""),
    fournisseur: str = Form(""),
    date: str = Form(""),
    montant_ttc: str = Form(""),
    tva: str = Form(""),
    devise: str = Form("EUR"),
    description: str = Form(""),
    confiance: str = Form(""),
    image_data: str = Form(""),
):
    data = {
        "type_document": type_document,
        "fournisseur": fournisseur,
        "date": date,
        "montant_ttc": montant_ttc,
        "tva": tva,
        "devise": devise,
        "description": description,
        "confiance": confiance,
    }

    image_url = None
    if image_data and "," in image_data:
        try:
            header, encoded = image_data.split(",", 1)
            media_type = header.replace("data:", "").split(";")[0] or "image/jpeg"
            image_url = sheets.upload_image(base64.b64decode(encoded), media_type)
        except Exception:
            image_url = None

    try:
        sheets.append_expense(data, image_url)
    except Exception as e:
        raise HTTPException(500, detail=f"Erreur Google Sheets : {str(e)}")

    return HTMLResponse(content='<p class="message message-success">Note de frais envoyée au Google Sheet avec succès.</p>')
