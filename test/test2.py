import sys
from tkinter import filedialog
import os
import docx2txt as docx
import re
sys.path.append('//tmddom01.lcl/spe/PROJECT OFFICE/99. Doc Control Transfer/26. Projetos Mateus/Project/Python/GRDEGPN/src/')
from builderADP import builderADP
from extractor import Extractor


sys.path.append('//tmddom01.lcl/spe/PROJECT OFFICE/99. Doc Control Transfer/26. Projetos Mateus/Project/Python/GRDEGPN/model/')
from GRD_Zip import GRD_ZIP
from pp import Patterns_Paths

class Test():
    def __init__(self):
        self.builderADP=builderADP()
        self.extractor=Extractor()
        self.GRD_Zip=GRD_ZIP()
        self.pp=Patterns_Paths()
    def folder_path(self):
        self.Folder_path=filedialog.askdirectory()

if __name__=="__main__":
    test=Test()
    test.folder_path()
    test.extractor.ETL_GRD_file_list(test.Folder_path)
    for grd in test.extractor.files:
        test.GRD_Zip.get_attributes(grd)
        for adp in test.GRD_Zip.ADPs:
            text = docx.process(os.path.join(test.pp.temp_folder,adp))
            egpn=test.builderADP.produce_egpn_code(text)
            print(egpn)
            







