from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

# Tüm Origin, Header ve Metotlara Tam İzin Veren CORS Yapılandırması
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Tarayıcıların Preflight (OPTIONS) isteklerini manuel onaylama
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    return JSONResponse(
        content={"status": "ok"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-User-Logged-In, Authorization",
        },
    )

class DownloadRequest(BaseModel):
    url: str
    quality: str

@app.get("/")
async def root():
    return {"status": "ok", "message": "API Servisi Aktif"}

@app.post("/api/download")
async def get_download_link(
    request: DownloadRequest, 
    x_user_logged_in: str = Header(default="false")
):
    if request.quality == "1080p" and x_user_logged_in != "true":
        raise HTTPException(
            status_code=403, 
            detail="1080p video indirmek için üye girişi yapmanız gerekmektedir!"
        )

    format_option = "best"
    if request.quality == "mp3":
        format_option = "bestaudio/best"
    elif request.quality == "720p":
        format_option = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
    elif request.quality == "1080p":
        format_option = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"

    ydl_opts = {
        'format': format_option,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            download_url = info.get('url')
            
            if not download_url and 'requested_formats' in info:
                download_url = info['requested_formats'][0]['url']

            return {
                "success": True,
                "title": info.get('title', 'Video'),
                "download_url": download_url,
                "thumbnail": info.get('thumbnail', ''),
                "quality": request.quality
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
