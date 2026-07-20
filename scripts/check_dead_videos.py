import sqlite3
import urllib.request
import urllib.error

DB_PATH = "data/db/northstar.db"

def check_video_exists(url):
    oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
    try:
        req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
        urllib.request.urlopen(req)
        return True
    except urllib.error.HTTPError as e:
        if e.code in [404, 401, 400]:
            return False
        # Other errors might be temporary, assume true for safety
        return True
    except Exception as e:
        return True

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT video_id, url FROM learning_videos")
    videos = cursor.fetchall()

    to_delete = []
    print(f"Checking {len(videos)} videos...")
    for video_id, url in videos:
        if not check_video_exists(url):
            print(f"Video dead: {video_id} - {url}")
            to_delete.append(video_id)
        else:
            print(f"Video OK: {video_id} - {url}")

    if to_delete:
        print(f"Deleting {len(to_delete)} videos...")
        placeholders = ",".join(["?"] * len(to_delete))
        cursor.execute(f"DELETE FROM learning_videos WHERE video_id IN ({placeholders})", to_delete)
        conn.commit()
        print("Deleted.")
    else:
        print("No dead videos found.")

    conn.close()

if __name__ == "__main__":
    main()
