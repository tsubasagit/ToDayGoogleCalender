import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")


def get_credentials():
    """OAuth認証を行い、認証情報を返す。初回はブラウザで認証。"""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    "credentials.json が見つかりません。\n"
                    "SETUP.md を参照して Google Cloud Console から\n"
                    "OAuth クライアントIDをダウンロードしてください。"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return creds


def get_events_for_date(target_date=None):
    """指定日の予定を取得して返す。target_dateはdatetime.dateオブジェクト。"""
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    if target_date is None:
        target_date = datetime.date.today()

    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    start_of_day = now.replace(
        year=target_date.year, month=target_date.month, day=target_date.day,
        hour=0, minute=0, second=0, microsecond=0
    )
    end_of_day = start_of_day + datetime.timedelta(days=1)

    time_min = start_of_day.isoformat()
    time_max = end_of_day.isoformat()

    events_result = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])

    parsed = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))

        all_day = "date" in event["start"]

        parsed.append({
            "summary": event.get("summary", "(タイトルなし)"),
            "start": start,
            "end": end,
            "location": event.get("location", ""),
            "all_day": all_day,
        })

    return parsed
