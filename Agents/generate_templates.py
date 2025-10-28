"""
Script to generate all admin dashboard templates with black & white theme
"""
import os

# Base template
BASE_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}MicroLearning Admin{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        'sans': ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
                    },
                }
            }
        }
    </script>
    <style>
        * { font-family: 'Inter', system-ui, -apple-system, sans-serif; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #f5f5f5; }
        ::-webkit-scrollbar-thumb { background: #a3a3a3; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #737373; }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body class="bg-neutral-50 text-neutral-900 antialiased">
    <aside class="fixed top-0 left-0 h-screen w-64 bg-white border-r border-neutral-200 z-50">
        <div class="flex flex-col h-full">
            <div class="px-6 py-6 border-b border-neutral-200">
                <h1 class="text-xl font-semibold text-neutral-900 tracking-tight">
                    <svg class="inline-block w-6 h-6 mr-2 -mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                    </svg>
                    MicroLearning
                </h1>
            </div>
            
            <nav class="flex-1 px-3 py-4 overflow-y-auto">
                <ul class="space-y-1">
                    <li>
                        <a href="{{ url_for('dashboard') }}" 
                           class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all
                                  {% if request.endpoint == 'dashboard' %}bg-neutral-900 text-white{% else %}text-neutral-700 hover:bg-neutral-100{% endif %}">
                            <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
                            </svg>
                            Dashboard
                        </a>
                    </li>
                    <li>
                        <a href="{{ url_for('users') }}" 
                           class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all
                                  {% if request.endpoint in ['users', 'user_detail'] %}bg-neutral-900 text-white{% else %}text-neutral-700 hover:bg-neutral-100{% endif %}">
                            <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
                            </svg>
                            Users
                        </a>
                    </li>
                    <li>
                        <a href="{{ url_for('videos') }}" 
                           class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all
                                  {% if request.endpoint in ['videos', 'add_video', 'edit_video'] %}bg-neutral-900 text-white{% else %}text-neutral-700 hover:bg-neutral-100{% endif %}">
                            <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                            Videos
                        </a>
                    </li>
                    <li>
                        <a href="{{ url_for('questions') }}" 
                           class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all
                                  {% if request.endpoint == 'questions' %}bg-neutral-900 text-white{% else %}text-neutral-700 hover:bg-neutral-100{% endif %}">
                            <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                            Questions
                        </a>
                    </li>
                    <li>
                        <a href="{{ url_for('analytics') }}" 
                           class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all
                                  {% if request.endpoint == 'analytics' %}bg-neutral-900 text-white{% else %}text-neutral-700 hover:bg-neutral-100{% endif %}">
                            <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                            </svg>
                            Analytics
                        </a>
                    </li>
                    <li>
                        <a href="{{ url_for('documents') }}" 
                           class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all
                                  {% if request.endpoint == 'documents' %}bg-neutral-900 text-white{% else %}text-neutral-700 hover:bg-neutral-100{% endif %}">
                            <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                            </svg>
                            Documents
                        </a>
                    </li>
                </ul>
            </nav>
            
            <div class="px-3 py-4 border-t border-neutral-200">
                <a href="{{ url_for('logout') }}" 
                   class="flex items-center px-3 py-2.5 text-sm font-medium text-neutral-700 hover:bg-neutral-100 rounded-lg transition-all">
                    <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                    </svg>
                    Logout
                </a>
            </div>
        </div>
    </aside>
    
    <main class="ml-64 min-h-screen">
        <div class="max-w-7xl mx-auto px-8 py-8">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <div class="mb-6 space-y-2">
                        {% for category, message in messages %}
                            <div class="px-4 py-3 rounded-lg border text-sm font-medium
                                        {% if category == 'success' %}bg-neutral-50 border-neutral-900 text-neutral-900{% endif %}
                                        {% if category == 'error' %}bg-neutral-900 border-neutral-900 text-white{% endif %}
                                        {% if category == 'warning' %}bg-neutral-100 border-neutral-400 text-neutral-900{% endif %}
                                        {% if category == 'info' %}bg-neutral-50 border-neutral-300 text-neutral-700{% endif %}"
                                 role="alert">
                                <div class="flex items-center justify-between">
                                    <span>{{ message }}</span>
                                    <button type="button" onclick="this.parentElement.parentElement.remove()" 
                                            class="ml-4 text-current opacity-70 hover:opacity-100">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            
            {% block content %}{% endblock %}
        </div>
    </main>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
'''

# Login template
LOGIN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - MicroLearning Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        'sans': ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
                    },
                }
            }
        }
    </script>
</head>
<body class="bg-white antialiased">
    <div class="min-h-screen flex items-center justify-center px-4 py-12">
        <div class="w-full max-w-md">
            <div class="text-center mb-10">
                <div class="inline-flex items-center justify-center w-16 h-16 mb-6 border-2 border-neutral-900 rounded-lg">
                    <svg class="w-8 h-8 text-neutral-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                    </svg>
                </div>
                <h1 class="text-3xl font-semibold text-neutral-900 tracking-tight mb-2">MicroLearning</h1>
                <p class="text-sm text-neutral-600 font-medium">Admin Dashboard</p>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <div class="mb-6 space-y-2">
                        {% for category, message in messages %}
                            <div class="px-4 py-3 rounded-lg border text-sm font-medium
                                        {% if category == 'error' %}bg-neutral-900 border-neutral-900 text-white{% else %}bg-neutral-50 border-neutral-300 text-neutral-900{% endif %}"
                                 role="alert">
                                {{ message }}
                            </div>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            
            <form method="POST" class="space-y-5">
                <div>
                    <label for="username" class="block text-sm font-medium text-neutral-900 mb-2">Username</label>
                    <input type="text" id="username" name="username" required autofocus
                           class="w-full px-4 py-3 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-all duration-150 bg-white text-neutral-900 placeholder:text-neutral-400"
                           placeholder="Enter your username">
                </div>
                
                <div>
                    <label for="password" class="block text-sm font-medium text-neutral-900 mb-2">Password</label>
                    <input type="password" id="password" name="password" required
                           class="w-full px-4 py-3 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-all duration-150 bg-white text-neutral-900 placeholder:text-neutral-400"
                           placeholder="Enter your password">
                </div>
                
                <button type="submit" 
                        class="w-full px-4 py-3 text-sm font-semibold text-white bg-neutral-900 rounded-lg hover:bg-neutral-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-neutral-900 transition-all duration-150 active:bg-black">
                    Sign In
                </button>
            </form>
            
            <div class="mt-8 text-center">
                <p class="text-xs text-neutral-500">Secure authentication required for dashboard access</p>
            </div>
        </div>
    </div>
</body>
</html>
'''

# Dashboard template - simplified placeholder
DASHBOARD_HTML = '''{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<div class="mb-8">
    <h1 class="text-3xl font-semibold text-neutral-900 tracking-tight">Dashboard</h1>
    <p class="mt-2 text-sm text-neutral-600">Overview of your MicroLearning platform</p>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <div class="text-sm font-medium text-neutral-600 mb-1">Total Users</div>
        <div class="text-3xl font-semibold text-neutral-900">{{ stats.total_users }}</div>
        <div class="text-xs text-neutral-500 mt-1">{{ stats.active_users }} active</div>
    </div>
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <div class="text-sm font-medium text-neutral-600 mb-1">Total Videos</div>
        <div class="text-3xl font-semibold text-neutral-900">{{ stats.total_videos }}</div>
        <div class="text-xs text-neutral-500 mt-1">{{ stats.active_videos }} active</div>
    </div>
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <div class="text-sm font-medium text-neutral-600 mb-1">Quiz Attempts</div>
        <div class="text-3xl font-semibold text-neutral-900">{{ stats.total_quiz_attempts }}</div>
        <div class="text-xs text-neutral-500 mt-1">{{ stats.total_questions }} questions</div>
    </div>
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <div class="text-sm font-medium text-neutral-600 mb-1">Videos Watched</div>
        <div class="text-3xl font-semibold text-neutral-900">{{ stats.videos_watched }}</div>
        <div class="text-xs text-neutral-500 mt-1">Completed</div>
    </div>
</div>

<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <h2 class="text-lg font-semibold text-neutral-900 mb-4">User Activity</h2>
        <div class="flex justify-around">
            <div class="text-center">
                <div class="text-2xl font-semibold text-neutral-900">{{ stats.active_today }}</div>
                <div class="text-xs text-neutral-600 mt-1">Active Today</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-semibold text-neutral-900">{{ stats.active_this_week }}</div>
                <div class="text-xs text-neutral-600 mt-1">Active This Week</div>
            </div>
        </div>
    </div>
    
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <h2 class="text-lg font-semibold text-neutral-900 mb-4">Quick Actions</h2>
        <div class="space-y-2">
            <a href="{{ url_for('add_video') }}" class="block px-4 py-2 text-sm font-medium text-center text-white bg-neutral-900 rounded-lg hover:bg-neutral-800 transition-colors">Add New Video</a>
            <a href="{{ url_for('analytics') }}" class="block px-4 py-2 text-sm font-medium text-center text-neutral-900 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50 transition-colors">View Analytics</a>
        </div>
    </div>
</div>
{% endblock %}
'''

# Create templates directory if it doesn't exist
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
os.makedirs(template_dir, exist_ok=True)

# Write all template files
templates = {
    'base.html': BASE_HTML,
    'login.html': LOGIN_HTML,
    'dashboard.html': DASHBOARD_HTML,
}

for filename, content in templates.items():
    filepath = os.path.join(template_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'✓ Created {filename}')

print(f'\nSuccessfully created {len(templates)} template files!')
print('Note: Remaining templates (users.html, videos.html, etc.) need to be created')
print('Run the dashboard to test: python admin_dashboard.py')
