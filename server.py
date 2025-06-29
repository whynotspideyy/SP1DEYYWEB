from flask import Flask, request, render_template, send_file
import os, uuid, time
from threading import Thread

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
shared_links = {}

if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

def parse_hhmmss(text):
    try:
        h, m, s = map(int, text.strip().split(":"))
        return h * 3600 + m * 60 + s
    except:
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        expiry = parse_hhmmss(request.form["expiry"])
        if not file or expiry is None:
            return "❌ Invalid input"

        filename = str(uuid.uuid4()) + "_" + file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        link_id = str(uuid.uuid4())
        shared_links[link_id] = {
            "path": filepath,
            "expires_at": time.time() + expiry
        }

        return render_template("index.html", link=request.host_url + link_id)
    return render_template("index.html", link=None)

@app.route("/<link_id>")
def download(link_id):
    info = shared_links.get(link_id)
    if not info:
        return "<h2>❌ Link not found</h2>", 404
    if time.time() > info["expires_at"]:
        return "<h2>⏰ Link expired</h2>", 410
    return send_file(info["path"], as_attachment=True)

def cleanup():
    while True:
        time.sleep(30)
        now = time.time()
        for link_id in list(shared_links):
            if now > shared_links[link_id]["expires_at"]:
                try:
                    os.remove(shared_links[link_id]["path"])
                except:
                    pass
                del shared_links[link_id]

Thread(target=cleanup, daemon=True).start()

if __name__ == "__main__":
import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)