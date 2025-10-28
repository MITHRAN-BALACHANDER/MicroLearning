"""
Emergency script to regenerate all corrupted templates
"""
import os

template_dir = os.path.join(os.path.dirname(__file__), 'templates')

# Videos template
VIDEOS_HTML = '''{% extends "base.html" %}
{% block title %}Videos - MicroLearning Admin{% endblock %}
{% block content %}
<div class="flex justify-between items-center mb-8">
    <div>
        <h1 class="text-3xl font-semibold text-neutral-900 tracking-tight">Videos</h1>
        <p class="mt-2 text-sm text-neutral-600">Manage learning content and video library</p>
    </div>
    <a href="{{ url_for('add_video') }}" class="px-4 py-2.5 text-sm font-semibold text-white bg-neutral-900 rounded-lg hover:bg-neutral-800 transition-colors inline-flex items-center">
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Add Video
    </a>
</div>

<div class="bg-white border border-neutral-200 rounded-lg overflow-hidden">
    <table class="min-w-full divide-y divide-neutral-200">
        <thead class="bg-neutral-50">
            <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Title</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Description</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Views</th>
                <th class="px-6 py-3 text-right text-xs font-semibold text-neutral-900 uppercase tracking-wider">Actions</th>
            </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-200">
            {% for video in videos %}
            <tr class="hover:bg-neutral-50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-medium text-neutral-900">{{ video.title }}</div>
                </td>
                <td class="px-6 py-4">
                    <div class="text-sm text-neutral-600 max-w-xs truncate">{{ video.description or 'No description' }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 text-xs font-medium rounded {% if video.is_active %}bg-neutral-900 text-white{% else %}bg-neutral-200 text-neutral-600{% endif %}">
                        {{ 'Active' if video.is_active else 'Inactive' }}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-600">{{ video.view_count or 0 }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    <a href="{{ url_for('edit_video', video_id=video.id) }}" class="text-neutral-900 hover:text-neutral-600">Edit</a>
                    <a href="{{ url_for('toggle_video', video_id=video.id) }}" class="text-neutral-900 hover:text-neutral-600">{{ 'Deactivate' if video.is_active else 'Activate' }}</a>
                    <a href="{{ url_for('delete_video', video_id=video.id) }}" onclick="return confirm('Delete this video?')" class="text-neutral-900 hover:text-neutral-600">Delete</a>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="5" class="px-6 py-8 text-center text-sm text-neutral-500">No videos found. Click "Add Video" to get started.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
'''

# Questions template
QUESTIONS_HTML = '''{% extends "base.html" %}
{% block title %}Questions - MicroLearning Admin{% endblock %}
{% block content %}
<div class="mb-8">
    <h1 class="text-3xl font-semibold text-neutral-900 tracking-tight">Questions</h1>
    <p class="mt-2 text-sm text-neutral-600">Manage quiz questions and assessments</p>
</div>

<div class="bg-white border border-neutral-200 rounded-lg overflow-hidden">
    <table class="min-w-full divide-y divide-neutral-200">
        <thead class="bg-neutral-50">
            <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">ID</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Video</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Question</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Type</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Active</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Created</th>
            </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-200">
            {% for question in questions %}
            <tr class="hover:bg-neutral-50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-900">{{ question.id }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-900">{{ question.video.title if question.video else 'N/A' }}</td>
                <td class="px-6 py-4 text-sm text-neutral-600 max-w-md truncate">{{ question.question_text }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-600">{{ question.question_type }}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 text-xs font-medium rounded {% if question.is_active %}bg-neutral-900 text-white{% else %}bg-neutral-200 text-neutral-600{% endif %}">
                        {{ 'Yes' if question.is_active else 'No' }}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-500">{{ question.created_at.strftime('%Y-%m-%d') if question.created_at else 'N/A' }}</td>
            </tr>
            {% else %}
            <tr><td colspan="6" class="px-6 py-8 text-center text-sm text-neutral-500">No questions found.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
'''

