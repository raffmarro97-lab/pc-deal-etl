from score.programming_score import (
    calculate_programming_score,
    classify_programming_score,
    score_cpu,
    score_gpu,
    score_ram,
    score_storage,
)

def test_score_ram():
    assert score_ram(16) == 20
    assert score_ram(32) == 25
    assert score_ram(64) == 25


def test_score_storage():
    assert score_storage(512) == 12
    assert score_storage(1024) == 15
    assert score_storage(2048) == 15


def test_score_gpu_unknown():
    assert score_gpu("Unknown") == 0


def test_score_gpu_rtx():
    assert score_gpu("NVIDIA GeForce RTX 4060") == 5


def test_score_cpu_unknown():
    assert score_cpu("Unknown") == 0


def test_score_cpu_ryzen_5():
    assert score_cpu("AMD Ryzen 5") == 44


def test_score_cpu_core_ultra_7():
    assert score_cpu("Intel Core Ultra 7 155H") == 52


def test_score_cpu_intel_core_7():
    assert score_cpu("Intel Core 7 Processor 150U") == 46


def test_classification():
    assert classify_programming_score(85) == "Excellent"
    assert classify_programming_score(70) == "Good"
    assert classify_programming_score(55) == "Acceptable"
    assert classify_programming_score(54) == "Poor"


def test_complete_programming_score():
    product = {
        "cpu": "Intel Core Ultra 5 225U",
        "ram_gb": 24,
        "storage_gb": 1024,
        "gpu": "Unknown",
    }

    result = calculate_programming_score(product)

    assert result["cpu_score"] == 47
    assert result["ram_score"] == 23
    assert result["storage_score"] == 15
    assert result["gpu_score"] == 0

    assert result["programming_score"] == 85
    assert result["programming_class"] == "Excellent"