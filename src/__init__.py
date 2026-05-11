from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import re
import random
import string
from telegram import Bot
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import select
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from schema.table import Users
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from contextlib import asynccontextmanager
from schema.storage import init_db, get_session
from blofin import BloFinClient
from blofin.utils import get_server_time as original_get_time
import blofin.auth as _auth
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr
from typing import Dict
from dotenv import load_dotenv
import resend
import requests
import time
import hmac
import hashlib
import base64
from urllib.parse import urlencode
import os
load_dotenv()


BASE_URL = "https://api-spot.weex.com"
REQUEST_PATH = ""
ACCESS_PASSPHRASE = ""
waxx_api_key = ""
waxx_api_secret = ""
api_key=''
api_secret=''
passphrase=''
BYDEFI_API_KEY = ""
BYDEFI_SECRET_KEY = ""
BYDEFI_API_URL = "https://api.bydfi.com/api/v1/agent/regular_overview"
RESEND_API_KEY=""
BOT_TOKEN = ""
GROUP_CHAT_ID = 00000000000
otp_store: Dict[str, str] = {}

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ''
SMTP_PASS = ''

resend.api_key = RESEND_API_KEY

# Models
class EmailRequest(BaseModel):
    email: EmailStr

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

expire_time = datetime.now(timezone.utc) + timedelta(hours=1)
expire_timestamp = int(expire_time.timestamp())


def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

    
def send_email(to_email: str, otp: str):
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}"

    params = {
        "from": f"Hello <{SMTP_USER}>",
        "to": [to_email],
        "subject": subject,
        "html": body,
    }

    try:
        email = resend.Emails.send(params)
        print("Email sent:", email)
    except Exception as e:
        print("Error sending email:", e)



def safe_get_server_time():
    import time
    try:
        server_time = original_get_time()
        return str(int(server_time)) if server_time else str(int(time.time() * 1000))
    except Exception:
        return str(int(time.time() * 1000))

_auth.get_server_time = safe_get_server_time


client = BloFinClient(
    api_key=api_key,
    api_secret=api_secret,
    passphrase=passphrase,
    use_server_time=True, 
)


@asynccontextmanager
async def lifespan(app:FastAPI):
    print("server is running at port 8000")
    await init_db()
    print("database started successfully")
    yield
    print("the system has close automatically")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



@app.get("/", response_class=HTMLResponse)
async def intro_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


async def verify_and_get_invite(user: Users, session: AsyncSession) -> JSONResponse:
    if user.is_group_member is not True:
        user.is_group_member = True
        user.updated_at = datetime.now(timezone.utc)
        # session.add(user)
        await session.commit()
        await session.refresh(user)
    try:
        bot = Bot(token=BOT_TOKEN)
        invite_link = await bot.export_chat_invite_link(GROUP_CHAT_ID)
        return JSONResponse(
            status_code=200,
        content={"message": "verified", "invite_link": invite_link}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Unable to generate invite link"}
        )
    


@app.post("/check-status")
async def submit_data(request: Request, session: AsyncSession = Depends(get_session)):
    data = await request.json()
    user_id = data.get("user_id")
    username = data.get("username")

    if not user_id:
        return JSONResponse(status_code=400, content={"error": "Missing user_id"})

    statement = select(Users).where(Users.telegram_id == str(user_id))
    result = await session.exec(statement)
    user = result.one_or_none()

    if not user:
        return JSONResponse(
            status_code=200,
            content={"message": "new user, please register first"}
        )

    # Already verified
    if user.is_group_member:
        return await verify_and_get_invite(user, session)

    has_trading_id = user.blofin_uuid or user.bydefi_id or user.weex_uuid

    # Has trading ID but no email
    if has_trading_id and not user.email:
        uid = user.blofin_uuid or user.bydefi_id or user.weex_uuid
        return JSONResponse(
            status_code=200,
            content={
                "redirect_url": f"/enter-email?user_id={user_id}&username={username}&blofin_id={uid}"
            }
        )

    # Fully verified
    if has_trading_id and user.email:
        return await verify_and_get_invite(user, session)

    # Fallback (optional but defensive)
    return JSONResponse(
        status_code=200,
        content={"message": "verification incomplete"}
    )




