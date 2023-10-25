from .extractor import Extractor
from tkinter import filedialog
from .builderADP import builderADP
from .builderGRD import builderGRD
from .transformations import generate_excel
from .validations import Validations
from .movimentations import Movimentations
from .builderGRDZIP import Builder_GRD_ZIP
from model.GRD_Zip import GRD_ZIP
import shutil
from model.pp import Patterns_Paths
import os



class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
class Director(metaclass=SingletonMeta):
    def __init__(self):
        self.Extractor=Extractor()
        self.ADP_processor=builderADP()
        self.GRD_processor=builderGRD()
        self.pp=Patterns_Paths()
        self.builder_zip_instance=Builder_GRD_ZIP()
    
    @classmethod
    def destroy_instance(cls):
        if cls in cls._instances:
            del cls._instances[cls]
        
    def GRD_EGPN_Validation(self):
        if self.Folder_path:
            self.ETL_files()
            self.generate_Excel_validations()

    def execute_movimentation(self):
        if self.Folder_path:
            self.movimentation=Movimentations()
            self.movimentation.start(self.Folder_path)
            self.remove_temp_files()
        
    def folder_path(self):
        try:
            self.Folder_path=filedialog.askdirectory()
        except:
            self.Folder_path=None
            print('No folder selected\n')

    def set_folder_path(self,path):
        self.Folder_path=path

    def ETL_files(self):
        print(f'\n Starting Process Files...\n')
        self.Extractor.ETL_GRD_file_list(self.Folder_path)
        self.ADP_processor.DataFrame_ADP()
        self.GRD_processor.build_capa_items()

    def produce_validations(self):
        validation=Validations(GRD_capa=self.GRD_processor.capa,
                               GRD_items=self.GRD_processor.items,
                               ADP=self.ADP_processor.ADP)
        dfs_validation=validation.build_validations_controls()
        return dfs_validation
    
    def remove_temp_files(self):
        shutil.rmtree(self.pp.temp_folder)
        os.makedirs(self.pp.temp_folder)
    
    def generate_Excel_validations(self):
        dfs_validation=self.produce_validations()
        generate_excel(folder_path=self.Folder_path,dataframes=dfs_validation,sheet_names=['Val GRD-AA',
                                                                                           'Val GRD-EGPN',
                                                                                           'Val ADP Control',
                                                                                           'GRD-EGPN Control',
                                                                                           'ADP Control ',
                                                                                           'ADP-R-Reply Control'])


class DM:
    @classmethod
    def destroy_builders(cls):
        singleton_classes = [
            "GRD_ZIP",
            "Patterns_Paths",
            "Director",
            "builderADP",
            "builderGRD",
            "Extractor",
            "Builder_GRD_ZIP"
        ]
        
        for class_name in singleton_classes:
            cls_name = globals().get(class_name)
            if cls_name:
                cls_name().destroy_instance()

