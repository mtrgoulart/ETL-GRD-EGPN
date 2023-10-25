import os
import re
import pandas as pd
import docx2txt as docx
from .transformations import find_match_start_position,list_to_dict_with_incremental_index,transform_list,convert_to_list,replace_minus_for_dash,replace_hifen_for_dash_egpncode,split_if_whitespace
from .extractor import Extractor


from model.pp import Patterns_Paths
from model.GRD_Zip import GRD_ZIP

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class builderADP(metaclass=SingletonMeta):
    def __init__(self):
        self.Extractor=Extractor()
        self.pp=Patterns_Paths()
        self.ADP=pd.DataFrame()
        self.GRD_Zip=GRD_ZIP()

    @classmethod
    def destroy_instance(cls):
        if cls in cls._instances:
            del cls._instances[cls]
            
    def DataFrame_ADP(self):
        for file in self.Extractor.files:
            self.GRD_Zip.get_attributes(file)
            metadata_ADP=self.build_ADP_metadata(self.GRD_Zip,self.GRD_Zip.ADPs)
            adp=self.build_ADP_dataframe(metadata_ADP)
            self.ADP=pd.concat([adp,self.ADP],ignore_index=True)
    
    def build_ADP_metadata(self,GRD_Zip,list_ADPs):
        metadata_list=[]
        for inner_file_name in list_ADPs:
            text = docx.process(os.path.join(self.pp.temp_folder,inner_file_name))
            title=self.produce_title(text)
            adp_number=self.produce_adp_number(inner_file_name)
            adp_type=self.produce_adp_type(inner_file_name)
            egpn_code=self.produce_egpn_code(text)
            spe_code=self.produce_spe_code(text)
            date=self.produce_date(text)
            grd_code=GRD_Zip.GRD_code[:-4]
            grd_file_name=GRD_Zip.GRD_code
            adp_file_name=inner_file_name
            status,sec_status=self.produce_status_adp(text)
            inner_adp_number=self.produce_adp_number_insider(text)
            metadata_list.append((grd_code,adp_type,adp_number,egpn_code,spe_code,date,status,sec_status,adp_file_name,grd_file_name,title,inner_adp_number))
        return metadata_list

    def build_ADP_dataframe(self,list_ADPs_Builded):
        columns=['GRD EGPN','Tipo Documento','ADP','EGPN Code','SPE Code','Date','Status','Duplicate Status?','ADP Filename','GRD Filename','Title ADP','Inner ADP']
        adp=pd.DataFrame(list_ADPs_Builded,columns=columns)
        
        adp['EGPN Code'] = adp['EGPN Code'].fillna('N/A').apply(lambda x: split_if_whitespace(x) if isinstance(x, str) else x)
        adp['SPE Code'] = adp['SPE Code'].fillna('N/A').apply(lambda x: split_if_whitespace(x) if isinstance(x, str) else x)
        adp['is_list'] = adp['EGPN Code'].apply(lambda x: isinstance(x, list))
        df_with_lists = adp[adp['is_list']].copy()
        df_without_lists = adp[~adp['is_list']].copy()

        if not df_with_lists.empty:

            df_with_lists['EGPN Dic'] = df_with_lists['EGPN Code'].apply(lambda x: list_to_dict_with_incremental_index(x))
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

            df_with_lists[['index EGPN', 'EGPN Code']] = pd.DataFrame(df_with_lists['EGPN Dic List'].tolist(), index=df_with_lists.index)
            df_with_lists[['index SPE', 'SPE Code']] = pd.DataFrame(df_with_lists['SPE Dic List'].tolist(), index=df_with_lists.index)

            mask = df_with_lists['index EGPN'] != df_with_lists['index SPE']
            df_with_lists = df_with_lists[~mask]

            columns_to_drop = ['EGPN Dic List', 'SPE Dic List','EGPN Dic', 'SPE Dic', 'EGPN Dic List length', 'SPE Dic List length', 'index EGPN', 'index SPE']

            adp = pd.concat([df_with_lists, df_without_lists])
            adp = adp.sort_values(by=['GRD EGPN', 'ADP', 'index EGPN'])
            adp = adp.reset_index(drop=True)
            adp.drop(columns=columns_to_drop, inplace=True)
        
        #Prepare EGPN, Review and SPE
        
        adp['EGPN Code'] = adp['EGPN Code'].apply(lambda value: value.strip())
        adp['Review']=adp['EGPN Code'].str.extract(r'([-/ ]?[A-Za-z0-9]+)$')
        adp['Review'] = adp['Review'].astype(str)
        adp['Review']=adp['Review'].apply(lambda value: value.replace('-','').replace('/',''))
        adp['EGPN'] = adp['EGPN Code'].apply(self.remove_pattern)
        adp['SPE Code']=adp['SPE Code'].apply(replace_minus_for_dash)
        adp['Review']=adp['Review'].astype(str).str.strip()
        adp['EGPN']=adp['EGPN'].str.strip()
        adp['SPE Code']=adp['SPE Code'].str.strip()
        adp['EGPN']=adp['EGPN'].apply(replace_hifen_for_dash_egpncode)

        adp.drop(columns=['EGPN Code','is_list'],inplace=True)

        return adp

    def produce_title(self,text):
        try:
            lines = text.split('\n')
            lines=[item for item in lines if item]
            for idx, line in enumerate(lines):
                line=line.strip()
                match_title_header=re.match(r'T[ÍI]TULO DO DOCUMENTO|DOCUMENT TITLE',line,re.IGNORECASE)
                match_status=re.match(r'Status do Documento|Document Status',line,re.IGNORECASE)
                if match_title_header:
                    title_header_position=idx
                if match_status:
                    status_position = idx
            title_position=status_position-1
            title=lines[title_position]
        except:
            title='N/A'
        return title

    def produce_adp_number(self,file_name):
        try:
            if re.match(self.pp.adp_pattern,file_name):
                adp_number=file_name[4:8].strip()
                return adp_number
            elif re.match(self.pp.adp_reply_pattern,file_name,re.IGNORECASE):
                adp_number=file_name[12:16].strip()
                return adp_number
        except:
            adp_number=0000

    def produce_adp_type(self,inner_file_name):
        try:
            if re.match(self.pp.adp_reply_pattern,inner_file_name,re.IGNORECASE):
                adp_type='ADP-R-Reply'
                return adp_type
            elif re.match(self.pp.adp_pattern,inner_file_name):
                adp_type='ADP'
                return adp_type
        except:
            adp_type='N/A'
            return adp_type
        
    def produce_egpn_code(self,text):
        start_index = find_match_start_position(self.pp.egpn_code_pattern,text)
        start_index_list=[]
        if start_index==-1:
            for match in re.finditer(self.pp.egpn_code_pattern_2,text):
                start_index_list.append(match.start())
            start_index=start_index_list[2]
        end_index=[]
        for match in re.finditer(self.pp.spe_code_pattern,text):
            index=match.start()
            end_index.append(index)
        if end_index[0]<start_index:
            end_index=end_index[1]
        else:
            end_index=end_index[0]
            match_date=re.search(self.pp.date_pattern,text)
            if match_date:
                if match_date.start()<end_index:
                    match_newline_between_date_egpn=re.search(r'\n',text[start_index:match_date.start()])
                    end_index=start_index+match_newline_between_date_egpn.start()
        
        code_section = text[start_index:end_index].strip()
        codes = code_section.split('\n')
        if not start_index_list:
            codes = [re.sub(self.pp.egpn_code_pattern,'',code).strip() for code in codes if code.strip()]
        else:
            codes = [re.sub(self.pp.egpn_code_pattern_2,'',code).strip() for code in codes if code.strip()]
        egpn_code='\n'.join(codes)
        return egpn_code.strip()

    def produce_spe_code(self,text):
        try:
            start_index_egpn = find_match_start_position(self.pp.egpn_code_pattern,text)
            end_index_egpn=[]
            for match in re.finditer(self.pp.spe_code_pattern,text):
                index=match.start()
                end_index_egpn.append(index)
            if end_index_egpn[0]<start_index_egpn:
                end_index_egpn=end_index_egpn[1]
            else:
                end_index_egpn=end_index_egpn[0]

            start_index_spe=end_index_egpn
            end_index=text.find('DAT',start_index_spe)
            
            code_section = text[start_index_spe:end_index].strip()
            codes = code_section.split('\n')
            codes = [re.sub(self.pp.spe_code_pattern,'',code).replace(':','').strip() for code in codes if code.strip()]
            spe_code='\n'.join(codes)
            if len(spe_code)>200:
                spe_code='N/A'
            return spe_code.upper().strip()
        except:
            spe_code='N/A'
            return spe_code

    def produce_date(self,text):
        try:
            match=re.search(self.pp.date_pattern,text)
            if match:
                date_section=text[match.start():match.end()]
                dates=date_section.split('\n')
                date = [date.replace('.','/').strip() for date in dates if date.strip()]
                date='\n'.join(date)
                return date
            else:
                return 'N/A'
        except:
            date='N/A'
            return date

    def produce_status_adp(self,text):
        pattern_empty=r'\(\s*[xX]?\s*\)'
        pattern_x=r'\(\s*[xX]\s*\)'
        empty_position=[]
        list_x_positions=[]
        for match in re.finditer(pattern_empty, text):
            empty_position.append(match.start())
        for match in re.finditer(pattern_x,text):
            x_match_pos=match.start()
            list_x_positions.append(match)
        position=empty_position.index(list_x_positions[0].start())

        #Check Duplicate status
        if len(list_x_positions)>1:
            if list_x_positions[1].start() in empty_position[:2]:
                sec_status='Yes'
            else:
                sec_status='No'
        else:
                sec_status='No'

        #Define the status
        if position==0:
            status='RELEASED'
        elif position==1:
            status='RELEASED WITH COMMENTS'
        elif position==2:
            status='NOT RELEASED'
        else:
            status='N/A'

        return status,sec_status



    def produce_adp_number_insider(self,text):
        match=re.search(self.pp.adp_insider_pattern,text,re.IGNORECASE)
        if match:
            match_newline=re.search(r'\n',text[match.end():])
            if match_newline:
                adp_number=text[match.end():match.end()+match_newline.start()]
                adp_number=re.sub(':','',adp_number).strip()
            else:
                adp_number=''
        else:
            adp_number=''
        return adp_number

    def remove_pattern(self,code):
        return re.sub(r'([-/ ]?[A-Za-z0-9]+)$', '', code)
