const state = { stage: 'intro', product: {}, assets: [], platforms: [], schedule: {}, campaignId: null };
        const platforms = {"bluesky":{"icon":"🦋","name":"Bluesky","supported":true},"mastodon":{"icon":"🐘","name":"Mastodon","supported":true},"reddit":{"icon":"🔶","name":"Reddit","supported":true},"instagram":{"icon":"📸","name":"Instagram","supported":false},"linkedin":{"icon":"💼","name":"LinkedIn","supported":false},"facebook":{"icon":"📘","name":"Facebook","supported":false},"tiktok":{"icon":"🎵","name":"TikTok","supported":false},"youtube":{"icon":"📺","name":"YouTube","supported":false},"threads":{"icon":"🧵","name":"Threads","supported":false},"pinterest":{"icon":"📌","name":"Pinterest","supported":false}};
        const defaultSchedules = {"bluesky":{"times":["09:00","12:00","17:00"]},"mastodon":{"times":["09:00","14:00","19:00"]},"reddit":{"times":["10:00","19:00"]},"instagram":{"times":["11:00","21:00"]},"linkedin":{"times":["07:30","12:00"]},"facebook":{"times":["09:00","13:00","19:00"]},"tiktok":{"times":["12:00","19:00","22:00"]},"youtube":{"times":["15:00"]},"threads":{"times":["09:00","18:00"]},"pinterest":{"times":["14:00","21:00"]}};
        
        document.addEventListener('DOMContentLoaded', function() {
            addMandyMessage("Hey! 👋 I'm Mandy, your marketing sidekick. What are we promoting today?", ["I'm selling t-shirts", "I have a software product", "I run a local business", "Something else"]);
            
            document.querySelector('.attach-btn').addEventListener('click', triggerUpload);
            document.querySelector('.send-btn').addEventListener('click', sendMessage);
            document.getElementById('marketBtn').addEventListener('click', launchCampaign);
            document.getElementById('fileInput').addEventListener('change', handleFiles);
            document.getElementById('userInput').addEventListener('keydown', handleKeyDown);
            
            // Settings modal listeners
            loadCredentials();
            if (document.getElementById('settingsBtn')) {
                document.getElementById('settingsBtn').addEventListener('click', openSettings);
            }
            if (document.getElementById('closeSettings')) {
                document.getElementById('closeSettings').addEventListener('click', closeSettings);
            }
            if (document.getElementById('cancelSettings')) {
                document.getElementById('cancelSettings').addEventListener('click', closeSettings);
            }
            if (document.getElementById('saveSettings')) {
                document.getElementById('saveSettings').addEventListener('click', saveCredentials);
            }
            if (document.getElementById('settingsModal')) {
                document.getElementById('settingsModal').addEventListener('click', function(e) {
                    if (e.target === this) closeSettings();
                });
            }
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
                var supported = p.supported !== false;
                var pillClass = 'platform-pill' + (supported ? '' : ' coming-soon-pill');
                var suffix = supported ? '<span class="check">✓</span>' : '<span class="soon-badge">Soon</span>';
                html += '<div class="' + pillClass + '" data-platform="' + id + '" data-supported="' + supported + '"><span>' + p.icon + '</span><span>' + p.name + '</span>' + suffix + '</div>';
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
            if (pill.dataset.supported === 'false') {
                addSystemMessage(platforms[id].name + ' coming soon! Select from supported platforms.');
                return;
            }
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

        
        // Platform credential configs
        const platformCreds = {
            bluesky: {
                name: 'Bluesky',
                icon: '🦋',
                status: 'supported',
                fields: [
                    { key: 'BLUESKY_HANDLE', label: 'Handle', placeholder: 'yourname.bsky.social' },
                    { key: 'BLUESKY_APP_PASSWORD', label: 'App Password', placeholder: 'xxxx-xxxx-xxxx-xxxx', type: 'password' }
                ],
                helpUrl: 'https://bsky.app/settings/app-passwords',
                helpText: 'Settings → Privacy & Security → App Passwords'
            },
            mastodon: {
                name: 'Mastodon',
                icon: '🐘',
                status: 'supported',
                fields: [
                    { key: 'MASTODON_INSTANCE', label: 'Instance', placeholder: 'mastodon.social' },
                    { key: 'MASTODON_ACCESS_TOKEN', label: 'Access Token', placeholder: 'Paste your access token', type: 'password' }
                ],
                helpUrl: 'https://docs.joinmastodon.org/client/token/',
                helpText: 'Settings → Development → New Application'
            },
            reddit: {
                name: 'Reddit',
                icon: '🔶',
                status: 'supported',
                fields: [
                    { key: 'REDDIT_CLIENT_ID', label: 'Client ID', placeholder: 'Under app name after creation' },
                    { key: 'REDDIT_CLIENT_SECRET', label: 'Client Secret', placeholder: 'secret field' },
                    { key: 'REDDIT_USERNAME', label: 'Username', placeholder: 'Your Reddit username' },
                    { key: 'REDDIT_PASSWORD', label: 'Password', placeholder: 'Your Reddit password', type: 'password' }
                ],
                helpUrl: 'https://www.reddit.com/prefs/apps',
                helpText: 'Create app → Select "script" type'
            },
            instagram: {
                name: 'Instagram',
                icon: '📸',
                status: 'coming_soon',
                fields: [],
                helpUrl: '#',
                helpText: 'Coming soon - awaiting Meta API approval'
            },
            linkedin: {
                name: 'LinkedIn',
                icon: '💼',
                status: 'coming_soon',
                fields: [],
                helpUrl: '#',
                helpText: 'Coming soon - awaiting API approval'
            },
            facebook: {
                name: 'Facebook',
                icon: '📘',
                status: 'coming_soon',
                fields: [],
                helpUrl: '#',
                helpText: 'Coming soon - awaiting Meta API approval'
            },
            tiktok: {
                name: 'TikTok',
                icon: '🎵',
                status: 'coming_soon',
                fields: [],
                helpUrl: '#',
                helpText: 'Coming soon - awaiting API approval'
            },
            youtube: {
                name: 'YouTube',
                icon: '📺',
                status: 'coming_soon',
                fields: [],
                helpUrl: '#',
                helpText: 'Coming soon - awaiting API approval'
            },
            threads: {
                name: 'Threads',
                icon: '🧵',
                status: 'coming_soon',
                fields: [],
                helpUrl: '#',
                helpText: 'Coming soon - awaiting Meta API approval'
            },
            pinterest: {
                name: 'Pinterest',
                icon: '📌',
                status: 'coming_soon',
                fields: [],
                helpUrl: '#',
                helpText: 'Coming soon - awaiting API approval'
            }
        };
        

        
        let savedCredentials = {};
        
        function openSettings() {
            renderPlatformSettings();
            document.getElementById('settingsModal').classList.add('active');
        }
        
        function closeSettings() {
            document.getElementById('settingsModal').classList.remove('active');
        }
        
        function renderPlatformSettings() {
            const container = document.getElementById('platformSettings');
            container.innerHTML = '';
            
            for (const [pid, config] of Object.entries(platformCreds)) {
                if (config.status === 'removed') continue;
                
                const isComingSoon = config.status === 'coming_soon';
                const isConnected = !isComingSoon && checkPlatformConnected(pid);
                const card = document.createElement('div');
                card.className = 'platform-card' + (isComingSoon ? ' coming-soon' : '');
                card.dataset.platform = pid;
                
                let fieldsHtml = '';
                if (isComingSoon) {
                    fieldsHtml = '<p class="coming-soon-msg">🚧 ' + config.helpText + '</p>';
                } else {
                    config.fields.forEach(function(field) {
                        const savedVal = savedCredentials[field.key] || '';
                        const inputType = field.type || 'text';
                        fieldsHtml += '<div class="cred-field">' +
                            '<label>' + field.label + '</label>' +
                            '<input type="' + inputType + '" data-key="' + field.key + '" placeholder="' + field.placeholder + '" value="' + savedVal + '">' +
                            '</div>';
                    });
                }
                
                let statusText = isComingSoon ? '🚧 Coming Soon' : (isConnected ? '● Connected' : '○ Not connected');
                let statusClass = isComingSoon ? 'coming-soon' : (isConnected ? 'connected' : 'not-connected');
                
                card.innerHTML = 
                    '<div class="platform-card-header">' +
                        '<span class="platform-card-icon">' + config.icon + '</span>' +
                        '<span class="platform-card-name">' + config.name + '</span>' +
                        '<span class="platform-card-status ' + statusClass + '">' + statusText + '</span>' +
                        (isComingSoon ? '' : '<span class="platform-card-toggle">▼</span>') +
                    '</div>' +
                    '<div class="platform-card-body">' +
                        fieldsHtml +
                        (isComingSoon ? '' : '<p class="cred-help">' + config.helpText + ' → <a href="' + config.helpUrl + '" target="_blank">Get credentials</a></p>') +
                        (isComingSoon ? '' : '<button class="test-connection" data-platform="' + pid + '">🔌 Test Connection</button>') +
                    '</div>';
                
                container.appendChild(card);
                
                var header = card.querySelector('.platform-card-header');
                if (header) {
                    header.addEventListener('click', function() {
                        card.classList.toggle('expanded');
                    });
                }
                
                var testBtn = card.querySelector('.test-connection');
                if (testBtn) {
                    testBtn.addEventListener('click', function(e) {
                        e.stopPropagation();
                        testConnection(pid);
                    });
                }
            }
        }
        
        function checkPlatformConnected(pid) {
            const config = platformCreds[pid];
            return config.fields.every(function(f) { 
                return savedCredentials[f.key] && savedCredentials[f.key].length > 0; 
            });
        }
        
        function loadCredentials() {
            fetch('/api/credentials')
                .then(function(r) { return r.json(); })
                .then(function(data) { 
                    savedCredentials = data.credentials || {}; 
                })
                .catch(function() { 
                    savedCredentials = {}; 
                });
        }
        
        function saveCredentials() {
            const inputs = document.querySelectorAll('.platform-card input');
            const creds = {};
            inputs.forEach(function(input) {
                const key = input.dataset.key;
                const val = input.value.trim();
                if (val) creds[key] = val;
            });
            
            fetch('/api/credentials', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ credentials: creds })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success) {
                    savedCredentials = creds;
                    addSystemMessage('✅ Credentials saved!');
                    closeSettings();
                }
            })
            .catch(function() {
                addSystemMessage('❌ Failed to save credentials');
            });
        }
        
        function testConnection(pid) {
            const card = document.querySelector('[data-platform="' + pid + '"]');
            const btn = card.querySelector('.test-connection');
            btn.textContent = '⏳ Testing...';
            btn.disabled = true;
            
            // Gather current field values
            const creds = {};
            card.querySelectorAll('input').forEach(function(input) {
                creds[input.dataset.key] = input.value.trim();
            });
            
            fetch('/api/test-connection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ platform: pid, credentials: creds })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                btn.textContent = data.success ? '✅ Connected!' : '❌ Failed';
                setTimeout(function() {
                    btn.textContent = '🔌 Test Connection';
                    btn.disabled = false;
                }, 2000);
                
                const status = card.querySelector('.platform-card-status');
                if (data.success) {
                    status.className = 'platform-card-status connected';
                    status.textContent = '● Connected';
                }
            })
            .catch(function() {
                btn.textContent = '❌ Error';
                setTimeout(function() {
                    btn.textContent = '🔌 Test Connection';
                    btn.disabled = false;
                }, 2000);
            });
        }