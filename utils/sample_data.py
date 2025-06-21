# utils/sample_data.py
import random

# ==============================================================================
# == CÁC MẪU DỮ LIỆU CƠ BẢN (BASIC DATA SAMPLES)                            ==
# ==============================================================================

# Dữ liệu cho tác vụ 'text_classification'.
SAMPLE_TEXT = "The sun finally came out after days of rain, what a joyous day!"

# Dữ liệu cho tác vụ 'image_classification' và 'object_detection_in_image'.
SAMPLE_BASE64_IMAGE = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

# Dữ liệu URL hình ảnh mẫu
SAMPLE_IMAGE_URL = "https://i.imgur.com/8qC4i3a.jpeg"

# Dữ liệu JSON mẫu chung
SAMPLE_JSON = {
    "key1": "value1",
    "key2": 123
}

# ==============================================================================
# == CÁC MẪU DỮ LIỆU CẤU TRÚC PHỨC TẠP (COMPLEX STRUCTURE SAMPLES)         ==
# ==============================================================================

# Dữ liệu cho tác vụ 'tabular_Youtubeing'
SAMPLE_TABULAR_PAYLOAD = {
    "table": {
        "columns": ["Player", "Team", "Points"],
        "data": [
            ["John", "Team A", 25],
            ["Mike", "Team B", 30],
            ["Sara", "Team A", 22]
        ]
    },
    "queries": [
        "Who scored the most points?",
        "How many points did Sara score?"
    ]
}

# Dữ liệu cho tác vụ 'audio_classification'
SAMPLE_AUDIO_PAYLOAD = {
    "audio_data": [random.uniform(-1.0, 1.0) for _ in range(1500)],
    "sampling_rate": 48000
}

# Dữ liệu cho tác vụ 'time_series_forecasting'
SAMPLE_TIMESERIES_PAYLOAD = {
    "table": {
        "columns": ["timestamp", "open", "high", "low", "close", "volume"],
        "data": [
            ["2025-01-01 00:00:00", 0.25, 0.26, 0.24, 0.245, 100000],
            ["2025-01-01 01:00:00", 0.245, 0.25, 0.24, 0.248, 120000],
            ["2025-01-01 02:00:00", 0.248, 0.255, 0.247, 0.252, 110000],
            ["2025-01-01 03:00:00", 0.252, 0.26, 0.251, 0.258, 150000],
            ["2025-01-01 04:00:00", 0.258, 0.263, 0.257, 0.26, 130000]
        ]
    },
    "field_names": ["open", "close", "volume"],
    "prediction_length": 5,
    "num_samples": 5
}

# Dữ liệu cho tác vụ 'code_generation'
SAMPLE_CODE_GENERATION_PAYLOAD = {
    "prompt": "Write a function to calculate the factorial of a number",
    "entry_point": "factorial"
}

# Dữ liệu chung cho các tác vụ xử lý hình ảnh
SAMPLE_IMAGE_PAYLOAD = {
    "data": SAMPLE_BASE64_IMAGE
}