from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

# WordPress sitenizden gelen isteklere izin vermek için CORS ayarı
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    quality: str  # "mp3", "720p", "1080p"

@app.post("/api/download")
async def get_download_link(
    request: DownloadRequest, 
    x_user_logged_in: str = Header(default="false")
):
    # 1080p İndirme Yetki Kontrolü
    if request.quality == "1080p" and x_user_logged_in != "true":
        raise HTTPException(
            status_code=403, 
            detail="1080p video indirmek için üye girişi yapmanız gerekmektedir!"
        )

    # Kaliteye göre yt-dlp format ayarı
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