# @app.post("/check-status")
# async def submit_data(request: Request, session: AsyncSession = Depends(get_session)):
#     data = await request.json()
#     user_id = data.get("user_id")
#     username = data.get("username")

#     if not user_id or not username:
#         return JSONResponse(status_code=400, content={"error": "Missing user_id or username"})

#     statement = select(Users).where(Users.telegram_id == str(user_id))
#     result = await session.exec(statement)
#     user = result.one_or_none()
#     if not user:
#         return JSONResponse(status_code=200, content={"message": "new user, please register first"})

#     if user.is_group_member:
#         bot = Bot(token=BOT_TOKEN)
#         invite_link = await bot.export_chat_invite_link(GROUP_CHAT_ID)
#         return JSONResponse(status_code=200, content={"message": f"verified", "invite_link": invite_link})
    
#     if (user.blofin_uuid or user.bydefi_id or user.weex_uuid) and not user.email:
#         uid = user.blofin_uuid or user.bydefi_id or user.weex_uuid
#         return JSONResponse(status_code=200, content={"redirect_url": f"/enter-email?user_id={user_id}&username={username}&blofin_id={uid}"})

#     if (user.blofin_uuid or user.bydefi_id or user.weex_uuid) and user.email:
#         bot = Bot(token=BOT_TOKEN)
#         invite_link = await bot.export_chat_invite_link(GROUP_CHAT_ID)
#         return JSONResponse(status_code=200, content={"message": f"verified", "invite_link": invite_link})

    
    

@app.get("/home", response_class=HTMLResponse)
async def register_page(request: Request, user_id: str = "", username: str = ""):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user_id": user_id,
        "username": username
    })



@app.get("/blofin", response_class=HTMLResponse)
async def enter_uuid(request: Request, user_id: str = "", username: str = ""):
    return templates.TemplateResponse("blofin_intruct.html",{
        "request": request,
        "user_id": user_id,
        "username": username

    })
    
    
@app.get("/blofin-verify-success", response_class=HTMLResponse)
async def enter_uuid(request: Request, user_id: str = "", username: str = "", blofin_id: str = ""):
    return templates.TemplateResponse("blofId_success.html",{
        "request": request,
        "user_id": user_id,
        "username": username,
        "blofin_id": blofin_id
    })


@app.get("/enter-uuid", response_class=HTMLResponse)
async def enter_uuid(request: Request, user_id: str = "", username: str = ""):
    return templates.TemplateResponse("uuid.html",{
        "request": request,
        "user_id": user_id,
        "username": username
    })


@app.get("/enter-email", response_class=HTMLResponse)
async def enter_email(request: Request,user_id: str = "", username: str = "", blofin_id: str = ""):
    return templates.TemplateResponse("email.html",{
        "request": request,
        "user_id": user_id,
        "username": username,
        "blofin_id": blofin_id
    })
    


@app.get("/send-otp", response_class=HTMLResponse)
async def send_otp(request: Request, user_id: str = "", username: str = "", email: str = ""):
    return templates.TemplateResponse("otp.html", {
        "request": request,
        "user_id": user_id,
        "username": username,
        "email": email
    })
    
    
@app.get("/email-verify-success", response_class=HTMLResponse)
async def enter_email(request: Request,user_id: str = "", username: str = "", email: str = ""):
    return templates.TemplateResponse("emailSuccess.html",{
        "request": request,
        "user_id": user_id,
        "username": username,
        "email": email
    })


@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request,user_id: str = "", username: str = ""):
    return templates.TemplateResponse("terms.html", {
        "request": request,
        "user_id": user_id,
        "username": username
    })


def get_affiliate_info(uuid):
    try:
        if not uuid:
            raise ValueError("UUID is required to fetch affiliate info")

        invitee_info = client.affiliate.get_invitees(uid=uuid)
        
        if not invitee_info or "data" not in invitee_info or not invitee_info.get("data"):
            raise ValueError("No invitees found for the provided UUID")
        
        user_data_info = invitee_info["data"]
        
        if str(user_data_info[0].get("uid")).lower() != str(uuid).lower():
            raise ValueError("UUID mismatch in invitee data")

        return user_data_info[0]

    except Exception as e:
        print(f"❌ Error fetching affiliate info: {e}")
        raise



