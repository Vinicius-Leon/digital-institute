from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def celery_eager_mode():
    """Faz o Celery executar tasks de forma síncrona nos testes."""
    from institute.worker import celery_app

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False


@pytest.mark.unit
class TestSendNotificationTask:
    def test_send_notification_returns_logged_status(self):
        """Task deve executar e retornar status logged."""
        from institute.tasks import send_notification

        # Chama a função diretamente, sem passar pelo broker
        result = send_notification(
            user_id="123",
            event="test_event",
            payload={"key": "value"},
        )
        assert result["status"] == "logged"
        assert result["user_id"] == "123"
        assert result["event"] == "test_event"

    def test_send_notification_logs_processing(self):
        """Task deve logar o processamento."""
        from institute.tasks import send_notification

        with patch("institute.tasks.logger") as mock_logger:
            send_notification(
                user_id="456",
                event="user_registered",
                payload={},
            )
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args
            assert "Processing notification" in call_kwargs[0][0]


@pytest.mark.unit
class TestWorkerConfig:
    def test_celery_app_is_configured(self):
        """Worker deve estar configurado com as opções corretas."""
        from institute.worker import celery_app

        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.worker_prefetch_multiplier == 1
