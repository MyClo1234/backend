"""
배치 작업 진입점 모듈
각 도메인의 배치 작업을 오케스트레이션
"""

from .weather import run_daily_weather_batch

__all__ = ["run_daily_weather_batch"]
