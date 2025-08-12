from flask import Flask, request, jsonify
from flask_cors import CORS
from ytmusicapi import YTMusic
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("power2-backend")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

try:
    ytmusic = YTMusic()  # anonymous
    logger.info("YTMusic initialized (anonymous).")
except Exception as e:
    logger.exception("Failed to initialize YTMusic: %s", e)
    ytmusic = None

@app.route("/search")
def search():
    q = request.args.get("query") or request.args.get("q")
    if not q:
        return jsonify({"error": "missing query"}), 400
    if ytmusic is None:
        return jsonify({"error": "ytmusic not initialized"}), 500
    try:
        results = ytmusic.search(q, filter="songs")
        out = []
        for r in results:
            out.append({
                "title": r.get("title"),
                "videoId": r.get("videoId") or r.get("id"),
                "artists": [a.get("name") for a in r.get("artists", [])] if r.get("artists") else [],
                "duration": r.get("duration"),
                "thumbnails": r.get("thumbnails", [])
            })
        return jsonify(out)
    except Exception as e:
        logger.exception("search error: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/playlists/<playlist_id>")
def playlist(playlist_id):
    if ytmusic is None:
        return jsonify({"error": "ytmusic not initialized"}), 500
    try:
        data = ytmusic.get_playlist(playlist_id, limit=200)
        return jsonify(data or {})
    except Exception as e:
        logger.exception("playlist error: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/playlists/<playlist_id>/tracks")
def playlist_tracks(playlist_id):
    if ytmusic is None:
        return jsonify({"error": "ytmusic not initialized"}), 500
    try:
        data = ytmusic.get_playlist(playlist_id, limit=200)
        tracks = data.get("tracks", []) if data else []
        out = []
        for t in tracks:
            out.append({
                "title": t.get("title"),
                "videoId": t.get("videoId"),
                "artists": [a.get("name") for a in t.get("artists", [])] if t.get("artists") else [],
                "duration": t.get("duration"),
                "thumbnail": (t.get("thumbnails") or [{}])[-1].get("url") if t.get("thumbnails") else None
            })
        return jsonify({"tracks": out})
    except Exception as e:
        logger.exception("playlist_tracks error: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/")
def root():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
