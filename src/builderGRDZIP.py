class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Builder_GRD_ZIP(metaclass=SingletonMeta):
    def __init__(self):
        self.GRDs_data={}
    
    def insert_values(self,GRD_code,inner_files,path):
        self.GRDs_data[GRD_code]={
        'GRD_code':GRD_code,
        'inner_files':inner_files,
        'path':path,
        'GRD_Excel':self.get_GRD_Excel(inner_files),
        'GRD_pdf':self.get_GRD_pdf(inner_files),
        'ADPs':self.get_ADPs(inner_files),
        'ATAs':self.get_ATAs(inner_files),
        'Others':self.get_others(inner_files,self.get_GRD_Excel(inner_files),self.get_GRD_pdf(inner_files),self.get_ADPs(inner_files),self.get_ATAs(inner_files)),
        'GRD_Type':self.get_GRD_type(self.get_ADPs(inner_files),self.get_ATAs(inner_files))
        }


    @classmethod
    def destroy_instance(cls):
        if cls in cls._instances:
            del cls._instances[cls]

    def get_GRD_Excel(self,inner_files):
        GRD_Excel=next((file for file in inner_files if file.lower().startswith("grd") and file.lower().endswith((".xlsx",".xls","xlsm"))), None)
        return GRD_Excel
    
    def get_GRD_pdf(self,inner_files):
        GRD_pdf=next((file for file in inner_files if file.lower().startswith("grd") and file.lower().endswith(".pdf")), None)
        return GRD_pdf
    
    def get_ADPs(self,inner_files):
        ADPs=[file for file in inner_files if file.lower().endswith((".docx",".doc")) and file.lower().startswith('adp')]
        if not ADPs:
            return []
        return ADPs

    def get_ATAs(self,inner_files):
        ATAs=[file for file in inner_files if file.lower().startswith('ata')]
        if not ATAs:
            return []
        return ATAs

    def get_others(self,inner_files,GRD_Excel,GRD_pdf,ADPs,ATAs):
        main_files=[GRD_Excel,GRD_pdf]  
        main_files.extend(ADPs)
        main_files.extend(ATAs)
        set_main_files=set(main_files)
        set_inner_files=set(inner_files)
        other_files=list(set_inner_files-set_main_files)
        return other_files

    def get_GRD_type(self,ADPs,ATAs):
        if ADPs!=[] and ATAs==[]:
            return 'ADP'
        elif ADPs==[] and ATAs!=[]:
            return 'ATA'
        else:
            return 'Others'

    def clean_values(self):
         self.GRDs_data={}