import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Configuration
CONTENT_DIR = Path('content')
PUBLIC_DIR = Path('public')

def load_data():
    """Scans content directory for JSON files and loads them sorted by date."""
    news_data = []
    # Walk through the content directory
    for root, _, files in os.walk(CONTENT_DIR):
        for file in files:
            if file.endswith('.json'):
                file_path = Path(root) / file
                # Try to extract date from filename (expecting YYYY-MM-DD.json)
                try:
                    date_str = file_path.stem
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                    
                    news_data.append({
                        'date': date_obj,
                        'content': content,
                        'file_path': file_path
                    })
                except ValueError:
                    print(f"Skipping file with invalid date format: {file_path}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    # Sort by date descending (newest first)
    news_data.sort(key=lambda x: x['date'], reverse=True)
    return news_data

def ensure_public_dir():
    """Ensures the public directory exists."""
    if not PUBLIC_DIR.exists():
        PUBLIC_DIR.mkdir()

def get_relative_path(from_path, to_path):
    """Calculates relative path for links."""
    return os.path.relpath(to_path, from_path.parent)

def generate_navbar(relative_root):
    """Generates a simple navbar."""
    return f'''
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
        <div class="container">
            <a class="navbar-brand" href="{relative_root}/index.html">News Morning Paper</a>
        </div>
    </nav>
    '''

def generate_daily_page(item, previous_date=None, next_date=None):
    """Generates an HTML page for a specific day's news."""
    date_obj = item['date']
    content = item['content']
    
    # Create directory year/month/
    year_dir = PUBLIC_DIR / str(date_obj.year)
    month_dir = year_dir / f"{date_obj.month:02d}"
    month_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = month_dir / f"{date_obj.day:02d}.html"
    relative_root = "../../.." # consistently 3 levels deep: year/month/day.html
    
    # Group content by section
    sections = defaultdict(list)
    for entry in content:
        section = entry.get('版块', 'Uncategorized')
        sections[section].append(entry)
    
    # Generate HTML content
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{date_obj} News Morning Paper</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .news-card {{ transition: transform 0.2s; }}
        .news-card:hover {{ transform: translateY(-5px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .section-header {{ border-left: 5px solid #0d6efd; padding-left: 10px; margin-bottom: 20px; }}
    </style>
</head>
<body class="bg-light">
    {generate_navbar(relative_root)}
    
    <div class="container">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>{date_obj.strftime('%Y-%m-%d')} News</h1>
            <div>
                {f'<a href="{get_relative_path(output_file, get_daily_path(next_date))}" class="btn btn-outline-primary me-2">&larr; Next Day</a>' if next_date else '<button class="btn btn-outline-secondary me-2" disabled>&larr; Next Day</button>'}
                {f'<a href="{get_relative_path(output_file, get_daily_path(previous_date))}" class="btn btn-outline-primary">Previous Day &rarr;</a>' if previous_date else '<button class="btn btn-outline-secondary" disabled>Previous Day &rarr;</button>'}
            </div>
        </div>

        {''.join([generate_section_html(name, items) for name, items in sections.items()])}
        
    </div>

    <footer class="bg-dark text-white text-center py-3 mt-5">
        <p>&copy; {datetime.now().year} News Morning Paper. All rights reserved.</p>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated: {output_file}")
    return output_file

def get_daily_path(date_obj):
    if date_obj is None: return None
    return PUBLIC_DIR / str(date_obj.year) / f"{date_obj.month:02d}" / f"{date_obj.day:02d}.html"

def generate_section_html(section_name, items):
    items_html = ""
    for item in items:
        # Check source for favicon or styling (optional, kept simple for now)
        source = item.get('来源', 'Unknown')
        
        items_html += f'''
        <div class="col-md-12 mb-3">
            <div class="card news-card h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <h5 class="card-title text-primary"><a href="{item.get('链接', '#')}" target="_blank" class="text-decoration-none">{item.get('标题', 'No Title')}</a></h5>
                        <span class="badge bg-secondary">{item.get('分类', 'General')}</span>
                    </div>
                    <h6 class="card-subtitle mb-2 text-muted">{source} - {format_time(item.get('发布时间'))}</h6>
                    <p class="card-text">{item.get('内容', '')}</p>
                </div>
            </div>
        </div>
        '''
    
    return f'''
    <div class="row mb-5">
        <div class="col-12">
            <h2 class="section-header">{section_name}</h2>
            <div class="row">
                {items_html}
            </div>
        </div>
    </div>
    '''

def format_time(iso_time_str):
    if not iso_time_str: return ""
    try:
        # Handle simple ISO format output by common tools
        dt = datetime.fromisoformat(iso_time_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M')
    except:
        return iso_time_str

def generate_index(news_data):
    """Generates the main index.html listing the last 5 days."""
    recent_news = news_data[:5] # Last 5 days
    
    list_items = ""
    for item in recent_news:
        date_obj = item['date']
        # Construct path to daily file
        daily_link = f"{date_obj.year}/{date_obj.month:02d}/{date_obj.day:02d}.html"
        
        # Count items
        total_items = len(item['content'])
        
        list_items += f'''
        <a href="{daily_link}" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
            <div>
                <h5 class="mb-1">{date_obj.strftime('%Y-%m-%d')}</h5>
                <small class="text-muted">{total_items} news items</small>
            </div>
            <span class="badge bg-primary rounded-pill">View &rarr;</span>
        </a>
        '''

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>News Morning Paper Archive</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f8f9fa; }}
        .header-section {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 0; margin-bottom: 40px; }}
    </style>
</head>
<body>
    <div class="header-section text-center">
        <div class="container">
            <h1 class="display-4">News Morning Paper</h1>
            <p class="lead">Your daily dose of technology and industry updates.</p>
        </div>
    </div>
    
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card shadow-sm">
                    <div class="card-header bg-white">
                        <h4 class="mb-0">Recent Archives (Last 5 Days)</h4>
                    </div>
                    <div class="list-group list-group-flush">
                        {list_items if list_items else '<div class="list-group-item">No news data found.</div>'}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="text-center py-4 mt-5 text-muted">
        <p>&copy; {datetime.now().year} News Morning Paper</p>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''
    
    with open(PUBLIC_DIR / 'index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Generated: {PUBLIC_DIR / 'index.html'}")

def main():
    ensure_public_dir()
    data = load_data()
    
    if not data:
        print("No data found in content directory.")
        return

    generate_index(data)
    
    # Generate all daily pages, not just last 5, providing prev/next links
    for i, item in enumerate(data):
        # Data is sorted desc (newest first). 
        # Next date (future) is i-1 (if i>0)
        # Prev date (past) is i+1 (if i<len-1)
        next_date = data[i-1]['date'] if i > 0 else None
        prev_date = data[i+1]['date'] if i < len(data) - 1 else None
        
        generate_daily_page(item, prev_date, next_date)

if __name__ == '__main__':
    main()
