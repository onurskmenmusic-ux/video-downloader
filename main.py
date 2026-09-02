from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    quality: str

@app.get("/")
async def root():
    return {"status": "ok", "message": "API Aktif"}

@app.post("/api/download")
async def get_download_link(request: DownloadRequest):
    format_option = "best"
    if request.quality == "mp3":
        format_option = "bestaudio/best"
    elif request.quality == "720":
        format_option = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
    elif request.quality == "1080":
        format_option = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"

    # Farklı istemcileri sırayla deneyerek engelleri aşma konfigürasyonu
    client_configs = [
        ['ios', 'mweb'],
        ['android', 'web'],
        ['tv_embedded']
    ]

    last_error = ""

    for clients in client_configs:
        ydl_opts = {
            'format': format_option,
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extractor_args': {
                'youtube': {
                    'player_client': clients,
                    'skip': ['hls', 'dash']
                }
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(request.url, download=False)
                
                download_url = info.get('url')
                if not download_url and 'requested_formats' in info:
                    download_url = info['requested_formats'][0]['url']

                if download_url:
                    return {
                        "success": True,
                        "title": info.get('title', 'Video'),
                        "download_url": download_url,
                        "thumbnail": info.get('thumbnail', '')
                    }
        except Exception as e:
            last_error = str(e)
            continue

    raise HTTPException(status_code=400, detail=f"Bağlantı alınamadı: {last_error}")
