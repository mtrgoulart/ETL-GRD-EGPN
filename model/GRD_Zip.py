from src.builderGRDZIP import Builder_GRD_ZIP

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class GRD_ZIP(metaclass=SingletonMeta):

    def __init__(self):
        self.Builder_instance=Builder_GRD_ZIP()

    def get_attributes(self,GRD_code):
        self.GRD_ZIP_Data=self.get_GRD_data(GRD_code)
        self.GRD_code=self.GRD_ZIP_Data['GRD_code']
        self.inner_files=self.GRD_ZIP_Data['inner_files']
        self.path=self.GRD_ZIP_Data['path']
        self.GRD_type=self.GRD_ZIP_Data['GRD_Type']
        self.GRD_Excel=self.GRD_ZIP_Data['GRD_Excel']
        self.GRD_pdf=self.GRD_ZIP_Data['GRD_pdf']
        self.ADPs=self.GRD_ZIP_Data['ADPs']
        self.ATAs=self.GRD_ZIP_Data['ATAs']
        self.Others=self.GRD_ZIP_Data['Others']

    def get_GRD_data(self,GRD_code):
        GRD_data=self.Builder_instance.GRDs_data[GRD_code]
        return GRD_data

    @classmethod
    def destroy_instance(cls):
        if cls in cls._instances:
            del cls._instances[cls]