# Documents template
DOCUMENTS_HTML = '''{% extends "base.html" %}
{% block title %}Documents - MicroLearning Admin{% endblock %}
{% block content %}
<div class="mb-8">
    <h1 class="text-3xl font-semibold text-neutral-900 tracking-tight">Documents</h1>
    <p class="mt-2 text-sm text-neutral-600">RAG knowledge base content</p>
</div>

<div class="bg-white border border-neutral-200 rounded-lg overflow-hidden">
    <table class="min-w-full divide-y divide-neutral-200">
        <thead class="bg-neutral-50">
            <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Title</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Type</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Uploaded</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Chunks</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Path</th>
            </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-200">
            {% for doc in documents %}
            <tr class="hover:bg-neutral-50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-900">{{ doc.title }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-600">{{ doc.doc_type }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-500">{{ doc.uploaded_at.strftime('%Y-%m-%d') if doc.uploaded_at else 'N/A' }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-600">{{ doc.chunk_count or 0 }}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 text-xs font-medium rounded {% if doc.is_active %}bg-neutral-900 text-white{% else %}bg-neutral-200 text-neutral-600{% endif %}">
                        {{ 'Active' if doc.is_active else 'Inactive' }}
                    </span>
                </td>
                <td class="px-6 py-4 text-sm text-neutral-500 max-w-xs truncate">{{ doc.file_path }}</td>
            </tr>
            {% else %}
            <tr><td colspan="6" class="px-6 py-8 text-center text-sm text-neutral-500">No documents found.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
'''

# Analytics template
ANALYTICS_HTML = '''{% extends "base.html" %}
{% block title %}Analytics - MicroLearning Admin{% endblock %}
{% block extra_css %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
{% endblock %}
{% block content %}
<div class="mb-8">
    <h1 class="text-3xl font-semibold text-neutral-900 tracking-tight">Analytics</h1>
    <p class="mt-2 text-sm text-neutral-600">Platform insights and performance metrics</p>
</div>

<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <div class="text-sm font-medium text-neutral-600 mb-1">Avg. Completion Rate</div>
        <div class="text-3xl font-semibold text-neutral-900">{{ "%.1f"|format(quiz_stats.avg_score or 0) }}%</div>
    </div>
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <div class="text-sm font-medium text-neutral-600 mb-1">Total Attempts</div>
        <div class="text-3xl font-semibold text-neutral-900">{{ quiz_stats.total_attempts }}</div>
    </div>
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <div class="text-sm font-medium text-neutral-600 mb-1">Active Users</div>
        <div class="text-3xl font-semibold text-neutral-900">{{ user_stats.active_count }}</div>
    </div>
</div>

<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <h3 class="text-lg font-semibold text-neutral-900 mb-4">User Growth</h3>
        <canvas id="userGrowthChart"></canvas>
    </div>
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <h3 class="text-lg font-semibold text-neutral-900 mb-4">Video Completion</h3>
        <canvas id="videoCompletionChart"></canvas>
    </div>
</div>

<div class="bg-white border border-neutral-200 rounded-lg p-6">
    <h3 class="text-lg font-semibold text-neutral-900 mb-4">Top Users</h3>
    <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-neutral-200">
            <thead class="bg-neutral-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">User</th>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Videos Watched</th>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Quiz Attempts</th>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Avg. Score</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-neutral-200">
                {% for user in top_users %}
                <tr class="hover:bg-neutral-50 transition-colors">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-900">{{ user.full_name }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-600">{{ user.videos_watched }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-600">{{ user.quiz_attempts }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-600">{{ "%.1f"|format(user.avg_score or 0) }}%</td>
                </tr>
                {% else %}
                <tr><td colspan="4" class="px-6 py-8 text-center text-sm text-neutral-500">No user data available.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
const userGrowthData = {{ users_by_date|tojson }};
const videoCompletionData = {{ video_completion|tojson }};

const userGrowthChart = new Chart(document.getElementById('userGrowthChart'), {
    type: 'line',
    data: {
        labels: userGrowthData.labels,
        datasets: [{
            label: 'New Users',
            data: userGrowthData.data,
            borderColor: '#171717',
            backgroundColor: 'rgba(23, 23, 23, 0.1)',
            tension: 0.4
        }]
    },
    options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { display: false } } }
});

const videoCompletionChart = new Chart(document.getElementById('videoCompletionChart'), {
    type: 'bar',
    data: {
        labels: videoCompletionData.labels,
        datasets: [{
            label: 'Completions',
            data: videoCompletionData.data,
            backgroundColor: '#171717'
        }]
    },
    options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { display: false } } }
});
</script>
{% endblock %}
'''

