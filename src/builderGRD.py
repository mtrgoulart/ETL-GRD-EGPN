import os
import re
import pandas as pd
from .transformations import split_if_whitespace,list_to_dict_with_incremental_index,convert_to_list,transform_list,replace_hifen_for_dash_egpncode,replace_minus_for_dash
from .extractor import Extractor
from model.pp import Patterns_Paths
from model.GRD_Zip import GRD_ZIP


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class builderGRD(metaclass=SingletonMeta):
    def __init__(self):
        self.Extractor=Extractor()
        self.pp=Patterns_Paths()
        self.GRD_Zip=GRD_ZIP()
        self.capa=pd.DataFrame()
        self.items=pd.DataFrame()

    @classmethod
    def destroy_instance(cls):
        if cls in cls._instances:
            del cls._instances[cls]

    def build_capa_items(self):
        items=pd.DataFrame()
        capa=pd.DataFrame()
        for file in self.Extractor.files:
            self.GRD_Zip.get_attributes(file)
            if self.GRD_Zip.GRD_Excel:
                excel_file_path = os.path.join(self.pp.temp_folder, self.GRD_Zip.GRD_Excel)
                df = pd.read_excel(excel_file_path)
                
                lista_capa=self.produce_capa_columns(df,file)
                lista_items=self.produce_items_columns(df,file)
            else:
                lista_capa,lista_items=self.excel_exception()

            items=pd.concat([items,lista_items],ignore_index=True)
            capa=pd.concat([capa,lista_capa],ignore_index=True)
            

        items=self.break_values_items(items)

        self.capa,self.items=self.final_fixes_capa_items(capa,items)

    def produce_capa_columns(self,df,file):
        lista_capa = df.iloc[3, [1, 7, 13, 20, 23, 28]].to_frame().transpose()
        lista_capa.columns = ["GRD", "Para", "Modo de Transmissão", "Referencia1","Referencia2", "Data Envio"]
        lista_capa['Filename']=file
        lista_capa['Status File'] = lista_capa['Filename'].apply(lambda x: 'Corrigido' if self.pp.correcao_pattern.search(x) else ('Cancelada' if self.pp.cancelada_pattern.search(x) else 'Standard'))
        lista_capa['Type GRD']=self.GRD_Zip.GRD_type
        lista_capa=self.procude_capa_referencia(lista_capa)
        return lista_capa
    
    def procude_capa_referencia(self,lista_capa):
        if lista_capa['Referencia1'].str.startswith('GRD').any():
            if lista_capa['Referencia2'].str.startswith('AA').any():
                lista_capa['Referencia2']='-'+lista_capa['Referencia2']

        lista_capa['Referencia'] = lista_capa['Referencia1'] + lista_capa['Referencia2']
        lista_capa.drop(columns=['Referencia1', 'Referencia2'], inplace=True)
        return lista_capa
        
    def produce_items_columns(self,df,file):
        lista_items = df.iloc[11:, [1,3,6,9,11,21,24,27,30,32,34]]
        lista_items.columns = ["Item", "EGPN", "ESWBS", "Review", "Title", "SPE Code", "Origin", "Purpose", "Sig", "Data Doc", "Data aprov"]
        lista_items = lista_items[lista_items["Title"].notna()]
        lista_items['GRD'] = df.iat[3, 1]
        lista_items = lista_items.reindex(columns=["GRD"] + lista_items.columns[:-1].tolist())
        lista_items.fillna('N/A', inplace=True)
        lista_items.replace({'-': 'N/A'}, inplace=True)
        lista_items['Filename']=file
        lista_items['ADP'] = lista_items['Title'].apply(lambda title: title[12:16] if re.match(self.pp.adp_reply_pattern, title,re.IGNORECASE) else title[4:8] if re.match(self.pp.adp_pattern, title,re.IGNORECASE) else 'N/A')
        return lista_items

    def break_values_items(self,items):
        items['EGPN'] = items['EGPN'].fillna('N/A').apply(lambda x: split_if_whitespace(x) if isinstance(x, str) else x)
        items['SPE Code'] = items['SPE Code'].fillna('N/A').apply(lambda x: split_if_whitespace(x) if isinstance(x, str) else x)

        items['is_list'] = items['EGPN'].apply(lambda x: isinstance(x, list))
        df_with_lists = items[items['is_list']].copy()
        df_without_lists = items[~items['is_list']].copy()

        if not df_with_lists.empty:

            df_with_lists['EGPN Dic'] = df_with_lists['EGPN'].apply(lambda x: list_to_dict_with_incremental_index(x))
            df_with_lists['SPE Dic'] = df_with_lists['SPE Code'].apply(convert_to_list)
            df_with_lists['SPE Dic'] = df_with_lists['SPE Dic'].apply(lambda x: list_to_dict_with_incremental_index(x))

            df_with_lists['EGPN Dic List'] = df_with_lists['EGPN Dic'].apply(lambda x: list(x.items()))
            df_with_lists['SPE Dic List'] = df_with_lists['SPE Dic'].apply(lambda x: list(x.items()))

            df_with_lists['EGPN Dic List length'] = df_with_lists['EGPN Dic List'].apply(lambda x: len(x))
            df_with_lists['SPE Dic List length'] = df_with_lists['SPE Dic List'].apply(lambda x: len(x))

            df_with_lists['SPE Dic List'] = df_with_lists.apply(lambda row: row['SPE Dic List'] * row['EGPN Dic List length'] if row['EGPN Dic List length'] != row['SPE Dic List length'] else row['SPE Dic List'], axis=1)
            df_with_lists['SPE Dic List'] = df_with_lists['SPE Dic List'].apply(lambda x: transform_list(x))

            df_with_lists = df_with_lists.explode('EGPN Dic List')
            df_with_lists = df_with_lists.explode('SPE Dic List')
            
            df_with_lists[['index EGPN', 'EGPN']] = pd.DataFrame(df_with_lists['EGPN Dic List'].tolist(), index=df_with_lists.index)
            df_with_lists[['index SPE', 'SPE Code']] = pd.DataFrame(df_with_lists['SPE Dic List'].tolist(), index=df_with_lists.index)
            
            mask = df_with_lists['index EGPN'] != df_with_lists['index SPE']
            df_with_lists = df_with_lists[~mask]

            columns_to_drop = ['EGPN Dic List', 'SPE Dic List', 'is_list', 'EGPN Dic', 'SPE Dic', 'EGPN Dic List length', 'SPE Dic List length', 'index EGPN', 'index SPE']

            items = pd.concat([df_with_lists, df_without_lists])
            items = items.sort_values(by=['GRD', 'ADP', 'index EGPN'])
            items = items.reset_index(drop=True)
            items.drop(columns=columns_to_drop, inplace=True)

        items['EGPN']=items['EGPN'].str.strip()
        items['EGPN']=items['EGPN'].apply(replace_hifen_for_dash_egpncode)
        items['Review']=items['Review'].apply(str).astype(str)
        items['SPE Code']=items['SPE Code'].apply(replace_minus_for_dash)
        items['SPE Code']=items['SPE Code'].str.strip()   
        return items
    
    def final_fixes_capa_items(self,capa,items):
        capa=capa.sort_values(by='Status File',ascending=False).reset_index(drop=True)
        items=items.sort_values(by=['GRD','Item']).reset_index(drop=True)

        #Remove as linhas duplicadas
        capa=capa.drop_duplicates(subset='GRD',keep="last")
        items=items.drop_duplicates(subset=['GRD','Item','EGPN'],keep="last")

        capa=capa.sort_values(by='GRD',ascending=False).reset_index(drop=True)



        return capa,items
    
    def excel_exception(self):
        lista_capa = pd.DataFrame({
        'GRD': [self.GRD_Zip.GRD_code[:-4]],
        'Para': ['N/A'],
        'Modo de Transmissão': ['N/A'],
        'Referencia': ['N/A'],
        'Data Envio': ['N/A'],
        'Filename':[self.GRD_Zip.GRD_code],
        'Status File':['N/A'],
        'Type GRD': [self.GRD_Zip.GRD_type]
        })

        lista_items = pd.DataFrame({
            'Item': ['N/A'],
            'EGPN': ['N/A'],
            'ESWBS': ['N/A'],
            'Review': ['N/A'],
            'SPE Code': ['N/A'],
            'Origin': ['N/A'],
            'Purpose': ['N/A'],
            'Sig': ['N/A'],
            'Data Doc': ['N/A'],
            'Data aprov': ['N/A'],
            'GRD':[self.GRD_Zip.GRD_code[:-4]],
            'Filename': [self.GRD_Zip.GRD_code],
            'ADP': ['N/A']
        })

        return lista_capa,lista_items

