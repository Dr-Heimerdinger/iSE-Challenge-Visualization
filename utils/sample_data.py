# utils/sample_data.py
import random

# ==============================================================================
# == CÁC MẪU DỮ LIỆU CƠ BẢN (BASIC DATA SAMPLES)                            ==
# ==============================================================================

# Dữ liệu cho tác vụ 'text_classification'.
# Phù hợp với input_format yêu cầu một 'texts' là string.
# task.yaml: text_classification/task.yaml
SAMPLE_TEXT = "The sun finally came out after days of rain, what a joyous day!"

# Dữ liệu cho tác vụ 'image_classification' và 'object_detection_in_image'.
# Đây là một ảnh PNG 1x1 pixel trong suốt, được mã hóa base64.
# Phù hợp với input_format yêu cầu 'data' là một chuỗi base64.
# task.yaml: image_classification/task.yaml, object_detection_in_image/task.yaml
SAMPLE_BASE64_IMAGE = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

# Dữ liệu URL hình ảnh mẫu, hữu ích cho các tác vụ có thể yêu cầu URL.
SAMPLE_IMAGE_URL = "https://i.imgur.com/8qC4i3a.jpeg"

# Dữ liệu JSON mẫu chung cho các trường hợp không xác định.
SAMPLE_JSON = {
    "key1": "value1",
    "key2": 123
}

# ==============================================================================
# == CÁC MẪU DỮ LIỆU CẤU TRÚC PHỨC TẠP (COMPLEX STRUCTURE SAMPLES)         ==
# ==============================================================================

# Dữ liệu cho tác vụ 'tabular_Youtubeing'.
# Cấu trúc này khớp chính xác với input_format yêu cầu một object chứa 'table' và 'queries'.
# - table: một object chứa 'columns' (List[str]) và 'data' (List[List[Any]]).
# - queries: một List[str].
# task.yaml: tabular_Youtubeing/task.yaml
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

# Dữ liệu cho tác vụ 'audio_classification'.

SAMPLE_AUDIO_PAYLOAD = {
    "audio_data": [random.uniform(-1.0, 1.0) for _ in range(150000)],
    "sampling_rate": 48000
}