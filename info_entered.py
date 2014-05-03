class InfoEntered(object):
    
    def __init__(self, is_valid, error_message):
        self.validation = is_valid  # boolean
        self.error_msg = error_message  # string
        

    def get_validation_info(self):
        return self.validation


    def get_error_msg(self):
        return self.error_msg

    def set_error_msg(self, error_string):
        self.error_msg = error_string


    
