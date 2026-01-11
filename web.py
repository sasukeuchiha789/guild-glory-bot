from flask import Flask, render_template_string
import json

app = Flask(__name__)

@app.route('/')
def dashboard():
    with open("config.json") as f:
        cfg = json.load(f)
    return render_template_string("""
    <html>
    <head>
        <title>{{cfg.project_name}}</title>
        <style>
            body { font-family: 'Orbitron', sans-serif; background: #0a0a0a; color: cyan; text-align:center; }
            .card { margin-top:80px; background:#111; border-radius:20px; display:inline-block; padding:40px; box-shadow:0 0 15px cyan; }
            .credit { margin-top:20px; color:#888; font-size:14px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>{{cfg.project_name}} 💀</h1>
            <h3>Version: {{cfg.version}}</h3>
            <p>Developed by {{cfg.developer}}</p>
            <p>Mode: Fake Dashboard Simulation</p>
        </div>
        <div class="credit">© 2025 Phantom4ura Labs</div>
    </body>
    </html>
    """, cfg=cfg)

if __name__ == "__main__":
    app.run(debug=False, port=8080)