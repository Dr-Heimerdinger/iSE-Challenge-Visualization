# utils/payload_builder.py

from utils import sample_data

def _populate_simple_structure(schema_structure: dict) -> dict:
    """
    Hàm đệ quy này chỉ dùng cho các cấu trúc key-value đơn giản.
    """
    populated_payload = {}
    for key, field_info in schema_structure.items():
        field_type = field_info.get("type", "").lower()
        description = field_info.get("description", "").lower()
        
        if "base64" in field_type or "base64" in description:
            populated_payload[key] = sample_data.SAMPLE_BASE64_IMAGE
        # Cập nhật để nhận dạng "string" hoặc "text"
        elif "text" in field_type or "string" in field_type:
            populated_payload[key] = sample_data.SAMPLE_TEXT
        elif "url" in field_type or "url" in description:
            populated_payload[key] = sample_data.SAMPLE_IMAGE_URL
        else:
            # Fallback cho các kiểu đơn giản không xác định
            populated_payload[key] = f"Sample value for {key}"
            
    return populated_payload

def build_payload_from_schema(input_format_desc: dict) -> dict:
    """
    Hàm chính này hoạt động như một bộ định tuyến (router).
    Nó kiểm tra các cấu trúc phức tạp đã biết trước, nếu không khớp,
    nó sẽ chuyển sang xử lý cấu trúc đơn giản.
    """
    if not isinstance(input_format_desc, dict) or "structure" not in input_format_desc:
        raise ValueError("Invalid input_format_desc. Must be a dict with a 'structure' key.")
        
    structure_keys = set(input_format_desc["structure"].keys())

    # --- SỬA LỖI BẮT ĐẦU TẠI ĐÂY ---

    # 1. Ưu tiên kiểm tra các cấu trúc phức tạp đã biết.
    # Kiểm tra cho tác vụ Tabular Question Answering
    if "table" in structure_keys and "queries" in structure_keys:
        print("INFO: Detected 'Tabular Question Answering' structure. Using pre-defined complex payload.")
        return sample_data.SAMPLE_TABULAR_PAYLOAD

    # Kiểm tra cho tác vụ Audio Classification
    if "audio_data" in structure_keys and "sampling_rate" in structure_keys:
        print("INFO: Detected 'Audio Classification' structure. Using pre-defined complex payload.")
        return sample_data.SAMPLE_AUDIO_PAYLOAD

    # 2. Nếu không phải cấu trúc phức tạp, sử dụng builder đệ quy đơn giản.
    print("INFO: No complex structure detected. Using simple recursive builder.")
    return _populate_simple_structure(input_format_desc["structure"])
    
    # --- KẾT THÚC SỬA LỖI ---