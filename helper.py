from apiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from apiclient import discovery
from google.oauth2 import service_account
import googleapiclient.discovery
import os
import io
import json
import gspread

DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID")
DRIVE_FILE_ID = os.environ.get("DRIVE_FILE_ID")
FILES_DIR = os.path.dirname(os.path.realpath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(FILES_DIR, "haimyahad-aa77fdf4439f.json")
SCOPES = ["https://www.googleapis.com/auth/drive", "https://spreadsheets.google.com/feeds"]
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = discovery.build("drive", "v3", credentials=credentials)
gspread_client = gspread.authorize(credentials)
sheet = client.open("Haim Yahad").sheet1

def get_db(logger):
    request = service.files().get_media(fileId=DRIVE_FILE_ID)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)
    wrapped = io.TextIOWrapper(fh)
    db = json.loads(wrapped.read())
    logger.info("DB loaded: {}".format(db))
    return db

def save_user_context(user, user_context, logger):
    # get current saved user context
    db = get_db(logger)
    current_user_context = db.get(user, {})
    # update the current user context with new data (maybe)
    current_user_context.update(user_context)
    db[user] = current_user_context
    logger.info("About to save the following data for user {}: {}".format(user, current_user_context))
    # now save updated user context
    encoded_data = io.BytesIO(json.dumps(db).encode())
    media_body = MediaIoBaseUpload(encoded_data, mimetype="application/json")
    status = service.files().update(fileId=DRIVE_FILE_ID, media_body=media_body).execute()
    if status:
        logger.info("Successfully saved data to Google Drive!")
    else:
        logger.info("Error saving data to Google Drive.")

def update_requested_contact(user, logger):
    first_name, last_name = get_full_name(user, logger)
    row = [user, first_name, last_name, "ביקש שייצרו עמו קשר"]
    sheet.append_row(row)

def get_full_name(user, logger):
    db = get_db(logger)
    user_context = db.get(user, {})
    first_name = user_context.get("first_name", None)
    first_name = user_context.get("last_name", None)
    return first_name, last_name

def update_given_item(user, image_url, logger):
    first_name, last_name = get_full_name(user, logger)
    row = [user, first_name, last_name, "מוסר", image_url]
    sheet.append_row(row)

def update_requsted_item(user, item, logger):
    first_name, last_name = get_full_name(user, logger)
    row = [user, first_name, last_name, "מבקש", item]
    sheet.append_row(row)
