# visualize/pipeline.py

import os
import config
from utils.llm_client import LLMClient
from components.step_1_yaml_parser import parse_yaml
from components.step_2_data_preparer import prepare_sample_data
from components.step_3_api_caller import get_api_example
from components.step_4_ui_generator import generate_ui_code
from components.step_5_executor import execute_and_debug
from dotenv import load_dotenv

load_dotenv()

def main():
    """
    Hàm chính điều phối toàn bộ pipeline tự động tạo giao diện.
    """
    # Đường dẫn đến thư mục task, bạn có thể thay đổi để test các task khác nhau
    task_dir = os.getenv("FOLDER_DIR")
    task_yaml_path = os.path.join(task_dir, 'task.yaml')

    # Đảm bảo thư mục chứa code tự động tạo ra tồn tại
    os.makedirs(config.GENERATED_CODE_DIR, exist_ok=True)
    
    # Khởi tạo client cho LLM
    llm_client = LLMClient()
    if not llm_client.client:
        print("Không thể khởi tạo pipeline do lỗi LLM Client.")
        return

    # --- Bắt đầu Pipeline ---
    # Bước 1: Phân tích file YAML
    task_info = parse_yaml(task_yaml_path)
    if not task_info: return

    # Bước 2: Chuẩn bị payload mẫu
    sample_payload = prepare_sample_data(task_info, task_dir, llm_client)
    if not sample_payload: return

    # Bước 3: Gọi API để lấy ví dụ
    api_url = task_info.get('model_information', {}).get('api_url')
    api_example_output = get_api_example(api_url, sample_payload)
    if not api_example_output: return

    # Bước 4: Tạo mã nguồn giao diện
    ui_code = generate_ui_code(task_info, sample_payload, api_example_output, llm_client)
    if not ui_code: return

    # Bước 5 & 6: Thực thi và gỡ lỗi
    execute_and_debug(llm_client)

if __name__ == '__main__':
    main()