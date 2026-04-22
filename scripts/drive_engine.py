#!/usr/bin/env python3
"""
CPI Bangladesh Mission — Drive Operations Engine
All Google Drive / Sheets / Docs operations in one module.
Used by the GUI and CLI scripts.
"""

import json, time, io
from pathlib import Path
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG   = BASE_DIR / "config" / "cpms_config.json"

# ── Config: Drive IDs ─────────────────────────────────────────
DRIVE_CONFIG = {
    "SHARED_DRIVE_ID":  "18N_9Eq4oOCPZoTBW4CbsVNqLVBkvb6KW",
    "TEMPLATE_REG_ID":  "1kl39tYBZ2qVq5eq0LRv7e4Cv-jXeNUPGdIrZhrw1mIM",
    "INDEX_SHEET_ID":   "1jq5y9rY5-WaTtukok7Sol0px5SM5fUG6tF3MQmvBJaQ",
    "VERSION":          "v1.0",
    "TODAY":            "2026-04",
    "USER_EMAIL":       "ariful@cpintl.org",
}

# Folder ID map from verified build (99 folders)
FOLDER_IDS = {
    "ROOT":         "18N_9Eq4oOCPZoTBW4CbsVNqLVBkvb6KW",
    "00_TPL":       "1Qkyi-ZdzvG_52-aFp471nzAvTCLMUAzG",
    "01_HRA":       "18iryBvBOZr96FR49zZoVO6q5QZQX3wdp",
    "02_GF":        "1zDhsKUZEQi50mQjpdU8TcvmaMPJ2Tf-N",
    "03_LSC":       "1U_Tf3Z-kYAurOTkIZ-BLhrqy3dIDYaHo",
    "04_MER":       "1LH5oT8sIb0A_taNNok2HBAZ0C6PWE4Qj",
    "GBL_01_GOV":   "1G-Gv9WDFuEwg8sogFYf8jjag_USjiipk",
    "GBL_02_FIN":   "1mNZ18VrLZGVhBdD8_wuuwegJyjXHt4zV",
    "GBL_03_HR":    "1DSQW6C8vV1fuBAqNldmnprKU4x3m2XZQ",
    "GBL_04_LOG":   "1rwVQDKpGQeSWQNvOKNSWPb5K7M_98vuA",
    "GBL_05_PROG":  "1408RoCljObPWIVhGkl58nntK0-9Dd_ex",
    "GBL_06_MER":   "1MCzNI8dQTNsoS4fWXg1ib-bKIflOzpW_",
    "GBL_07_PART":  "1-WaJfRHzcozL58xFdYGy8zA2jJLPhMc6",
    "GBL_08_COMM":  "1WTi2Sqtzz45DUvGJV9uWXggZv317wazk",
    "99_ARC":       "ARCHIVE_ID_PLACEHOLDER",
}

