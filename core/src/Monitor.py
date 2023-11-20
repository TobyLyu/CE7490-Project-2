import yaml

class Monitor:
    def __init__(self) -> None:
        self.num_of_disk = 8
        self.num_data_disk = 6
        self.num_check_disk = 2
        self.disk_on = []
        self.disk_status = []
        self.disk_name = []
        self.chunk_size = 1
        self.strip_size = self.num_data_disk * self.chunk_size
        
        
    def load_system_info(self):
        with open('config.yml', 'r') as file:
            self.config = yaml.safe_load(file)
            
        self.num_of_disk = self.config['num_of_disk']
        self.num_data_disk = self.config['num_data_disk']
        self.num_check_disk = self.config['num_check_disk']
        self.chunk_size = self.config['chunk_size']