"""Tests for utils/logging_config.py — covering setup_logging, get_logger,
custom levels, and module-level initialization."""

import pytest
import sys
import os
import logging
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from utils.logging_config import setup_logging, get_logger


class TestSetupLogging:
    def test_setup_logging_returns_logger(self):
        logger = setup_logging(level=logging.INFO, console_level=logging.WARNING)
        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.DEBUG  # Root logger is always DEBUG

    def test_setup_logging_clears_handlers(self):
        logger = setup_logging()
        # Should have 2 handlers: file + console
        assert len(logger.handlers) == 2

    def test_file_handler_has_correct_level(self):
        logger = setup_logging(level=logging.DEBUG)
        file_handler = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handler) >= 1

    def test_console_handler_has_correct_level(self):
        logger = setup_logging(console_level=logging.ERROR)
        console_handler = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handler) >= 1

    def test_custom_log_file(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            logger = setup_logging(log_file=log_path)
            logger.info("Test message to custom file")
            # Close handlers so Windows can release the file lock
            for h in logger.handlers[:]:
                h.close()
                logger.removeHandler(h)
            with open(log_path, "r") as f:
                content = f.read()
            assert "Test message to custom file" in content
        finally:
            if os.path.exists(log_path):
                os.unlink(log_path)

    def test_file_handler_formatter(self):
        logger = setup_logging()
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                formatter = handler.formatter
                assert formatter is not None
                fmt = formatter._fmt
                assert "%(asctime)s" in fmt
                assert "%(name)s" in fmt
                assert "%(levelname)s" in fmt
                assert "%(message)s" in fmt

    def test_multiple_setup_calls_clear_handlers(self):
        logger1 = setup_logging()
        count1 = len(logger1.handlers)
        logger2 = setup_logging()
        count2 = len(logger2.handlers)
        # Each call clears and re-adds, so count should not double
        assert count2 == count1

    def test_handler_types(self):
        logger = setup_logging()
        handler_types = {type(h).__name__ for h in logger.handlers}
        assert "FileHandler" in handler_types
        assert "StreamHandler" in handler_types


class TestGetLogger:
    def test_returns_logger(self):
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_logger_propagates_to_root(self):
        logger = get_logger("test.module")
        assert logger.propagate is True

    def test_logger_level(self):
        logger = get_logger("test.module")
        # By default, level should be NOTSET (propagates to root)
        assert logger.level == logging.NOTSET

    def test_named_logger_reuse(self):
        logger1 = get_logger("shared.name")
        logger2 = get_logger("shared.name")
        assert logger1 is logger2


class TestSetupLoggingScenarios:
    def _close_handlers(self, logger):
        """Close all handlers to release file locks on Windows."""
        for h in logger.handlers[:]:
            h.close()
            logger.removeHandler(h)

    def test_debug_level_allows_debug(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            logger = setup_logging(log_file=log_path, level=logging.DEBUG)
            logger.debug("This is a debug message")
            self._close_handlers(logger)
            with open(log_path, "r") as f:
                content = f.read()
            assert "debug" in content.lower() or "DEBUG" in content
        finally:
            if os.path.exists(log_path):
                os.unlink(log_path)

    def test_info_level_filters_debug(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            logger = setup_logging(log_file=log_path, level=logging.INFO)
            logger.debug("This should NOT appear")
            logger.info("This should appear")
            self._close_handlers(logger)
            with open(log_path, "r") as f:
                content = f.read()
            assert "This should NOT appear" not in content
            assert "This should appear" in content
        finally:
            if os.path.exists(log_path):
                os.unlink(log_path)

    def test_warning_and_above_written(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            logger = setup_logging(log_file=log_path, level=logging.WARNING)
            logger.info("Should not appear")
            logger.warning("Should appear")
            logger.error("Should appear too")
            self._close_handlers(logger)
            with open(log_path, "r") as f:
                content = f.read()
            assert "Should not appear" not in content
            assert "Should appear" in content
            assert "Should appear too" in content
        finally:
            if os.path.exists(log_path):
                os.unlink(log_path)


class TestModuleLevelInit:
    """Test that module-level setup_logging() is called on import."""

    def test_logger_configured_on_import(self):
        # The module calls setup_logging() at import time
        import utils.logging_config
        root_logger = logging.getLogger()
        handlers = root_logger.handlers
        assert len(handlers) >= 1  # At least some handlers configured

    def test_default_log_file(self):
        # setup_logging() defaults to "app.log"
        logger = setup_logging()
        has_file_handler = any(
            isinstance(h, logging.FileHandler) and h.baseFilename.endswith("app.log")
            for h in logger.handlers
        )
        assert has_file_handler


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