# User detail template
USER_DETAIL_HTML = '''{% extends "base.html" %}
{% block title %}{{ user.full_name }} - MicroLearning Admin{% endblock %}
{% block content %}
<div class="mb-8">
    <a href="{{ url_for('users') }}" class="text-sm text-neutral-600 hover:text-neutral-900 inline-flex items-center mb-4">
        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        Back to Users
    </a>
    <h1 class="text-3xl font-semibold text-neutral-900 tracking-tight">{{ user.full_name }}</h1>
    <p class="mt-2 text-sm text-neutral-600">Telegram ID: {{ user.telegram_id }}</p>
</div>

<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <div class="text-sm font-medium text-neutral-600 mb-1">Videos Watched</div>
        <div class="text-3xl font-semibold text-neutral-900">{{ user_stats.videos_watched }}</div>
    </div>
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <div class="text-sm font-medium text-neutral-600 mb-1">Quiz Attempts</div>
        <div class="text-3xl font-semibold text-neutral-900">{{ user_stats.quiz_attempts }}</div>
    </div>
    <div class="bg-white border border-neutral-200 rounded-lg p-6">
        <div class="text-sm font-medium text-neutral-600 mb-1">Avg. Score</div>
        <div class="text-3xl font-semibold text-neutral-900">{{ "%.1f"|format(user_stats.avg_score or 0) }}%</div>
    </div>
</div>

<div class="bg-white border border-neutral-200 rounded-lg p-6 mb-6">
    <h3 class="text-lg font-semibold text-neutral-900 mb-4">Video Progress</h3>
    <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-neutral-200">
            <thead class="bg-neutral-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Video</th>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Status</th>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Last Watched</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-neutral-200">
                {% for prog in progress %}
                <tr class="hover:bg-neutral-50 transition-colors">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-900">{{ prog.video.title }}</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 py-1 text-xs font-medium rounded {% if prog.completed %}bg-neutral-900 text-white{% else %}bg-neutral-200 text-neutral-600{% endif %}">
                            {{ 'Completed' if prog.completed else 'In Progress' }}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-500">{{ prog.last_watched.strftime('%Y-%m-%d %H:%M') if prog.last_watched else 'N/A' }}</td>
                </tr>
                {% else %}
                <tr><td colspan="3" class="px-6 py-8 text-center text-sm text-neutral-500">No video progress found.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<div class="bg-white border border-neutral-200 rounded-lg p-6">
    <h3 class="text-lg font-semibold text-neutral-900 mb-4">Quiz Attempts</h3>
    <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-neutral-200">
            <thead class="bg-neutral-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Video</th>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Score</th>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Completed</th>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider">Date</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-neutral-200">
                {% for attempt in attempts %}
                <tr class="hover:bg-neutral-50 transition-colors">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-900">{{ attempt.video.title }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-600">{{ attempt.score }}%</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 py-1 text-xs font-medium rounded {% if attempt.completed %}bg-neutral-900 text-white{% else %}bg-neutral-200 text-neutral-600{% endif %}">
                            {{ 'Yes' if attempt.completed else 'No' }}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-500">{{ attempt.completed_at.strftime('%Y-%m-%d %H:%M') if attempt.completed_at else 'N/A' }}</td>
                </tr>
                {% else %}
                <tr><td colspan="4" class="px-6 py-8 text-center text-sm text-neutral-500">No quiz attempts found.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
'''

# Add video template
ADD_VIDEO_HTML = '''{% extends "base.html" %}
{% block title %}Add Video - MicroLearning Admin{% endblock %}
{% block content %}
<div class="mb-8">
    <a href="{{ url_for('videos') }}" class="text-sm text-neutral-600 hover:text-neutral-900 inline-flex items-center mb-4">
        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        Back to Videos
    </a>
    <h1 class="text-3xl font-semibold text-neutral-900 tracking-tight">Add New Video</h1>
</div>

<div class="bg-white border border-neutral-200 rounded-lg p-8 max-w-2xl">
    <form method="POST" class="space-y-6">
        <div>
            <label for="title" class="block text-sm font-medium text-neutral-900 mb-2">Title</label>
            <input type="text" id="title" name="title" required
                   class="w-full px-4 py-2.5 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-all bg-white text-neutral-900">
        </div>
        
        <div>
            <label for="description" class="block text-sm font-medium text-neutral-900 mb-2">Description</label>
            <textarea id="description" name="description" rows="4"
                      class="w-full px-4 py-2.5 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-all bg-white text-neutral-900"></textarea>
        </div>
        
        <div>
            <label for="gemini_file_id" class="block text-sm font-medium text-neutral-900 mb-2">Gemini File ID</label>
            <input type="text" id="gemini_file_id" name="gemini_file_id" required
                   class="w-full px-4 py-2.5 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-all bg-white text-neutral-900">
            <p class="mt-1.5 text-xs text-neutral-500">Upload video to Gemini and enter the file ID</p>
        </div>
        
        <div>
            <label for="order_index" class="block text-sm font-medium text-neutral-900 mb-2">Order</label>
            <input type="number" id="order_index" name="order_index" value="0"
                   class="w-full px-4 py-2.5 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-all bg-white text-neutral-900">
        </div>
        
        <div class="flex items-center">
            <input type="checkbox" id="is_active" name="is_active" checked
                   class="w-4 h-4 text-neutral-900 border-neutral-300 rounded focus:ring-neutral-900">
            <label for="is_active" class="ml-2 text-sm font-medium text-neutral-900">Active</label>
        </div>
        
        <div class="flex gap-3 pt-4">
            <button type="submit" class="px-6 py-2.5 text-sm font-semibold text-white bg-neutral-900 rounded-lg hover:bg-neutral-800 transition-colors">
                Create Video
            </button>
            <a href="{{ url_for('videos') }}" class="px-6 py-2.5 text-sm font-semibold text-neutral-900 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50 transition-colors">
                Cancel
            </a>
        </div>
    </form>
</div>
{% endblock %}
'''

