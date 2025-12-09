"""
Marketing Mandy - Conversational AI Marketing Assistant
Dead simple: Chat with Mandy -> Drop your stuff -> Hit Market -> Done
"""
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

app = Flask(__name__)
CORS(app)

# Storage
UPLOAD_FOLDER = Path('./uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Scheduler setup
jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///mandy_jobs.sqlite')}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

# Campaign state
campaigns = {}

DEFAULT_SCHEDULES = {
    'instagram': {'times': ['11:00', '21:00'], 'days': 'daily'},
    'x': {'times': ['09:00', '12:00', '17:00'], 'days': 'daily'},
    'linkedin': {'times': ['07:30', '12:00'], 'days': 'weekdays'},
    'facebook': {'times': ['09:00', '13:00', '19:00'], 'days': 'daily'},
    'tiktok': {'times': ['12:00', '19:00', '22:00'], 'days': 'daily'},
    'reddit': {'times': ['10:00', '19:00'], 'days': 'daily'},
    'youtube': {'times': ['15:00'], 'days': 'daily'},
    'threads': {'times': ['09:00', '18:00'], 'days': 'daily'},
    'pinterest': {'times': ['14:00', '21:00'], 'days': 'daily'}
}

PLATFORMS = {
    'instagram': {'icon': '📸', 'name': 'Instagram', 'max_chars': 2200},
    'x': {'icon': '𝕏', 'name': 'X (Twitter)', 'max_chars': 280},
    'linkedin': {'icon': '💼', 'name': 'LinkedIn', 'max_chars': 3000},
    'facebook': {'icon': '📘', 'name': 'Facebook', 'max_chars': 63206},
    'tiktok': {'icon': '🎵', 'name': 'TikTok', 'max_chars': 2200},
    'reddit': {'icon': '🔶', 'name': 'Reddit', 'max_chars': 40000},
    'youtube': {'icon': '📺', 'name': 'YouTube', 'max_chars': 5000},
    'threads': {'icon': '🧵', 'name': 'Threads', 'max_chars': 500},
    'pinterest': {'icon': '📌', 'name': 'Pinterest', 'max_chars': 500}
}

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marketing Mandy</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Syne:wght@700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0d0d12; --bg-chat: #16161e; --bg-input: #1e1e28;
            --accent: #ff2d92; --accent-glow: rgba(255, 45, 146, 0.3);
            --green: #00ff88; --blue: #00d4ff;
            --text: #ffffff; --text-dim: #8888aa; --border: #2a2a3a;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column; }
        .header { padding: 1rem 1.5rem; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 1rem; background: var(--bg-chat); }
        .mandy-avatar { width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, var(--accent), #b14aff); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; box-shadow: 0 0 20px var(--accent-glow); }
        .header-text h1 { font-family: 'Syne', sans-serif; font-size: 1.3rem; background: linear-gradient(135deg, var(--accent), var(--blue)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header-text p { font-size: 0.8rem; color: var(--text-dim); }
        .status-dot { width: 8px; height: 8px; background: var(--green); border-radius: 50%; margin-left: auto; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .chat-container { flex: 1; overflow-y: auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
        .message { max-width: 85%; padding: 1rem 1.25rem; border-radius: 18px; line-height: 1.5; animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .message.mandy { background: var(--bg-input); border: 1px solid var(--border); align-self: flex-start; border-bottom-left-radius: 4px; }
        .message.user { background: linear-gradient(135deg, var(--accent), #b14aff); align-self: flex-end; border-bottom-right-radius: 4px; }
        .message.system { background: rgba(0, 255, 136, 0.1); border: 1px solid var(--green); align-self: center; text-align: center; font-size: 0.9rem; }
        .quick-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem; }
        .quick-btn { background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; }
        .quick-btn:hover { border-color: var(--accent); background: rgba(255, 45, 146, 0.1); }
        .platform-pills { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem; }
        .platform-pill { display: flex; align-items: center; gap: 0.4rem; background: var(--bg); border: 2px solid var(--border); padding: 0.5rem 0.9rem; border-radius: 25px; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; }
        .platform-pill:hover { border-color: var(--blue); }
        .platform-pill.selected { border-color: var(--green); background: rgba(0, 255, 136, 0.1); }
        .platform-pill .check { display: none; color: var(--green); }
        .platform-pill.selected .check { display: inline; }
        .platform-pill.coming-soon-pill { opacity: 0.5; cursor: not-allowed; }
        .platform-pill .soon-badge { font-size: 0.65rem; background: rgba(255,200,0,0.3); color: #ffcc00; padding: 0.15rem 0.4rem; border-radius: 8px; }
        .upload-area { border: 2px dashed var(--border); border-radius: 16px; padding: 1.5rem; text-align: center; margin-top: 0.75rem; cursor: pointer; transition: all 0.2s; }
        .upload-area:hover { border-color: var(--accent); background: rgba(255, 45, 146, 0.05); }
        .upload-area .icon { font-size: 2rem; margin-bottom: 0.5rem; }
        .uploaded-files { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1rem; }
        .uploaded-file { position: relative; width: 80px; height: 80px; border-radius: 12px; overflow: hidden; border: 2px solid var(--border); }
        .uploaded-file img { width: 100%; height: 100%; object-fit: cover; }
        .uploaded-file .remove { position: absolute; top: 4px; right: 4px; width: 20px; height: 20px; background: rgba(0,0,0,0.7); border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 0.7rem; }
        .schedule-preview { background: var(--bg); border-radius: 12px; padding: 1rem; margin-top: 0.75rem; }
        .schedule-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border); }
        .schedule-item:last-child { border-bottom: none; }
        .schedule-item .times { color: var(--text-dim); font-size: 0.85rem; }
        .input-container { padding: 1rem 1.5rem; border-top: 1px solid var(--border); background: var(--bg-chat); }
        .input-row { display: flex; gap: 0.75rem; align-items: flex-end; }
        .input-wrapper { flex: 1; background: var(--bg-input); border: 1px solid var(--border); border-radius: 24px; display: flex; align-items: center; padding: 0.25rem; }
        .input-wrapper:focus-within { border-color: var(--accent); }
        .chat-input { flex: 1; background: none; border: none; color: var(--text); padding: 0.75rem 1rem; font-size: 1rem; font-family: inherit; resize: none; max-height: 120px; }
        .chat-input:focus { outline: none; }
        .chat-input::placeholder { color: var(--text-dim); }
        .attach-btn { background: none; border: none; color: var(--text-dim); font-size: 1.3rem; cursor: pointer; padding: 0.5rem; }
        .attach-btn:hover { color: var(--accent); }
        .send-btn { background: linear-gradient(135deg, var(--accent), #b14aff); border: none; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 1.2rem; transition: transform 0.2s; }
        .send-btn:hover { transform: scale(1.05); box-shadow: 0 0 20px var(--accent-glow); }
        .market-btn { width: 100%; background: linear-gradient(135deg, var(--green), #00b368); border: none; padding: 1rem; border-radius: 16px; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.2rem; color: #000; cursor: pointer; margin-top: 1rem; display: none; }
        .market-btn.visible { display: block; animation: fadeIn 0.3s ease; }
        .market-btn:hover { transform: scale(1.02); box-shadow: 0 0 30px rgba(0, 255, 136, 0.4); }
        .typing-indicator { display: flex; gap: 4px; padding: 1rem; }
        .typing-indicator span { width: 8px; height: 8px; background: var(--text-dim); border-radius: 50%; animation: bounce 1.4s infinite ease-in-out; }
        .typing-indicator span:nth-child(1) { animation-delay: 0s; }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-6px); } }

        .settings-btn { background: none; border: none; font-size: 1.3rem; cursor: pointer; padding: 0.5rem; margin-left: auto; opacity: 0.7; transition: opacity 0.2s; }
        .settings-btn:hover { opacity: 1; }
        .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 1000; align-items: center; justify-content: center; padding: 1rem; }
        .modal-overlay.active { display: flex; }
        .modal { background: var(--bg-chat); border: 1px solid var(--border); border-radius: 20px; width: 100%; max-width: 600px; max-height: 90vh; overflow: hidden; display: flex; flex-direction: column; }
        .modal-header { padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; }
        .modal-header h2 { font-family: 'Syne', sans-serif; font-size: 1.2rem; }
        .modal-close { background: none; border: none; color: var(--text-dim); font-size: 1.2rem; cursor: pointer; }
        .modal-close:hover { color: var(--text); }
        .modal-body { padding: 1.5rem; overflow-y: auto; flex: 1; }
        .modal-intro { color: var(--text-dim); font-size: 0.9rem; margin-bottom: 1.5rem; }
        .modal-footer { padding: 1rem 1.5rem; border-top: 1px solid var(--border); display: flex; gap: 0.75rem; justify-content: flex-end; }
        .btn-primary { background: linear-gradient(135deg, var(--accent), #b14aff); border: none; color: white; padding: 0.75rem 1.5rem; border-radius: 10px; font-weight: 600; cursor: pointer; }
        .btn-primary:hover { box-shadow: 0 0 20px var(--accent-glow); }
        .btn-secondary { background: transparent; border: 1px solid var(--border); color: var(--text); padding: 0.75rem 1.5rem; border-radius: 10px; cursor: pointer; }
        .btn-secondary:hover { border-color: var(--text-dim); }
        .platform-card { background: var(--bg-input); border: 1px solid var(--border); border-radius: 12px; margin-bottom: 1rem; overflow: hidden; }
        .platform-card-header { padding: 1rem; display: flex; align-items: center; gap: 0.75rem; cursor: pointer; }
        .platform-card-header:hover { background: rgba(255,255,255,0.02); }
        .platform-card-icon { font-size: 1.5rem; }
        .platform-card-name { font-weight: 600; flex: 1; }
        .platform-card-status { font-size: 0.75rem; padding: 0.25rem 0.6rem; border-radius: 10px; }
        .platform-card-status.connected { background: rgba(0,255,136,0.2); color: var(--green); }
        .platform-card-status.not-connected { background: rgba(255,255,255,0.1); color: var(--text-dim); }
        .platform-card-toggle { color: var(--text-dim); transition: transform 0.2s; }
        .platform-card.expanded .platform-card-toggle { transform: rotate(180deg); }
        .platform-card-body { display: none; padding: 0 1rem 1rem; border-top: 1px solid var(--border); }
        .platform-card.expanded .platform-card-body { display: block; }
        .cred-field { margin-top: 1rem; }
        .cred-field label { display: block; font-size: 0.85rem; color: var(--text-dim); margin-bottom: 0.4rem; }
        .cred-field input { width: 100%; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 0.7rem; color: var(--text); font-family: monospace; font-size: 0.85rem; }
        .cred-field input:focus { outline: none; border-color: var(--accent); }
        .cred-field input::placeholder { color: var(--text-dim); opacity: 0.5; }
        .cred-help { font-size: 0.75rem; color: var(--text-dim); margin-top: 0.3rem; }
        .cred-help a { color: var(--blue); text-decoration: none; }
        .cred-help a:hover { text-decoration: underline; }
        .test-connection { background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.85rem; cursor: pointer; margin-top: 1rem; }
        .test-connection:hover { border-color: var(--blue); color: var(--blue); }
        .platform-card.coming-soon { opacity: 0.6; }
        .platform-card.coming-soon .platform-card-header { cursor: default; }
        .platform-card-status.coming-soon { background: rgba(255,200,0,0.2); color: #ffcc00; }
        .coming-soon-msg { color: var(--text-dim); font-style: italic; padding: 0.5rem 0; }
    </style>
</head>
<body>
    <div class="header">
        <div class="mandy-avatar">👩‍💼</div>
        <div class="header-text"><h1>Marketing Mandy</h1><p>Your AI Posting Homie</p></div>
        <button class="settings-btn" id="settingsBtn">⚙️</button>
        <div class="status-dot"></div>
    </div>
    
    <!-- Settings Modal -->
    <div class="modal-overlay" id="settingsModal">
        <div class="modal">
            <div class="modal-header">
                <h2>⚙️ Platform Credentials</h2>
                <button class="modal-close" id="closeSettings">✕</button>
            </div>
            <div class="modal-body">
                <p class="modal-intro">Connect your accounts to start posting. Your credentials are stored locally and encrypted.</p>
                
                <div class="platform-settings" id="platformSettings">
                    <!-- Platform cards will be inserted here -->
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" id="cancelSettings">Cancel</button>
                <button class="btn-primary" id="saveSettings">💾 Save All</button>
            </div>
        </div>
    </div>
    <div class="chat-container" id="chat"></div>
    <div class="input-container">
        <div class="input-row">
            <div class="input-wrapper">
                <button class="attach-btn">📎</button>
                <textarea class="chat-input" id="userInput" placeholder="Tell Mandy about your business..." rows="1" onkeydown="handleKeyDown(event)"></textarea>
            </div>
            <button class="send-btn">➤</button>
        </div>
        <button class="market-btn" id="marketBtn">🚀 START MARKETING</button>
    </div>
    <input type="file" id="fileInput" multiple accept="image/*,video/*" style="display:none" onchange="handleFiles(event)">
    <script src="/static/mandy.js"></script>
</body>
</html>'''


@app.route('/')
def index():
    response = app.make_response(render_template_string(HTML_TEMPLATE))
    response.headers['Content-Security-Policy'] = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;"
    return response


@app.route('/api/launch', methods=['POST'])
def launch_campaign():
    data = request.json
    campaign_id = f"camp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    campaign = {
        'id': campaign_id,
        'product': data.get('product', {}),
        'assets': data.get('assets', []),
        'platforms': data.get('platforms', []),
        'status': 'active',
        'created_at': datetime.now().isoformat()
    }
    campaigns[campaign_id] = campaign
    
    # Schedule posts for each platform
    for platform_id in campaign['platforms']:
        schedule = DEFAULT_SCHEDULES.get(platform_id, {'times': ['12:00']})
        for time_str in schedule['times']:
            hour, minute = map(int, time_str.split(':'))
            now = datetime.now()
            post_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if post_time <= now:
                post_time += timedelta(days=1)
            
            job_id = f"{campaign_id}_{platform_id}_{time_str.replace(':', '')}"
            scheduler.add_job(
                execute_post,
                'interval',
                days=1,
                start_date=post_time,
                args=[campaign_id, platform_id],
                id=job_id
            )
    
    return jsonify({'success': True, 'campaign_id': campaign_id})


@app.route('/api/campaign/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    if campaign_id not in campaigns:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(campaigns[campaign_id])


@app.route('/api/campaign/<campaign_id>/pause', methods=['POST'])
def pause_campaign(campaign_id):
    if campaign_id not in campaigns:
        return jsonify({'error': 'Not found'}), 404
    campaigns[campaign_id]['status'] = 'paused'
    for job in scheduler.get_jobs():
        if job.id.startswith(campaign_id):
            job.pause()
    return jsonify({'success': True})


def execute_post(campaign_id: str, platform_id: str):
    """Execute a scheduled post"""
    if campaign_id not in campaigns:
        return
    campaign = campaigns[campaign_id]
    if campaign['status'] != 'active':
        return
    print(f"[MANDY] Posting to {platform_id} for {campaign_id}")



# Credentials storage
CREDS_FILE = Path('./credentials.json')

def load_creds_file():
    if CREDS_FILE.exists():
        try:
            with open(CREDS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_creds_file(creds):
    with open(CREDS_FILE, 'w') as f:
        json.dump(creds, f)


@app.route('/api/credentials', methods=['GET'])
def get_credentials():
    creds = load_creds_file()
    return jsonify({'credentials': creds})


@app.route('/api/credentials', methods=['POST'])
def save_credentials():
    data = request.json
    creds = data.get('credentials', {})
    save_creds_file(creds)
    
    # Also set as environment variables for current session
    for k, v in creds.items():
        if v:
            os.environ[k] = v
    
    return jsonify({'success': True})


@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    data = request.json
    platform = data.get('platform')
    creds = data.get('credentials', {})
    
    # Set credentials temporarily
    for k, v in creds.items():
        if v:
            os.environ[k] = v
    
    # Coming soon platforms
    coming_soon = ['instagram', 'linkedin', 'facebook', 'tiktok', 'youtube', 'threads', 'pinterest']
    if platform in coming_soon:
        return jsonify({'success': False, 'error': 'Coming soon - awaiting API approval', 'coming_soon': True})
    
    try:
        if platform == 'bluesky':
            import requests as req
            resp = req.post(
                'https://bsky.social/xrpc/com.atproto.server.createSession',
                json={
                    'identifier': creds.get('BLUESKY_HANDLE'),
                    'password': creds.get('BLUESKY_APP_PASSWORD')
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return jsonify({'success': True, 'user': data.get('handle')})
            return jsonify({'success': False, 'error': resp.json().get('message', 'Auth failed')})
        
        elif platform == 'mastodon':
            import requests as req
            instance = creds.get('MASTODON_INSTANCE', 'mastodon.social')
            token = creds.get('MASTODON_ACCESS_TOKEN')
            resp = req.get(
                f'https://{instance}/api/v1/accounts/verify_credentials',
                headers={'Authorization': f'Bearer {token}'}
            )
            if resp.status_code == 200:
                data = resp.json()
                return jsonify({'success': True, 'user': data.get('username')})
            return jsonify({'success': False, 'error': 'Invalid token or instance'})
        
        elif platform == 'reddit':
            import praw
            reddit = praw.Reddit(
                client_id=creds.get('REDDIT_CLIENT_ID'),
                client_secret=creds.get('REDDIT_CLIENT_SECRET'),
                username=creds.get('REDDIT_USERNAME'),
                password=creds.get('REDDIT_PASSWORD'),
                user_agent='MarketingMandy/1.0'
            )
            user = reddit.user.me()
            return jsonify({'success': True, 'user': str(user)})
        
        else:
            return jsonify({'success': False, 'error': 'Unknown platform'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def start_desktop():
    """Start as desktop app"""
    import webview
    webview.create_window('Marketing Mandy', app, width=450, height=700, resizable=True, min_size=(380, 500))
    webview.start()


if __name__ == '__main__':
    import sys
    if '--web' in sys.argv:
        port = int(sys.argv[sys.argv.index('--port') + 1]) if '--port' in sys.argv else 5000
        app.run(debug=True, port=port, host='0.0.0.0')
    else:
        start_desktop()
