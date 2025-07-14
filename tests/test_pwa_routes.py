"""
Comprehensive tests for PWA routes and functionality
"""

import json
import os
from unittest.mock import mock_open, patch

import pytest
from flask import Flask

from src.routes.pwa_routes import pwa_bp


@pytest.fixture
def app():
    """Create test Flask app with PWA blueprint"""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    app.register_blueprint(pwa_bp)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestPWAManifest:
    """Test PWA manifest endpoint"""

    def test_manifest_success(self, client):
        """Test successful manifest serving"""
        manifest_data = {
            "name": "Video Transcriber",
            "short_name": "VT",
            "start_url": "/",
            "display": "standalone",
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(manifest_data))):
            response = client.get("/manifest.json")

        assert response.status_code == 200
        assert response.content_type == "application/manifest+json; charset=utf-8"
        data = json.loads(response.data)
        assert data["name"] == "Video Transcriber"
        assert data["display"] == "standalone"

    def test_manifest_not_found(self, client):
        """Test manifest file not found"""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            response = client.get("/manifest.json")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["error"] == "Manifest not found"


class TestServiceWorker:
    """Test service worker endpoint"""

    def test_service_worker_success(self, client):
        """Test successful service worker serving"""
        sw_content = """
        // Service Worker
        const CACHE_NAME = 'test-cache';
        self.addEventListener('install', event => {
            console.log('SW installed');
        });
        """

        with patch("builtins.open", mock_open(read_data=sw_content)):
            response = client.get("/sw.js")

        assert response.status_code == 200
        assert response.content_type == "application/javascript; charset=utf-8"
        assert "Service-Worker-Allowed" in response.headers
        assert response.headers["Service-Worker-Allowed"] == "/"
        assert response.headers["Cache-Control"] == "no-cache"
        assert "CACHE_NAME" in response.data.decode()

    def test_service_worker_not_found(self, client):
        """Test service worker file not found"""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            response = client.get("/sw.js")

        assert response.status_code == 404
        assert "console.error('Service worker not found');" in response.data.decode()


class TestPWAStatus:
    """Test PWA status endpoint"""

    def test_pwa_status_default(self, client):
        """Test PWA status with default user agent"""
        response = client.get("/api/pwa/status")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["pwa_enabled"] is True
        assert data["is_standalone"] is False
        assert "capabilities" in data
        assert data["capabilities"]["service_worker"] is True
        assert data["capabilities"]["offline_support"] is True
        assert "version" in data
        assert "last_updated" in data

    def test_pwa_status_mobile_user_agent(self, client):
        """Test PWA status with mobile user agent"""
        response = client.get(
            "/api/pwa/status",
            headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
            },
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["capabilities"]["camera_access"] is True
        assert data["capabilities"]["share_api"] is True

    def test_pwa_status_standalone_mode(self, client):
        """Test PWA status in standalone mode"""
        response = client.get(
            "/api/pwa/status?standalone=true", headers={"X-Requested-With": "PWA"}
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["is_standalone"] is True


class TestInstallStats:
    """Test PWA installation statistics"""

    def test_track_install_prompt_shown(self, client):
        """Test tracking install prompt shown event"""
        data = {"event_type": "prompt_shown"}

        response = client.post(
            "/api/pwa/install-stats", json=data, content_type="application/json"
        )

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["success"] is True
        assert result["event_type"] == "prompt_shown"

    def test_track_install_accepted(self, client):
        """Test tracking install accepted event"""
        data = {"event_type": "install_accepted"}

        response = client.post(
            "/api/pwa/install-stats", json=data, content_type="application/json"
        )

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["success"] is True
        assert result["event_type"] == "install_accepted"

    def test_track_install_no_data(self, client):
        """Test tracking with no data"""
        response = client.post("/api/pwa/install-stats")

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["success"] is True


class TestCacheStats:
    """Test PWA cache statistics"""

    def test_cache_stats(self, client):
        """Test cache statistics endpoint"""
        response = client.get("/api/pwa/cache-stats")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "stats" in data
        stats = data["stats"]
        assert "cache_version" in stats
        assert "static_files_cached" in stats
        assert "dynamic_content_cached" in stats
        assert "estimated_storage_mb" in stats
        assert "last_cache_update" in stats
        assert "offline_sessions_available" in stats


class TestPushNotifications:
    """Test push notification endpoints"""

    def test_get_vapid_key(self, client):
        """Test VAPID key endpoint"""
        response = client.get("/api/push/vapid-key")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "publicKey" in data
        assert len(data["publicKey"]) > 0

    def test_subscribe_to_push(self, client):
        """Test push subscription"""
        subscription_data = {
            "endpoint": "https://example.com/push/endpoint",
            "keys": {"p256dh": "test-key", "auth": "test-auth"},
        }

        response = client.post(
            "/api/push/subscribe",
            json=subscription_data,
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "subscription_id" in data

    def test_subscribe_no_data(self, client):
        """Test push subscription with no data"""
        response = client.post("/api/push/subscribe")

        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False
        assert "error" in data

    def test_unsubscribe_from_push(self, client):
        """Test push unsubscription"""
        data = {"endpoint": "https://example.com/push/endpoint"}

        response = client.post(
            "/api/push/unsubscribe", json=data, content_type="application/json"
        )

        assert response.status_code == 200
        result = json.loads(response.data)

        assert result["success"] is True

    def test_unsubscribe_no_endpoint(self, client):
        """Test push unsubscription with no endpoint"""
        response = client.post(
            "/api/push/unsubscribe", json={}, content_type="application/json"
        )

        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False


class TestOfflineQueue:
    """Test offline queue management"""

    def test_get_offline_queue(self, client):
        """Test getting offline queue"""
        response = client.get("/api/pwa/offline-queue")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "queue" in data
        assert "queue_length" in data
        assert "processing" in data
        assert isinstance(data["queue"], list)

    def test_add_to_offline_queue(self, client):
        """Test adding to offline queue"""
        queue_item = {
            "filename": "test-video.mp4",
            "action": "transcribe",
            "timestamp": "2025-07-14T13:00:00Z",
        }

        response = client.post(
            "/api/pwa/offline-queue", json=queue_item, content_type="application/json"
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "queue_id" in data

    def test_add_to_offline_queue_no_data(self, client):
        """Test adding to offline queue with no data"""
        response = client.post("/api/pwa/offline-queue")

        assert response.status_code == 400
        data = json.loads(response.data)

        assert data["success"] is False


class TestCacheManagement:
    """Test cache management endpoints"""

    def test_clear_cache(self, client):
        """Test cache clearing"""
        response = client.post("/api/pwa/clear-cache")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "message" in data

    def test_update_check(self, client):
        """Test update checking"""
        response = client.get("/api/pwa/update-check")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "update_available" in data
        assert "current_version" in data
        assert "latest_version" in data
        assert "release_notes" in data


class TestOfflineTemplate:
    """Test offline template route"""

    def test_offline_page(self, client):
        """Test offline page rendering"""
        with patch("flask.render_template") as mock_render:
            mock_render.return_value = "<html>Offline Page</html>"

            response = client.get("/offline")

            assert response.status_code == 200
            mock_render.assert_called_once_with("offline.html")


class TestErrorHandlers:
    """Test PWA-specific error handlers"""

    def test_pwa_404_error(self, client):
        """Test PWA 404 error handler"""
        response = client.get("/api/pwa/nonexistent")

        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["success"] is False
        assert data["error"] == "PWA resource not found"
        assert "available_endpoints" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
