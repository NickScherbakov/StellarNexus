import requests
import json
from datetime import datetime
import os


def fetch_github_data():
    """Получение данных о топ-10 репозиториях с GitHub"""
    url = "https://api.github.com/search/repositories?q=stars:>0&sort=stars&order=desc&per_page=10"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return None


def save_data(data):
    """Сохранение данных в JSON файл"""
    if not data:
        return

    filename = f"data/github_top_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Данные сохранены в {filename}")


if __name__ == "__main__":
    print("Запуск получения данных GitHub...")
    github_data = fetch_github_data()
    save_data(github_data)
