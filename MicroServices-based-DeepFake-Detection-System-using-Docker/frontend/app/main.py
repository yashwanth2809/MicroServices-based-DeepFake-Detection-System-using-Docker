from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import httpx, shutil, os, uuid

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="CHANGE_THIS_SECRET")

templates = Jinja2Templates(directory="templates")
FD_URL = "http://face_detection_service:8000/predict_all"

# in-memory user store
users = {}

@app.get("/register")
def reg_form(request: Request):
    return templates.TemplateResponse("register.html", {"request":request})

@app.post("/register")
def do_register(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in users:
        return templates.TemplateResponse("register.html", {"request":request, "error":"Username exists"})
    users[username] = password
    return RedirectResponse("/login", status_code=302)

@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request":request})

@app.post("/login")
def do_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if users.get(username) != password:
        return templates.TemplateResponse("login.html", {"request":request, "error":"Invalid"})    
    request.session["user"] = username
    return RedirectResponse("/upload", status_code=302)

@app.get("/upload")
def upload_form(request: Request):
    if "user" not in request.session:
        return RedirectResponse("/login")
    return templates.TemplateResponse("upload.html", {"request":request, "user":request.session["user"]})

@app.post("/upload")
async def do_upload(request: Request, file: UploadFile = File(...)):
    if "user" not in request.session:
        return RedirectResponse("/login")
    tmp_name = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(tmp_name, "wb") as f:
        shutil.copyfileobj(file.file, f)

    async with httpx.AsyncClient() as client:
        resp = await client.post(FD_URL, files={"file": open(tmp_name,"rb")})
    os.remove(tmp_name)

    if resp.status_code != 200:
        raise HTTPException(502, "Face-detection failure")

    result = resp.json()
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "user": request.session["user"],
        "result": result
    })
