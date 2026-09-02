from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    quality: str

@app.get("/")
async def root():
    return {"status": "ok", "message": "API Servisi Aktif"}

@app.post("/api/download")
async def get_download_link(request: DownloadRequest):
    format_option = "best"
    if request.quality == "mp3":
        format_option = "bestaudio/best"
    elif request.quality == "720p":
        format_option = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
    elif request.quality == "1080p":
        format_option = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"

    # YouTube Bot Engellerini Aşma Ayarları
    ydl_opts = {
        'format': format_option,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            
            download_url = info.get('url')
            if not download_url and 'requested_formats' in info:
                download_url = info['requested_formats'][0]['url']

            if not download_url:
                raise HTTPException(status_code=400, detail="İndirme bağlantısı ayıklanamadı.")

            return {
                "success": True,
                "title": info.get('title', 'Video'),
                "download_url": download_url,
                "thumbnail": info.get('thumbnail', ''),
                "quality": request.quality
            }
    except Exception as e:
        # Hatayı doğrudan WordPress'e bildir
        raise HTTPException(status_code=400, detail=f"yt-dlp Hatası: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
