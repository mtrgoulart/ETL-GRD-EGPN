import os
import shutil
import re
from src.extractor import Extractor
from src.builderADP import builderADP
from src.builderGRD import builderGRD
from src.validations import Validations

from model.pp import Patterns_Paths



class Movimentations():
    def __init__(self):
        self.pp=Patterns_Paths()
        self.Extractor=Extractor()
        self.ADP_processor=builderADP()
        self.GRD_processor=builderGRD()
        self.Validation=Validations(ADP=self.ADP_processor.ADP,GRD_capa=self.GRD_processor.capa,GRD_items=self.GRD_processor.items)
        self.folder_path=None

    def set_folder_path(self,folder_path):
        self.folder_path=folder_path

    def start(self,folder_path):
        if folder_path:
            self.set_folder_path(folder_path)
            print('\n Starting file movimentation: \n')
            list_all_zips,list_adp_zips,list_adp_tkms,list_atas_zips=self.produce_file_list()
            self.move_zip_files(list_all_zips,list_atas_zips,list_adp_zips)
            self.move_inner_files(list_adp_tkms)
        else:
            raise 'No folder selected'


    def produce_file_list(self):
        df_grd_files=self.GRD_processor.capa[['Filename','Type GRD']].copy()

        df_zips_adps=df_grd_files[df_grd_files['Type GRD']=='ADP']
        df_zips_atas=df_grd_files[df_grd_files['Type GRD']=='ATA']
        
        list_all_zips=df_grd_files['Filename'].tolist()
        list_adp_zips=df_zips_adps['Filename'].tolist()
        list_atas_zips=df_zips_atas['Filename'].tolist()

        #Build tkMS Dataframe
        df_adp_grdaa=self.Validation.df_merged[['ADP Filename','ADP','SPE GRD-AA']].copy()
        df_adp_grdaa.drop_duplicates(subset=['ADP Filename','ADP'],inplace=True)
                    
        df_adp_tkms = df_adp_grdaa[df_adp_grdaa['SPE GRD-AA'].str.match(self.pp.spe_tc_code_pattern, case=False)]
        list_adp_tkms=df_adp_tkms['ADP Filename'].tolist()

        return list_all_zips,list_adp_zips,list_adp_tkms,list_atas_zips
    
    def move_inner_files(self,list_adp_tkms):
        for temp_files in os.listdir(self.pp.temp_folder):
            
            source_path_inner_files=os.path.join(self.pp.temp_folder,temp_files)

            destination_grd_egpn_pdf=os.path.join(self.pp.path_grd_egpn_pdf,temp_files)
            destination_adp=os.path.join(self.pp.path_adp,temp_files)
            destination_adp_reply=os.path.join(self.pp.path_adp_reply,temp_files)

            #GRD xls and pdf
            #Project Office/03. GRD-EGPN (pdf)
            if temp_files.lower().endswith((".xlsx",".xls",".pdf",".xlsm")) and temp_files.lower().startswith('grd'):
                if not os.path.exists(destination_grd_egpn_pdf):
                    print('\n To Project Office/03. GRD-EGPN (pdf)')
                    shutil.copy2(source_path_inner_files,destination_grd_egpn_pdf)
                    print(f'Copied {temp_files}')

            #ADP/ADP-R-REPLY doc, docx
            if temp_files.lower().endswith((".docx",".doc")) and temp_files.lower().startswith('adp'):
                #01. ADP
                if re.search(self.pp.adp_pattern,temp_files):
                    if not os.path.exists(destination_adp):
                        print(f'\n To Projec Office/01. ADP (PDA)')
                        shutil.copy2(source_path_inner_files,destination_adp)
                        print(f'Copied {temp_files}')
                #01. ADP (reply)
                if re.search(self.pp.adp_reply_pattern,temp_files):
                    if not os.path.exists(destination_adp_reply):
                        print(f'\n To Projec Office/01. ADP (PDA) (REPLY)')
                        shutil.copy2(source_path_inner_files,destination_adp_reply)
                        print(f'Copied {temp_files}')

                #3. Colocar no TeamCenter
                if temp_files in list_adp_tkms:
                    destination_team_center=os.path.join(self.pp.path_team_center,temp_files)
                    if not os.path.exists(destination_team_center):
                        print('\n To 0. GRD-EGPN/3. Colocar no TeamCenter')
                        shutil.copy2(source_path_inner_files,destination_team_center)     
                        print(f'Copied {temp_files}')

            os.remove(source_path_inner_files)
               
    def move_zip_files(self,list_all_zips,list_atas_zips,list_adp_zips):
        for file in list_all_zips:
            source_path = os.path.join(self.folder_path,file)

            destination_grd_egpn_zip=os.path.join(self.pp.path_grd_egpn_zip,file)
            destination_cryptshare_sharepoint=os.path.join(self.pp.path_cryptshare_sharepoint,file)
            destination_fusion=os.path.join(self.pp.path_fusion,file)
            destination_atas=os.path.join(self.pp.path_atas,file)

            #0.3 GRD-EGPN (doc)
            self.move(source_path,destination_grd_egpn_zip,'\n To 0.3 GRD-EGPN (doc)',file,list_all_zips)

            #2.Cryptshare - Sharepoint
            self.move(source_path,destination_cryptshare_sharepoint,'\n To 0. GRD-EGPN/2. Cryptshare - Sharepoint',file,list_all_zips)

            #4. Colocar no Fusion
            self.move(source_path,destination_fusion,'\n To 0. GRD-EGPN/4.Colocar no Fusion',file,list_atas_zips)
            self.move(source_path,destination_fusion,'\n To 0. GRD-EGPN/4.Colocar no Fusion',file,list_adp_zips)

            #1. Atas para processar
            self.move(source_path,destination_atas,'\n To 0. GRD-EGPN/1. Atas para processar',file,list_atas_zips)

            os.remove(source_path)

    def move(self,source,destination,massage,file,list):
        if not os.path.exists(destination) and file in list:
            print(massage)
            shutil.copy2(source, destination)
            print(f'Copied {file}') 

