import requests
import shutil
import os
import time

# Optional libtorrent import; if unavailable, libtorrent functions will raise
try:
    import libtorrent as lt
except Exception:
    lt = None

from yt_dlp import YoutubeDL


def realdebrid_unrestrict(link, api_key, timeout=15):
    """Unrestrict a magnet or torrent URL using Real-Debrid (example).
    Returns a direct downloadable/streamable URL on success.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.post(
        "https://api.real-debrid.com/rest/1.0/unrestrict/link",
        data={"link": link},
        headers=headers,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    # Real‑Debrid returns fields like 'download' and 'streaming'
    return data.get("download") or data.get("streaming") or data


def start_libtorrent_stream(magnet_uri, save_path="/tmp/jptv"):
    """Very small libtorrent magnet resolver that waits for metadata and
    returns the path to the largest file inside the torrent. Blocking call.
    """
    if lt is None:
        raise RuntimeError("python-libtorrent is not installed or not available")

    os.makedirs(save_path, exist_ok=True)
    ses = lt.session()
    params = {"save_path": save_path, "storage_mode": lt.storage_mode_t.storage_mode_sparse}
    handle = lt.add_magnet_uri(ses, magnet_uri, params)
    ses.start_dht()
    # wait for metadata
    while not handle.has_metadata():
        time.sleep(0.5)
    info = handle.get_torrent_info()
    files = info.files()
    largest_idx = max(range(files.num_files()), key=lambda i: files.file_size(i))
    filename = os.path.join(save_path, files.file_path(largest_idx))
    return filename


def yt_dlp_extract(url, opts=None):
    """Extract a playable URL or filename using yt-dlp."""
    ydl_opts = {"quiet": True, "no_warnings": True}
    if opts:
        ydl_opts.update(opts)
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # For HLS or direct media, ydl may return 'url' or a list of formats
        if "url" in info:
            return info["url"]
        # fall back to best format
        formats = info.get("formats") or []
        if formats:
            best = max(formats, key=lambda f: f.get("height") or 0)
            return best.get("url")
        return info.get("webpage_url")


def resolve_stream(input_link, debrid_key=None):
    """High level resolver used by the player.
    - If magnet + debrid_key -> unrestrict with debrid
    - If magnet + no debrid -> libtorrent fallback
    - Else -> yt-dlp/HLS extraction
    Returns a local file path or a direct URL suitable for playback.
    """
    if input_link.startswith("magnet:") or input_link.endswith(".torrent"):
        if debrid_key:
            return realdebrid_unrestrict(input_link, debrid_key)
        else:
            return start_libtorrent_stream(input_link)
    else:
        return yt_dlp_extract(input_link)


if __name__ == "__main__":
    print("Stream manager loaded. Run resolve_stream(url, debrid_key) from your app.")