MIME = {
    "folder": "application/vnd.google-apps.folder",
    "sheet":  "application/vnd.google-apps.spreadsheet",
    "doc":    "application/vnd.google-apps.document",
    "form":   "application/vnd.google-apps.form",
    "json":   "application/json",
    "xlsx":   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class DriveEngine:
    """All Drive/Sheets/Docs operations. Instantiate once, reuse."""

    def __init__(self, drive_svc, sheets_svc, docs_svc=None):
        self.drive  = drive_svc
        self.sheets = sheets_svc
        self.docs   = docs_svc
        self.log    = []

    # ── Search ────────────────────────────────────────────────

    def find(self, name, parent_id, mime=None):
        """Return (id, name, mimeType) of first match, or None."""
        q = f"name='{name}' and '{parent_id}' in parents and trashed=false"
        if mime:
            q += f" and mimeType='{mime}'"
        try:
            res = self.drive.files().list(
                q=q, spaces="drive",
                fields="files(id,name,mimeType,webViewLink,modifiedTime)",
                supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()
            items = res.get("files", [])
            return items[0] if items else None
        except HttpError:
            return None

    def list_children(self, parent_id, mime=None, page_size=100):
        """Return list of all children in a folder."""
        q = f"'{parent_id}' in parents and trashed=false"
        if mime:
            q += f" and mimeType='{mime}'"
        try:
            results, token = [], None
            while True:
                kwargs = dict(
                    q=q, spaces="drive", pageSize=page_size,
                    fields="nextPageToken,files(id,name,mimeType,webViewLink,modifiedTime,size)",
                    supportsAllDrives=True, includeItemsFromAllDrives=True,
                    orderBy="name"
                )
                if token:
                    kwargs["pageToken"] = token
                res = self.drive.files().list(**kwargs).execute()
                results.extend(res.get("files", []))
                token = res.get("nextPageToken")
                if not token:
                    break
            return results
        except HttpError as e:
            return []

    def get_file_info(self, file_id):
        """Return metadata for a specific file/folder ID."""
        try:
            return self.drive.files().get(
                fileId=file_id,
                fields="id,name,mimeType,webViewLink,modifiedTime,parents,size",
                supportsAllDrives=True
            ).execute()
        except HttpError:
            return None

    # ── Create ────────────────────────────────────────────────

    def create_folder(self, name, parent_id, skip_if_exists=True):
        if skip_if_exists:
            existing = self.find(name, parent_id, MIME["folder"])
            if existing:
                self.log.append(f"📁 EXISTS  {name}")
                return existing["id"]
        meta = {"name": name, "mimeType": MIME["folder"], "parents": [parent_id]}
        f = self.drive.files().create(body=meta, fields="id", supportsAllDrives=True).execute()
        self.log.append(f"📁 CREATED {name}")
        time.sleep(0.15)
        return f["id"]

    def create_sheet(self, name, parent_id, skip_if_exists=True):
        if skip_if_exists:
            existing = self.find(name, parent_id, MIME["sheet"])
            if existing:
                self.log.append(f"📊 EXISTS  {name}")
                return existing["id"]
        meta = {"name": name, "mimeType": MIME["sheet"], "parents": [parent_id]}
        f = self.drive.files().create(body=meta, fields="id", supportsAllDrives=True).execute()
        self.log.append(f"📊 CREATED {name}")
        time.sleep(0.15)
        return f["id"]

    def create_doc(self, name, parent_id, skip_if_exists=True):
        if skip_if_exists:
            existing = self.find(name, parent_id, MIME["doc"])
            if existing:
                self.log.append(f"📄 EXISTS  {name}")
                return existing["id"]
        meta = {"name": name, "mimeType": MIME["doc"], "parents": [parent_id]}
        f = self.drive.files().create(body=meta, fields="id", supportsAllDrives=True).execute()
        self.log.append(f"📄 CREATED {name}")
        time.sleep(0.15)
        return f["id"]

    def upload_json(self, name, parent_id, data: dict, skip_if_exists=True):
        fname = name if name.endswith(".json") else name + ".json"
        if skip_if_exists:
            existing = self.find(fname, parent_id)
            if existing:
                self.log.append(f"🗂️  EXISTS  {fname}")
                return existing["id"]
        content = json.dumps(data, indent=2).encode("utf-8")
        meta    = {"name": fname, "parents": [parent_id]}
        media   = MediaIoBaseUpload(io.BytesIO(content), mimetype=MIME["json"])
        f = self.drive.files().create(
            body=meta, media_body=media, fields="id", supportsAllDrives=True
        ).execute()
        self.log.append(f"🗂️  CREATED {fname}")
        time.sleep(0.15)
        return f["id"]

    def upload_file(self, local_path: Path, parent_id: str, mime: str, skip_if_exists=True):
        name = local_path.name
        if skip_if_exists:
            existing = self.find(name, parent_id)
            if existing:
                self.log.append(f"📎 EXISTS  {name}")
                return existing["id"]
        media = MediaIoBaseUpload(open(local_path, "rb"), mimetype=mime)
        meta  = {"name": name, "parents": [parent_id]}
        f = self.drive.files().create(
            body=meta, media_body=media, fields="id", supportsAllDrives=True
        ).execute()
        self.log.append(f"📎 UPLOADED {name}")
        return f["id"]

    # ── Rename / Move ─────────────────────────────────────────

    def rename(self, file_id, new_name):
        self.drive.files().update(
            fileId=file_id, body={"name": new_name}, supportsAllDrives=True
        ).execute()
        self.log.append(f"✏️  RENAMED → {new_name}")

    def move(self, file_id, new_parent_id, old_parent_id):
        self.drive.files().update(
            fileId=file_id,
            addParents=new_parent_id,
            removeParents=old_parent_id,
            supportsAllDrives=True,
            fields="id,parents"
        ).execute()
        self.log.append(f"📦 MOVED {file_id}")

    def trash(self, file_id):
        self.drive.files().update(
            fileId=file_id, body={"trashed": True}, supportsAllDrives=True
        ).execute()
        self.log.append(f"🗑️  TRASHED {file_id}")

    # ── Sheets ────────────────────────────────────────────────

    def write_sheet_headers(self, sheet_id, headers: list, sheet_name="Sheet1"):
        self.sheets.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption="RAW",
            body={"values": [headers]}
        ).execute()
        time.sleep(0.2)

    def write_sheet_rows(self, sheet_id, rows: list, start_row=2, sheet_name="Sheet1"):
        if not rows:
            return
        self.sheets.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!A{start_row}",
            valueInputOption="USER_ENTERED",
            body={"values": rows}
        ).execute()
        time.sleep(0.2)

    def read_sheet(self, sheet_id, range_name="Sheet1"):
        try:
            res = self.sheets.spreadsheets().values().get(
                spreadsheetId=sheet_id, range=range_name
            ).execute()
            return res.get("values", [])
        except HttpError:
            return []

    def append_sheet_row(self, sheet_id, row: list, sheet_name="Sheet1"):
        self.sheets.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]}
        ).execute()
        time.sleep(0.1)

    def clear_sheet(self, sheet_id, range_name="Sheet1"):
        self.sheets.spreadsheets().values().clear(
            spreadsheetId=sheet_id, range=range_name
        ).execute()

    def apply_header_formatting(self, sheet_id, num_cols: int, sheet_name="Sheet1"):
        """Apply CPI purple header row formatting."""
        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 0, "endRowIndex": 1,
                        "startColumnIndex": 0, "endColumnIndex": num_cols
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.255, "green": 0.153, "blue": 0.231},
                            "textFormat": {
                                "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                                "bold": True,
                                "fontSize": 10,
                                "fontFamily": "Arial"
                            }
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"
                }
            },
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": 0, "gridProperties": {"frozenRowCount": 1}},
                    "fields": "gridProperties.frozenRowCount"
                }
            }
        ]
        self.sheets.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": requests}
        ).execute()

    # ── Permissions ───────────────────────────────────────────

    def set_permission(self, file_id, email, role="reader"):
        """Set viewer or editor permission for a specific user."""
        body = {"type": "user", "role": role, "emailAddress": email}
        self.drive.permissions().create(
            fileId=file_id, body=body, supportsAllDrives=True
        ).execute()
        self.log.append(f"🔒 PERMISSION {role} → {email}")

    def list_permissions(self, file_id):
        res = self.drive.permissions().list(
            fileId=file_id, supportsAllDrives=True,
            fields="permissions(id,emailAddress,role,type)"
        ).execute()
        return res.get("permissions", [])

    # ── Utilities ─────────────────────────────────────────────

    def drive_url(self, file_id, is_folder=True):
        if is_folder:
            return f"https://drive.google.com/drive/folders/{file_id}"
        return f"https://drive.google.com/file/d/{file_id}"

    def sheet_url(self, sheet_id):
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}"

    def doc_url(self, doc_id):
        return f"https://docs.google.com/document/d/{doc_id}"

    def get_log(self):
        return self.log.copy()

    def clear_log(self):
        self.log = []
