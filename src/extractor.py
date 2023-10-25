import os
import zipfile
import shutil
from .builderGRDZIP import Builder_GRD_ZIP
import re

from model.pp import Patterns_Paths

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Extractor(metaclass=SingletonMeta):
    def __init__(self):
        self.PP=Patterns_Paths()
        self.Builder_GRD_Zip=Builder_GRD_ZIP()
        self.files=[]
        

    @classmethod
    def destroy_instance(cls):
        if cls in cls._instances:
            del cls._instances[cls]

    def ETL_GRD_file_list(self,folder_path):
        self.files=[]
        for file_name in [f for f in os.listdir(folder_path) if f.endswith('.zip') and re.match(self.PP.grd_egpn_pattern, f,re.IGNORECASE)]:
            file_path = os.path.join(folder_path, file_name)
            inner_files=self.extract_inner_files(file_path)
            self.Builder_GRD_Zip.insert_values(file_name,inner_files,file_path)
            self.files.append(file_name)

    def extract_inner_files(self,file_path):
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            inner_files=[inner_file_name for inner_file_name in zip_file.namelist()]
            zip_file.extractall(self.PP.temp_folder,members=inner_files)
            return inner_files
        
    def clean_temp_folder(self):
        shutil.rmtree(Patterns_Paths.temp_folder)
        os.makedirs(Patterns_Paths.temp_folder)
