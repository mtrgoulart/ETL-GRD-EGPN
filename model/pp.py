import os
import sys
import re

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Patterns_Paths(metaclass=SingletonMeta):
    def __init__(self):
        self.adp_reply_pattern=r"ADP-R-Reply\s*\d{4}"
        self.adp_pattern=r"ADP\s*\d{4}"
        self.grd_aa_path='//tmddom01.lcl/spe/PROJECT OFFICE/99. Doc Control Transfer/0. PLANILHAS 2023/00. GRD-AA e NT-AA.xlsx'
        self.grd_egpn_path='//tmddom01.lcl/spe/PROJECT OFFICE/99. Doc Control Transfer/0. PLANILHAS 2023/00. GRD-EGPN e ADP.xlsx'
        self.grd_egpn_pattern=r'GRD-EGPN-\d{4}-\d{4}'
        self.spe_tc_code_pattern=r'\d{8}-\d{5}-[A-Za-z]-\d{4}'
        self.spe_code_pattern=r'\bSPE\sNº\b|\btkMS\b|\bSPE\b'
        self.date_pattern=r'\d{2}\s*[./]\s*\d{2}\s*[./]\s*\d{2,4}'
        self.model_path = os.path.join(os.path.dirname(sys.executable), 'en_core_web_md-3.6.0')
        self.temp_folder='C:\\Project\\temp'
        self.egpn_code_pattern=r'\b(EMGEPRON|Emgepron|EGPN)\s*:'
        self.egpn_code_pattern_2=r'\b(EMGEPRON|Emgepron|EGPN)\s*'
        self.correcao_pattern = re.compile(r'-\s?corr.*', flags=re.IGNORECASE)
        self.cancelada_pattern = re.compile(r'-\s?canc.*', flags=re.IGNORECASE)
        self.path_grd_egpn_zip='//tmddom01.lcl/spe/PROJECT OFFICE/03. GRD-EGPN (doc)/2023_GRD-EGPN (doc)'
        self.path_grd_egpn_pdf='//tmddom01.lcl/spe/PROJECT OFFICE/03. GRD-EGPN (pdf)/2023_GRD-EGPN (pdf)'
        self.path_adp='//tmddom01.lcl/spe/PROJECT OFFICE/01. ADP (PDA)/1. ADP'
        self.path_adp_reply='//tmddom01.lcl/spe/PROJECT OFFICE/01. ADP (PDA)/2. ADP-R-REPLY'
        self.path_cryptshare_sharepoint='//tmddom01.lcl/spe/PROJECT OFFICE/99. Doc Control Transfer/0. GRD-EGPN/2. Cryptshare - Sharepoint'
        self.path_team_center='//tmddom01.lcl/spe/PROJECT OFFICE/99. Doc Control Transfer/0. GRD-EGPN/3. Colocar no TeamCenter'
        self.path_fusion='//tmddom01.lcl/spe/PROJECT OFFICE/99. Doc Control Transfer/0. GRD-EGPN/4. Colocar no Fusion'
        self.path_atas='//tmddom01.lcl/spe/PROJECT OFFICE/99. Doc Control Transfer/0. GRD-EGPN/1. Atas para processar'
        self.adp_insider_pattern=r'ADP Nº|PDA No.|ADP-R-REPLY Nº|ADP No|ADP Nº'
    
    @classmethod
    def destroy_instance(cls):
        if cls in cls._instances:
            del cls._instances[cls]