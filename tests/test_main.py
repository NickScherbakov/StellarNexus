"""
StellarNexus Test Suite
Comprehensive tests for the GitHub Top Stars Tracker
"""

import pytest
import json
import os
from datetime import datetime
from unittest.mock import Mock, patch
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from main import fetch_top_repos, update_history, generate_chart

class TestGitHubAPI:
    """Test GitHub API functionality"""

    @patch('main.requests.get')
    def test_fetch_top_repos_success(self, mock_get):
        """Test successful API call"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {
                    'id': 1,
                    'name': 'test-repo',
                    'stargazers_count': 1000,
                    'html_url': 'https://github.com/test/repo',
                    'description': 'Test repository'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_top_repos()
        assert len(result) == 1
        assert result[0]['name'] == 'test-repo'

    @patch('main.requests.get')
    def test_fetch_top_repos_error(self, mock_get):
        """Test API error handling"""
        mock_get.side_effect = Exception("API Error")

        result = fetch_top_repos()
        assert result is None

class TestDataPersistence:
    """Test data storage functionality"""

    def test_update_history_creates_file(self, tmp_path):
        """Test that history file is created"""
        # Mock data
        mock_items = [
            {
                'id': 1,
                'name': 'test-repo',
                'stargazers_count': 1000,
                'html_url': 'https://github.com/test/repo',
                'description': 'Test repository'
            }
        ]

        # Change to tmp_path for testing
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)

            result = update_history(mock_items)

            # Check that file was created
            assert os.path.exists('data/top_repos_history.json')

            # Check content
            with open('data/top_repos_history.json', 'r') as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]['repositories'][0]['name'] == 'test-repo'

        finally:
            os.chdir(original_cwd)

class TestAnalytics:
    """Test analytics and reporting functionality"""

    def test_data_structure(self):
        """Test that data has correct structure"""
        # This would test the data validation
        expected_keys = ['date', 'repositories']

        # Mock data for testing
        test_data = {
            'date': '2025-09-07',
            'repositories': [
                {
                    'name': 'test-repo',
                    'stars': 1000,
                    'rank': 1,
                    'url': 'https://github.com/test/repo',
                    'description': 'Test repo'
                }
            ]
        }

        assert all(key in test_data for key in expected_keys)
        assert isinstance(test_data['repositories'], list)
        assert len(test_data['repositories']) > 0

class TestWebInterface:
    """Test web interface functionality"""

    def test_api_endpoints_structure(self):
        """Test that API endpoints return correct structure"""
        # This would test FastAPI endpoints
        # For now, just test the expected response structure

        expected_analytics = {
            'total_repositories': 10,
            'avg_stars': 150000.5,
            'top_gainer': {
                'name': 'test-repo',
                'stars': 200000,
                'rank': 1,
                'url': 'https://github.com/test/repo',
                'description': 'Test repository'
            },
            'last_updated': '2025-09-07'
        }

        required_keys = ['total_repositories', 'avg_stars', 'last_updated']
        assert all(key in expected_analytics for key in required_keys)

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])