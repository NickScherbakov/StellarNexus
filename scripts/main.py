import requests
import json
from datetime import datetime
import os
import pandas as pd
import matplotlib.pyplot as plt

# Configuration
GH_TOKEN = os.getenv('GH_TOKEN')
HEADERS = {'Authorization': f'token {GH_TOKEN}'} if GH_TOKEN else {}
DATA_FILE = 'data/top_repos_history.json'
CHART_FILE = 'docs/assets/stars_trend.png'

def fetch_top_repos():
    """Fetches top 10 repos from GitHub API."""
    url = 'https://api.github.com/search/repositories?q=stars:>0&sort=stars&order=desc&per_page=10'
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data['items']

def update_history(items):
    """Appends a new daily snapshot to the history JSON file."""
    date_today = datetime.now().strftime('%Y-%m-%d')
    
    # Load existing history or create empty list
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            history = json.load(f)
    else:
        history = []
    
    # Create today's entry
    today_entry = {
        "date": date_today,
        "repositories": []
    }
    
    for i, repo in enumerate(items[:10], 1):  # Top 10
        repo_data = {
            "name": repo['name'],
            "stars": repo['stargazers_count'],
            "rank": i,
            "url": repo['html_url'],
            "description": repo['description'] or ""
        }
        today_entry["repositories"].append(repo_data)
    
    # Append to history
    history.append(today_entry)
    
    # Save back to file
    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    return today_entry

def generate_chart():
    """Reads historical data and generates a line chart of star growth."""
    if not os.path.exists(DATA_FILE):
        print("No historical data found. Skipping chart generation.")
        return
    
    with open(DATA_FILE, 'r') as f:
        history = json.load(f)
    
    if not history:
        print("No data to plot.")
        return
    
    # Prepare data for plotting
    dates = []
    repo_data = {}
    
    for entry in history:
        date = entry['date']
        dates.append(date)
        for repo in entry['repositories']:
            name = repo['name']
            stars = repo['stars']
            if name not in repo_data:
                repo_data[name] = []
            repo_data[name].append(stars)
    
    # Create DataFrame
    df_data = {'date': dates}
    for name, stars_list in repo_data.items():
        df_data[name] = stars_list
    
    df = pd.DataFrame(df_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    # Plot
    plt.figure(figsize=(12, 8))
    for column in df.columns:
        plt.plot(df.index, df[column], label=column, marker='o')
    
    plt.title('GitHub Top Repositories Star Growth')
    plt.xlabel('Date')
    plt.ylabel('Stars')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()
    print(f"Chart saved to {CHART_FILE}")

def update_readme(today_data):
    """Updates the README.md file with the current ranking table."""
    if not today_data:
        return
    
    # Load existing README or create basic structure
    readme_path = 'README.md'
    if os.path.exists(readme_path):
        with open(readme_path, 'r') as f:
            content = f.read()
    else:
        content = "# GitHub Top Stars Tracker\n\n## Current Top 10 Repositories\n\n| Rank | Repository | Stars | Description |\n|------|------------|-------|-------------|\n\n## Star Growth Chart\n\n![Star Growth](docs/assets/stars_trend.png)\n"
    
    # Calculate star gains (if previous data exists)
    star_gains = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            history = json.load(f)
        if len(history) > 1:
            prev_entry = history[-2]  # Previous day
            prev_stars = {repo['name']: repo['stars'] for repo in prev_entry['repositories']}
            for repo in today_data['repositories']:
                name = repo['name']
                current = repo['stars']
                previous = prev_stars.get(name, current)
                star_gains[name] = current - previous
    
    # Generate table
    table_lines = ["| Rank | Repository | Stars | Stars Gained | Description |"]
    table_lines.append("|------|------------|-------|--------------|-------------|")
    
    for repo in today_data['repositories']:
        name = repo['name']
        stars = repo['stars']
        rank = repo['rank']
        url = repo['url']
        desc = repo['description'][:100] + "..." if len(repo['description']) > 100 else repo['description']
        gain = star_gains.get(name, 0)
        table_lines.append(f"| {rank} | [{name}]({url}) | {stars:,} | +{gain} | {desc} |")
    
    table = "\n".join(table_lines)
    
    # Replace table in README
    import re
    pattern = r'## Current Top 10 Repositories\n\n\|.*?\n\|.*?\n(?:\|.*?\n)*'
    new_content = re.sub(pattern, f'## Current Top 10 Repositories\n\n{table}\n', content, flags=re.DOTALL)
    
    with open(readme_path, 'w') as f:
        f.write(new_content)
    
    print("README.md updated with current rankings.")

if __name__ == '__main__':
    date_today = datetime.now().strftime('%Y-%m-%d')
    try:
        top_repos = fetch_top_repos()
        today_data = update_history(top_repos)
        generate_chart()
        update_readme(today_data)
        print("Data update successful!")
    except Exception as e:
        print(f"Error: {e}")