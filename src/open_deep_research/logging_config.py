"""Logging configuration for Open Deep Research."""

import sys
from loguru import logger

# Remove default logger
logger.remove()

# Add terminal output with detailed formatting
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
    backtrace=True,
    diagnose=True
)

# Also add file output for debugging
logger.add(
    "logs/open_deep_research_{time}.log",
    rotation="100 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    backtrace=True,
    diagnose=True
)

# Export configured logger
__all__ = ["logger"]