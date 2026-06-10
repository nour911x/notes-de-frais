# Application Agentique de Gestion des Notes de Frais

Application web qui transforme la photo d'un justificatif (ticket de restaurant, billet de train, facture d'hôtel, etc.) en une ligne structurée dans un Google Sheet partagé avec la comptabilité.

Un salarié prend en photo une note de frais, l'application en extrait automatiquement les informations utiles via un modèle de vision, les affiche dans un formulaire éditable, puis les synchronise dans un Google Sheet. L'image est hébergée en ligne et un lien cliquable est inséré dans le tableur.

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Modèle IA | `meta-llama/llama-4-scout-17b-16e-instruct` via le SDK Groq |
| Backend | Python · FastAPI |
| Frontend | HTML · HTMX · CSS · JS Vanilla |
| Tableur | Google Sheets API (via `gspread`) |
| Hébergement image | imgbb |

## Structure du projet

```
expense-tracker/
├── backend.py          # Classe ExpenseAgent — extraction IA
├── app.py              # Serveur FastAPI — routes et orchestration
├── sheets.py           # Classe GoogleSheetsClient — écriture Sheet + upload image
├── context.txt         # Prompt système du modèle
├── prompt.txt          # Prompt utilisateur envoyé avec l'image
├── requirements.txt
├── .env.example
├── .env                # Non commité (secrets)
├── credentials.json    # Non commité (clé du compte de service)
└── static/
    ├── index.html      # Interface HTMX
    ├── style.css       # Feuille de style (dark mode)
    └── app.js          # JS Vanilla (prévisualisation, events HTMX)
```

## Installation

```bash
git clone https://github.com/Nour911x/notes-de-frais.git
cd notes-de-frais

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

## Configuration

Copiez le modèle d'environnement puis renseignez vos valeurs :

```bash
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux
```

Variables à renseigner dans `.env` :

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Clé API Groq (https://console.groq.com) |
| `GOOGLE_SHEET_ID` | ID du Google Sheet (chaîne entre `/d/` et `/edit` dans l'URL) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Chemin vers le fichier JSON du compte de service |
| `IMGBB_API_KEY` | Clé API imgbb (https://api.imgbb.com) |

### Configuration Google Cloud

1. Créez un projet sur https://console.cloud.google.com
2. Activez la **Google Sheets API**.
3. Créez un **compte de service** (rôle Éditeur) et téléchargez sa clé **JSON** dans le projet sous le nom `credentials.json`.
4. Créez un Google Sheet, renommez la première feuille en **`Notes de frais`** et ajoutez les en-têtes :
   `Horodatage · Type · Fournisseur · Date · Montant TTC (€) · TVA (€) · Devise · Description · Confiance · Image`
5. **Partagez** le Sheet avec l'email du compte de service (`...@...iam.gserviceaccount.com`) en rôle **Éditeur**.

> Le fichier `credentials.json` et le `.env` ne doivent jamais être commités (voir `.gitignore`).

## Lancement

```bash
uvicorn app:app --reload
```

Ouvrez ensuite http://127.0.0.1:8000

## Utilisation

1. Choisissez ou photographiez un justificatif.
2. Cliquez sur **Analyser le ticket** : le modèle extrait les champs et remplit un formulaire éditable.
3. Corrigez les champs si nécessaire.
4. Cliquez sur **Envoyer vers le Google Sheet** : la ligne (avec le lien de l'image) est ajoutée au tableur.

## Exemple de JSON retourné par le modèle

```json
{
  "type_document": "restaurant",
  "fournisseur": "Bistrot Paul",
  "date": "10/06/2026",
  "montant_ttc": 24.90,
  "tva": 2.27,
  "devise": "EUR",
  "description": "Déjeuner d'affaires",
  "confiance": "haute"
}
```

## Note sur le stockage de l'image

L'upload via le compte de service Google Drive n'est pas possible avec un compte Gmail personnel (les comptes de service n'ont pas de quota de stockage, et les Shared Drives nécessitent Google Workspace). L'image est donc hébergée sur **imgbb**, et son URL publique est insérée dans la colonne `Image` via la formule `=IMAGE(...)`.
