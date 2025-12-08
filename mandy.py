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
    </style>
</head>
<body>
    <div class="header">
        <div class="mandy-avatar">👩‍💼</div>
        <div class="header-text"><h1>Marketing Mandy</h1><p>Your AI Posting Homie</p></div>
        <div class="status-dot"></div>
    </div>
    <div class="chat-container" id="chat"></div>
    <div class="input-container">
        <div class="input-row">
            <div class="input-wrapper">
                <button class="attach-btn" onclick="triggerUpload()">📎</button>
                <textarea class="chat-input" id="userInput" placeholder="Tell Mandy about your business..." rows="1" onkeydown="handleKeyDown(event)"></textarea>
            </div>
            <button class="send-btn" onclick="sendMessage()">➤</button>
        </div>
        <button class="market-btn" id="marketBtn" onclick="launchCampaign()">🚀 START MARKETING</button>
    </div>
    <input type="file" id="fileInput" multiple accept="image/*,video/*" style="display:none" onchange="handleFiles(event)">
    <script>
        const state = { stage: 'intro', product: {}, assets: [], platforms: [], schedule: {}, campaignId: null };
        const platforms = {"instagram":{"icon":"📸","name":"Instagram"},"x":{"icon":"𝕏","name":"X (Twitter)"},"linkedin":{"icon":"💼","name":"LinkedIn"},"facebook":{"icon":"📘","name":"Facebook"},"tiktok":{"icon":"🎵","name":"TikTok"},"reddit":{"icon":"🔶","name":"Reddit"},"youtube":{"icon":"📺","name":"YouTube"},"threads":{"icon":"🧵","name":"Threads"},"pinterest":{"icon":"📌","name":"Pinterest"}};
        const defaultSchedules = {"instagram":{"times":["11:00","21:00"]},"x":{"times":["09:00","12:00","17:00"]},"linkedin":{"times":["07:30","12:00"]},"facebook":{"times":["09:00","13:00","19:00"]},"tiktok":{"times":["12:00","19:00","22:00"]},"reddit":{"times":["10:00","19:00"]},"youtube":{"times":["15:00"]},"threads":{"times":["09:00","18:00"]},"pinterest":{"times":["14:00","21:00"]}};
        
        document.addEventListener('DOMContentLoaded', function() {
            addMandyMessage("Hey! 👋 I'm Mandy, your marketing sidekick. What are we promoting today?", ["I'm selling t-shirts", "I have a software product", "I run a local business", "Something else"]);
            
            document.querySelector('.attach-btn').addEventListener('click', triggerUpload);
            document.querySelector('.send-btn').addEventListener('click', sendMessage);
            document.getElementById('marketBtn').addEventListener('click', launchCampaign);
            document.getElementById('fileInput').addEventListener('change', handleFiles);
            document.getElementById('userInput').addEventListener('keydown', handleKeyDown);
        });
        
        function addMandyMessage(text, quickActions, extra) {
            quickActions = quickActions || [];
            extra = extra || '';
            const chat = document.getElementById('chat');
            const msg = document.createElement('div');
            msg.className = 'message mandy';
            let html = text;
            if (quickActions.length) {
                html += '<div class="quick-actions">';
                quickActions.forEach(function(a) { 
                    html += '<button class="quick-btn" data-action="' + a + '">' + a + '</button>'; 
                });
                html += '</div>';
            }
            msg.innerHTML = html + extra;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
            
            msg.querySelectorAll('.quick-btn').forEach(function(btn) {
                btn.addEventListener('click', function() {
                    handleQuickAction(this.getAttribute('data-action'));
                });
            });
            
            var uploadArea = msg.querySelector('.upload-area');
            if (uploadArea) {
                uploadArea.addEventListener('click', triggerUpload);
            }
        }
        
        function addUserMessage(text) {
            const chat = document.getElementById('chat');
            const msg = document.createElement('div');
            msg.className = 'message user';
            msg.textContent = text;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function addSystemMessage(text) {
            const chat = document.getElementById('chat');
            const msg = document.createElement('div');
            msg.className = 'message system';
            msg.innerHTML = text;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function showTyping() {
            const chat = document.getElementById('chat');
            const t = document.createElement('div');
            t.className = 'message mandy'; 
            t.id = 'typing';
            t.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
            chat.appendChild(t);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function hideTyping() { 
            const t = document.getElementById('typing'); 
            if (t) t.remove(); 
        }
        
        function handleQuickAction(action) { 
            addUserMessage(action); 
            processInput(action); 
        }
        
        function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;
            addUserMessage(text);
            input.value = '';
            processInput(text);
        }
        
        function handleKeyDown(e) { 
            if (e.key === 'Enter' && !e.shiftKey) { 
                e.preventDefault(); 
                sendMessage(); 
            } 
        }
        
        function processInput(text) {
            showTyping();
            setTimeout(function() {
                hideTyping();
                if (state.stage === 'intro') {
                    state.product.name = text;
                    state.stage = 'product';
                    addMandyMessage("Nice! Tell me more - what's the vibe? Who's it for?", ["Trendy & youthful", "Professional & clean", "Fun & quirky", "Premium & luxury"]);
                } else if (state.stage === 'product') {
                    state.product.vibe = text;
                    state.stage = 'assets';
                    addMandyMessage("Got it! Now drop some visuals - logo, product pics, any ads you've made.", [], '<div class="upload-area" id="uploadArea"><div class="icon">📁</div><div>Drop files here or click to browse</div></div><div class="uploaded-files" id="uploadedFiles"></div>');
                } else if (state.stage === 'assets') {
                    state.stage = 'platforms';
                    showPlatformSelection();
                } else if (state.stage === 'platforms') {
                    state.stage = 'schedule';
                    showSchedulePreview();
                } else if (state.stage === 'schedule') {
                    state.stage = 'ready';
                    showReadyState();
                }
            }, 800);
        }
        
        function showPlatformSelection() {
            let html = '<div class="platform-pills">';
            for (const id in platforms) {
                const p = platforms[id];
                html += '<div class="platform-pill" data-platform="' + id + '"><span>' + p.icon + '</span><span>' + p.name + '</span><span class="check">✓</span></div>';
            }
            html += '</div><div style="margin-top:1rem"><button class="quick-btn" id="confirmPlatformsBtn">Done selecting →</button></div>';
            addMandyMessage("Where do you want to post?", [], html);
            
            setTimeout(function() {
                document.querySelectorAll('.platform-pill').forEach(function(pill) {
                    pill.addEventListener('click', function() {
                        togglePlatform(this.getAttribute('data-platform'));
                    });
                });
                var confirmBtn = document.getElementById('confirmPlatformsBtn');
                if (confirmBtn) {
                    confirmBtn.addEventListener('click', confirmPlatforms);
                }
            }, 100);
        }
        
        function togglePlatform(id) {
            const pill = document.querySelector('[data-platform="' + id + '"]');
            const idx = state.platforms.indexOf(id);
            if (idx > -1) { 
                state.platforms.splice(idx, 1); 
                pill.classList.remove('selected'); 
            } else { 
                state.platforms.push(id); 
                pill.classList.add('selected'); 
            }
        }
        
        function confirmPlatforms() {
            if (state.platforms.length === 0) { 
                addSystemMessage("Pick at least one!"); 
                return; 
            }
            addUserMessage("Selected: " + state.platforms.map(function(p) { return platforms[p].name; }).join(', '));
            state.stage = 'schedule';
            showSchedulePreview();
        }
        
        function showSchedulePreview() {
            let html = '<div class="schedule-preview">';
            state.platforms.forEach(function(pid) {
                const p = platforms[pid];
                const s = defaultSchedules[pid];
                html += '<div class="schedule-item"><span>' + p.icon + '</span><span>' + p.name + '</span><span class="times">' + s.times.join(' & ') + '</span></div>';
            });
            html += '</div>';
            addMandyMessage("Here's when I'll post (optimal times):", ["Sounds good!", "Use defaults"], html);
        }
        
        function showReadyState() {
            addMandyMessage("🎯 Ready!<br><br><b>Product:</b> " + state.product.name + "<br><b>Vibe:</b> " + state.product.vibe + "<br><b>Assets:</b> " + state.assets.length + " files<br><b>Platforms:</b> " + state.platforms.map(function(p) { return platforms[p].icon; }).join(' ') + "<br><br>Hit that green button!");
            document.getElementById('marketBtn').classList.add('visible');
        }
        
        function launchCampaign() {
            const btn = document.getElementById('marketBtn');
            btn.textContent = '⏳ Launching...'; 
            btn.disabled = true;
            fetch('/api/launch', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify({ product: state.product, assets: state.assets, platforms: state.platforms }) 
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                state.campaignId = data.campaign_id;
                btn.style.display = 'none';
                addSystemMessage("🎉 Campaign is LIVE!");
                addMandyMessage("I'm now posting for you! Next post: " + platforms[state.platforms[0]].icon + " at " + defaultSchedules[state.platforms[0]].times[0], ["Show schedule", "Pause campaign"]);
            })
            .catch(function(e) { 
                btn.textContent = '🚀 START MARKETING'; 
                btn.disabled = false; 
                addSystemMessage("Oops! Try again."); 
            });
        }
        
        function triggerUpload() { 
            document.getElementById('fileInput').click(); 
        }
        
        function handleFiles(e) {
            const container = document.getElementById('uploadedFiles');
            if (!container) return;
            Array.from(e.target.files).forEach(function(file, i) {
                const reader = new FileReader();
                reader.onload = function(ev) {
                    const id = Date.now() + i;
                    state.assets.push({ id: id, name: file.name, data: ev.target.result });
                    const thumb = document.createElement('div');
                    thumb.className = 'uploaded-file';
                    thumb.innerHTML = '<img src="' + ev.target.result + '"><div class="remove" data-id="' + id + '">✕</div>';
                    thumb.querySelector('.remove').addEventListener('click', function() {
                        removeFile(id);
                    });
                    container.appendChild(thumb);
                };
                reader.readAsDataURL(file);
            });
            setTimeout(function() { 
                if (state.assets.length && state.stage === 'assets') {
                    addMandyMessage("Got " + state.assets.length + " file(s). More, or we good?", ["That's all", "Add more"]); 
                }
            }, 500);
        }
        
        function removeFile(id) { 
            state.assets = state.assets.filter(function(a) { return a.id !== id; }); 
            const el = document.querySelector('[data-id="' + id + '"]');
            if (el) el.parentElement.remove();
        }
    </script>
</body>
</html>'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


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
