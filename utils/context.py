class TaskContext:
    def __init__(self, initial_data=None):
        self.data = initial_data or {}
        self.ui_components = []
        self.api_signature = ""
        
    def update(self, key_value_pairs: dict):
        """Cập nhật nhiều cặp key-value cùng lúc"""
        self.data.update(key_value_pairs)
        
    def set_value(self, key, value):
        """Cập nhật một giá trị đơn lẻ"""
        self.data[key] = value
        
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def to_dict(self):
        return {
            **self.data,
            "ui_components": self.ui_components,
            "api_signature": self.api_signature
        }