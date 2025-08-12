from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
import logging
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ytmusic-backend")

app = FastAPI(title="TubeTune YTMusic Proxy (Anonymous)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    ytmusic = YTMusic()  # anonymous
    logger.info("YTMusic initialized (anonymous).")
except Exception as e:
    logger.exception("Failed to initialize YTMusic: %s", e)
    ytmusic = None

@app.get("/api/youtube/search")
def youtube_search(q: str = Query(..., description="search query")):
    if ytmusic is None:
        raise HTTPException(status_code=500, detail="YTMusic not initialized")
    try:
        results = ytmusic.search(q, filter="songs")
        out = []
        for r in results:
            out.append({
                "title": r.get("title"),
                "videoId": r.get("videoId") or r.get("id"),
                "artists": r.get("artists", []),
                "duration": r.get("duration"),
                "thumbnails": r.get("thumbnails", [])
            })
        return out
    except Exception as e:
        logger.exception("youtube_search error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/youtube/playlists/search")
def youtube_playlists_search(q: str = Query(..., description="playlist search query")):
    if ytmusic is None:
        raise HTTPException(status_code=500, detail="YTMusic not initialized")
    try:
        results = ytmusic.search(q, filter="playlists")
        out = []
        for r in results:
            out.append({
                "title": r.get("title"),
                "playlistId": r.get("playlistId") or r.get("id"),
                "thumbnails": r.get("thumbnails", [])
            })
        return out
    except Exception as e:
        logger.exception("youtube_playlists_search error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/youtube/playlists/{playlist_id}")
def youtube_playlist_details(playlist_id: str):
    if ytmusic is None:
        raise HTTPException(status_code=500, detail="YTMusic not initialized")
    try:
        data = ytmusic.get_playlist(playlist_id, limit=200)
        if not data:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return data
    except Exception as e:
        logger.exception("youtube_playlist_details error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/playlists/{playlist_id}")
def get_playlist(playlist_id: str):
    return youtube_playlist_details(playlist_id)

@app.get("/api/playlists/{playlist_id}/tracks")
def get_playlist_tracks(playlist_id: str):
    if ytmusic is None:
        raise HTTPException(status_code=500, detail="YTMusic not initialized")
    try:
        data = ytmusic.get_playlist(playlist_id, limit=200)
        tracks = data.get("tracks", []) if data else []
        normalized = []
        for t in tracks:
            normalized.append({
                "title": t.get("title"),
                "videoId": t.get("videoId") or t.get("videoId"),
                "artists": t.get("artists", []),
                "duration": t.get("duration"),
                "thumbnail": (t.get("thumbnails") or [{}])[-1].get("url") if t.get("thumbnails") else None
            })
        return {"tracks": normalized}
    except Exception as e:
        logger.exception("get_playlist_tracks error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, log_level="info")