# Edit video template
EDIT_VIDEO_HTML = '''{% extends "base.html" %}
{% block title %}Edit Video - MicroLearning Admin{% endblock %}
{% block content %}
<div class="mb-8">
    <a href="{{ url_for('videos') }}" class="text-sm text-neutral-600 hover:text-neutral-900 inline-flex items-center mb-4">
        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        Back to Videos
    </a>
    <h1 class="text-3xl font-semibold text-neutral-900 tracking-tight">Edit Video</h1>
</div>

<div class="bg-white border border-neutral-200 rounded-lg p-8 max-w-2xl">
    <form method="POST" class="space-y-6">
        <div>
            <label for="title" class="block text-sm font-medium text-neutral-900 mb-2">Title</label>
            <input type="text" id="title" name="title" value="{{ video.title }}" required
                   class="w-full px-4 py-2.5 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-all bg-white text-neutral-900">
        </div>
        
        <div>
            <label for="description" class="block text-sm font-medium text-neutral-900 mb-2">Description</label>
            <textarea id="description" name="description" rows="4"
                      class="w-full px-4 py-2.5 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-all bg-white text-neutral-900">{{ video.description }}</textarea>
        </div>
        
        <div>
            <label for="gemini_file_id" class="block text-sm font-medium text-neutral-900 mb-2">Gemini File ID</label>
            <input type="text" id="gemini_file_id" name="gemini_file_id" value="{{ video.gemini_file_id }}" required
                   class="w-full px-4 py-2.5 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-all bg-white text-neutral-900">
        </div>
        
        <div>
            <label for="order_index" class="block text-sm font-medium text-neutral-900 mb-2">Order</label>
            <input type="number" id="order_index" name="order_index" value="{{ video.order_index }}"
                   class="w-full px-4 py-2.5 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-all bg-white text-neutral-900">
        </div>
        
        <div class="flex items-center">
            <input type="checkbox" id="is_active" name="is_active" {% if video.is_active %}checked{% endif %}
                   class="w-4 h-4 text-neutral-900 border-neutral-300 rounded focus:ring-neutral-900">
            <label for="is_active" class="ml-2 text-sm font-medium text-neutral-900">Active</label>
        </div>
        
        <div class="flex gap-3 pt-4">
            <button type="submit" class="px-6 py-2.5 text-sm font-semibold text-white bg-neutral-900 rounded-lg hover:bg-neutral-800 transition-colors">
                Save Changes
            </button>
            <a href="{{ url_for('videos') }}" class="px-6 py-2.5 text-sm font-semibold text-neutral-900 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50 transition-colors">
                Cancel
            </a>
        </div>
    </form>
</div>
{% endblock %}
'''

# Write all templates
templates = {
    'videos.html': VIDEOS_HTML,
    'questions.html': QUESTIONS_HTML,
    'documents.html': DOCUMENTS_HTML,
    'analytics.html': ANALYTICS_HTML,
    'user_detail.html': USER_DETAIL_HTML,
    'add_video.html': ADD_VIDEO_HTML,
    'edit_video.html': EDIT_VIDEO_HTML,
}

print('Creating clean templates...')
for filename, content in templates.items():
    filepath = os.path.join(template_dir, filename)
    # Force overwrite with clean content
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f'✓ Created {filename} ({len(content)} bytes)')

print(f'\n✅ Successfully created {len(templates)} clean template files!')
print('Templates are ready. Restart Flask server to test.')
