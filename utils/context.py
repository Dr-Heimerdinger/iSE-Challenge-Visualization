class TaskContext:
    def __init__(self, initial_data=None):
        if isinstance(initial_data, dict):
            # Tái tạo đối tượng từ dictionary
            self.data = initial_data.get('data', {})
            self.ui_components = initial_data.get('ui_components', [])
            self.api_signature = initial_data.get('api_signature', "")
        else:
            self.data = initial_data or {}
            self.ui_components = []
            self.api_signature = ""
        
    def set_value(self, key, value):
        """Cập nhật một giá trị đơn lẻ"""
        self.data[key] = value
        
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def to_dict(self):
        return {
            'data': self.data,
            'ui_components': self.ui_components,
            'api_signature': self.api_signature
        }