def generate_signature(api_key, secret_key, timestamp):
    """Generate the X-API-SIGNATURE according to BYDFi documentation."""
    to_sign = f"{api_key}{timestamp}"
    signature = hmac.new(secret_key.encode(), to_sign.encode(), hashlib.sha256).hexdigest()
    return signature




def generate_signature_weex(timestamp: str, method: str, request_path: str, query_string: str) -> str:
    # Build the exact string to sign
    sign_str = f"{timestamp}{method}{request_path}"
    if query_string:
        sign_str += f"?{query_string}"

    # HMAC SHA256 → Base64
    digest = hmac.new(
        waxx_api_secret.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha256
    ).digest()

    return base64.b64encode(digest).decode("utf-8")





def is_weex_affiliate_member(uid: str) -> bool:
    timestamp = str(int(time.time() * 1000))
    method = "GET"

    params = {
        "uid": uid,
        "page": 1,
        "pageSize": 100
    }

    # Query string must match EXACTLY what is sent
    query_string = urlencode(params)

    signature = generate_signature_weex(
        timestamp,
        method,
        REQUEST_PATH,
        query_string
    )

    headers = {
        "ACCESS-KEY": waxx_api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-PASSPHRASE": ACCESS_PASSPHRASE,
        "ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }

    response = requests.get(
        BASE_URL + REQUEST_PATH,
        headers=headers,
        params=params
    )

    data = response.json()

    if data.get("code") != "200":
        return False

    items = data.get("data", {}).get("channelUserInfoItemList", [])
    return any(str(item.get("uid")) == str(uid) for item in items)





def is_bydfi_affiliate_member(user_uid: str):
    """Check if a specific user UID is in your BYDFi affiliate list."""
    try:
        timestamp = str(int(time.time() * 1000))
        signature = generate_signature(BYDEFI_API_KEY, BYDEFI_SECRET_KEY, timestamp)

        headers = {
            "X-API-KEY": BYDEFI_API_KEY,
            "X-API-TIMESTAMP": timestamp,
            "X-API-SIGNATURE": signature,
            "Content-Type": "application/json",
            "Accept-Language": "en-US"
        }

        response = requests.get(BYDEFI_API_URL, headers=headers)

        if response.status_code != 200:
            raise ValueError(f"API Error {response.status_code}: {response.text}")

        data = response.json()

        # Validate JSON structure
        if not data.get("success") or "data" not in data or "list" not in data["data"]:
            raise ValueError("UUID mismatch in invitee data")

        invitees = data["data"]["list"]

        # Check if the given UID exists in the list
        found_user = next((user for user in invitees if user.get("uid") == user_uid), None)

        if not found_user:
            raise ValueError("No invitees found for the provided UUID")

        return {
            "status": "found",
            "message": f"User {user_uid} is registered under your affiliate link.",
            "kyc": found_user.get("kyc"),
            "uid": found_user.get("uid"),
            "register_time": found_user.get("registerTime"),
            "swap_trading_amount": found_user.get("swapTradingAmount"),
            "deposit_amount": found_user.get("depositAmount"),
            "withdraw_amount": found_user.get("withdrawAmount")
        }

    except requests.RequestException as e:
        print(f"❌ Error fetching affiliate info: {e}")
        raise

    
    

def is_valid_email(email: str) -> bool:
    """
    Validates an email address using regex.

    Returns True if valid, False otherwise.
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))





@app.post("/submit")
async def submit_data(request: Request, session: AsyncSession = Depends(get_session)):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        username = data.get("username")
        blofin_id = data.get("blofin_id")
        email = data.get("email")
        code = data.get("otp")
        exchange =  data.get("exchange", None)

        if not user_id or not username:
            return JSONResponse(status_code=400, content={"error": "Missing user_id or username"})

        # Find or create user
        statement = select(Users).where(Users.telegram_id == str(user_id))
        result = await session.exec(statement)
        user = result.one_or_none()

        if not user:
            user = Users(
                telegram_id=str(user_id),
                username=username,
                is_group_member=False
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        updated = False

        # Check if blofin_id is already in use by someone else
        if blofin_id and exchange:
            if str(exchange).lower() == "blofin":
                existing_blofin = await session.exec(
                    select(Users).where(
                        Users.blofin_uuid == blofin_id,
                        Users.telegram_id != str(user_id)
                    )
                )
                blofin_conflict = existing_blofin.one_or_none()
                if blofin_conflict:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "This BloFin ID is already associated with another account."}
                    )

                # Validate the BloFin ID with SDK/API
                try:
                    invitee_info = get_affiliate_info(blofin_id)
                    if str(invitee_info.get("uid")) != str(blofin_id):
                        return JSONResponse(status_code=400, content={"error": "BloFin ID mismatch"})
                except Exception as e:
                    return JSONResponse(status_code=400, content={"error": str(e)})

                user.blofin_uuid = blofin_id
                # user.exchange = "BloFin"
                updated = True



            elif str(exchange).lower() == "bydfi":
                try:
                    bydefi_id = blofin_id
                    existing_bydefi = await session.exec(
                    select(Users).where(
                        Users.bydefi_id == str(bydefi_id),
                        Users.telegram_id != str(user_id)
                    )
                )
                    bydfi_conflict = existing_bydefi.one_or_none()
                    if bydfi_conflict:
                        return JSONResponse(
                            status_code=400,
                            content={"error": "This BydFi ID is already associated with another account."}
                        )
                    bydefi_invitee_info = is_bydfi_affiliate_member(bydefi_id)
                    if str(bydefi_invitee_info.get("uid")) != str(bydefi_id):
                        return JSONResponse(status_code=400, content={"error": "BydFi ID mismatch"})
                except Exception as e:
                    return JSONResponse(status_code=400, content={"error": str(e)})

                user.bydefi_id = bydefi_id
                # user.exchange = "BydFi"
                updated = True




            elif str(exchange).lower() == "weex" and blofin_id:
                try:
                    weex_id = str(blofin_id).strip().lower()

                    # Idempotent: already bound
                    if user.weex_uuid != weex_id:
                        result = await session.exec(
                            select(Users).where(
                                Users.weex_uuid == weex_id,
                                Users.exchange == "Weex",
                                Users.id != user.id
                            )
                        )
                        conflict = result.one_or_none()

                        if conflict:
                            return JSONResponse(
                                status_code=400,
                                content={"error": "This Weex ID is already associated with another account."}
                            )

                        invitee_info = is_weex_affiliate_member(weex_id)
                        if not invitee_info:
                            return JSONResponse(
                                status_code=400,
                                content={"error": "Invalid WEEX ID"}
                            )

                        user.weex_uuid = weex_id
                        updated = True
                except Exception as e:
                    return JSONResponse(status_code=400, content={"error": str(e)})




        # Check if email is already in use by another user
        if email and not code:
            email = email.strip().lower()  # Normalize email
            if not is_valid_email(email):
                return JSONResponse(status_code=400, content={"error": "Invalid email format"})

            existing_email = await session.exec(
                select(Users).where(
                    Users.email == email,
                    Users.telegram_id != str(user_id)
                )
            )
            email_conflict = existing_email.one_or_none()
            if email_conflict:
                return JSONResponse(
                    status_code=400,
                    content={"error": "This email is already associated with another account."}
                )

            try:              
                otp = generate_otp()
                otp_store[email] = otp
                send_email(email, otp)
            except Exception as e:
                return JSONResponse(status_code=400, content={"error": f"Failed to send otp to the provided email: {str(e)}"})
        
        if code:
            saved_otp = otp_store.get(email)
            if str(code) != str(saved_otp):
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid OTP"}
                )
                
            del otp_store[email]
            user.email = email
            updated = True
            

        if updated:
            user.updated_at = datetime.now()
            session.add(user)
            try:
                await session.commit()
                
            except IntegrityError as e:
                await session.rollback()
                return JSONResponse(
                    status_code=400,
                    content={"error": "Email or BloFin ID already associated with another account."}
                )
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"❌ SQLAlchemyError: {e}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Database constraint failed. Possibly duplicate email or BloFin ID."}
                )

        return JSONResponse(content={"status": "success", "message": "User info stored/updated"})

    except Exception as e:
        import traceback
        print(f"❌ Error in submit_data: {e} ({type(e).__name__})")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Internal error: {str(e)}"})

