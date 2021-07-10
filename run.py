from typing import Optional
import uvicorn
from typing import List
from fastapi import FastAPI
from io import BytesIO, StringIO
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException, Cookie, Form, status, Depends, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import sqlalchemy
from config import DATABASE_URL, SECRET_KEY
import databases
from pydantic import BaseModel
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from zipfile import ZipFile
from bs4 import BeautifulSoup
import base64


class Docs(BaseModel):
    seq: int
    title: str
    index: str
    html: str


database = databases.Database(DATABASE_URL.replace("postgres://", "postgresql://"))

metadata = sqlalchemy.MetaData()

Docs = sqlalchemy.Table(
    "docs",
    metadata,
    sqlalchemy.Column("seq", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("title", sqlalchemy.String),
    sqlalchemy.Column("index", sqlalchemy.String),
    sqlalchemy.Column("html", sqlalchemy.String)
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={}
)
metadata.create_all(engine)

app = FastAPI(docs_url="/api-docs", redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
security = HTTPBasic()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/docs/{doc_seq}", response_class=HTMLResponse)
async def documents(request: Request, doc_seq: int):
    query = Docs.select().order_by(Docs.c.seq)
    doc_rows = await database.fetch_all(query)
    title_list = [{"seq" : doc_row["seq"], "title" : doc_row["title"]} for doc_row in doc_rows]

    seq = None
    index = None
    for i, doc_row in enumerate(doc_rows):
        if doc_row["seq"] == doc_seq:

            index = doc_row["index"]
            seq = i

    if index is None:
        index_list = []
        doc_html = "준비중 입니다."
    else:
        index_list = index.split("/[|]/")
        doc_html = [doc_row["html"] for doc_row in doc_rows if doc_row["seq"] == doc_seq][0]
    # print(doc_html)
    return templates.TemplateResponse("docs.html",
                                      {"request": request, "title_list": title_list, "subtitle_list": index_list,
                                       "doc_seq": doc_seq,
                                       "doc_html": doc_html})


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    if not credentials.password == SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/upload-docs", response_class=HTMLResponse, )
async def upload_docs_form(request: Request, username: str = Depends(get_current_username)):
# async def upload_docs(request: Request):
    print(username)
    query = Docs.select().order_by(Docs.c.seq)
    doc_rows = await database.fetch_all(query)
    # doc_rows = [{"seq": doc_row["seq"], "title": doc_row["title"]} for doc_row in doc_rows]

    return templates.TemplateResponse("upload.html", {"request": request, "doc_rows": doc_rows})


@app.post("/upload-docs")
async def upload_docs(background_tasks: BackgroundTasks, file: bytes = File(...), doc_seq: str = Form(...)):
    zip_file = ZipFile(BytesIO(file))
    fname_list = zip_file.namelist()
    print(fname_list)

    html_file_name = None
    image_file_name_list = []
    for fname in fname_list:
        extension = fname.split(".")[-1]
        if html_file_name is None and extension == "html":
            html_file_name = fname
        if extension in ["png", "jpeg", "jpg", "gif"]:
            image_file_name_list.append(fname)

    with zip_file.open(html_file_name) as html_file:
        soup = BeautifulSoup(html_file.read().decode("utf8"), 'html.parser', )
        soup.find("div", {"class": "container"})["class"] = "contentWrapper"
        soup = soup.find("div", {"class": "contentWrapper"})
        subtitle_list = [subtitle.text for subtitle in soup.find_all("div", {"class": "subtitle"})]

        image_list = soup.find_all("img")
        for image in image_list:
            src = image.attrs["src"]
            print(src)
            img_fname = src.split("/")[-1]
            if img_fname in image_file_name_list:
                img_binary = zip_file.open(img_fname).read()
                # print(img_binary)
                encoded_string = base64.b64encode(img_binary).decode("utf8")
                base64_str = f"data:image/png;base64,{encoded_string}"
                # print(encoded_string)
                # import clipboard
                # clipboard.copy(base64_str)

                image.attrs["src"] = base64_str

        final_html = soup.prettify()
        query = Docs.update().where(Docs.c.seq == int(doc_seq)).values(html=final_html,
                                                                       index="/[|]/".join(subtitle_list))
        last_record_id = await database.execute(query)

    return {
        "message": "Success"
    }


if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=2918, reload=True, )
