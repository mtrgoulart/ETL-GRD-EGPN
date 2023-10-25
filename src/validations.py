import re
import pandas as pd
from datetime import timedelta
import numpy as np
from .transformations import remove_extension_from_title_grd_aa,check_match,paint_percent_values_cells,highlight_no_match,TextSimilarity,paint_cells_yes_no,paint_cells_if_value
from model.pp import Patterns_Paths

class Validations():
    def __init__(self,ADP,GRD_capa,GRD_items):
        self.ADP=ADP
        self.GRD_capa=GRD_capa
        self.GRD_items=GRD_items
        self.GRD_capa_items=pd.merge(self.GRD_capa,self.GRD_items, on='GRD',how='left')
        self.pp=Patterns_Paths()
        self.GRD_AA=pd.read_excel(self.pp.grd_aa_path,'GRD-AA')
        self.ADP_Control=pd.read_excel(self.pp.grd_egpn_path,'ADP 2023',skiprows=1)
        self.df_merged=self.get_merged_adp_grdaa()
        self.TextSimilarity=TextSimilarity()

    def build_validations_controls(self):
        df_validation_grd_aa=self.validation_with_grd_aa()
        df_validation_grd_egpn=self.validation_with_grd_egpn()
        df_validation_adp_control=self.validation_with_adp_control()
        df_excel_control_grd_egpn=self.excel_control_grd_egpn()
        df_excel_control_adp,df_excel_control_adp_reply=self.excel_control_adp_adpRReply()
        return [df_validation_grd_aa,
                df_validation_grd_egpn,
                df_validation_adp_control,
                df_excel_control_grd_egpn,
                df_excel_control_adp,
                df_excel_control_adp_reply
        ]

    def get_merged_adp_grdaa(self):
        grd_aa=self.GRD_AA.copy()
        check_list=pd.read_excel(self.pp.grd_aa_path,'Check-list EGPN (GRD-AA)')
        grd_aa=grd_aa[grd_aa['ADP-R?'] == 'NOT ADP-R']
        grd_aa=grd_aa[grd_aa['STATUS']=='RECEIVED']
        grd_aa['REVIEW']=grd_aa['REVIEW'].astype(str).str.strip()
        grd_aa['ORIGINALNo']=grd_aa['ORIGINALNo'].str.strip()    
        grd_aa['TITLE']=grd_aa.apply(lambda row: remove_extension_from_title_grd_aa(row['TITLE']),axis=1)

        df_merged=pd.merge(self.ADP, grd_aa, right_on=['EMGEPRON\'S CODE', 'REVIEW'], left_on=['EGPN', 'Review'], how='left')
        df_merged=pd.merge(df_merged,check_list,right_on=['GRD NUMBER'],left_on=['GRD-AA'],how='left')
        df_merged.fillna('N/A',inplace=True)

        column_map={'ADP_x':'ADP',
                    'EGPN':'EGPN ADP',
                    'EMGEPRON\'S CODE':'EGPN GRD-AA',
                    'SENT DATE':'DATE GRD-AA',
                    'Review':'Review ADP',
                    'REVIEW':'Review GRD-AA',
                    'SPE Code':'SPE ADP',
                    'ORIGINALNo':'SPE GRD-AA',
                    'TITLE':'Title GRD-AA',
                    'RESPONSIBLE COMPANY':'Responsible Company GRD-AA'
                    }    
        df_merged.rename(columns=column_map,inplace=True)

        return df_merged
    
    def excel_control_adp_adpRReply(self):
        def get_next_workday(date, num_days):
            current_date = date
            while num_days > 0:
                current_date += timedelta(days=1)
                if current_date.weekday() < 5:  # Monday to Friday are workdays (0 to 4)
                    num_days -= 1
            return current_date
    
        grdaa_adp_copy=self.df_merged[['ADP','Status','Tipo Documento','GRD-AA','EGPN ADP',
                                 'Review ADP','Responsible Company GRD-AA',
                                 'DATE GRD-AA']].copy()
        grdaa_adp_copy

        self.GRD_capa_items['EGPN'] = self.GRD_capa_items['EGPN'].str.strip()
        self.GRD_capa_items['Review'] = self.GRD_capa_items['Review'].str.strip()
        grdaa_adp_copy['EGPN ADP'] = grdaa_adp_copy['EGPN ADP'].str.strip()
        grdaa_adp_copy['Review ADP'] = grdaa_adp_copy['Review ADP'].str.strip()
    
        df_merged=pd.merge(right=self.GRD_capa_items,left=grdaa_adp_copy,right_on=['EGPN','Review'],left_on=['EGPN ADP','Review ADP'],how='left')
        df_merged['Subject']=""
        df_merged.rename(columns={'Status':'Initial ADP Status'},inplace=True)

        df_adp=df_merged[df_merged['Tipo Documento']=='ADP'].copy()
        df_adp.drop_duplicates(subset=['EGPN','Review'],inplace=True)

        df_adp['DeadLine to Argument'] = df_adp[df_adp['Initial ADP Status'] != 'RELEASED']['Data Envio'].apply(lambda x: get_next_workday(x, 5))
        df_adp['DeadLine to Argument']=df_adp['DeadLine to Argument'].fillna('N/A')
        df_adp['DATE OF SPE ARGUMENT']=''
        df_adp['GRD OF SPE COMMENT']=''
        df_adp['DATE OF EMGEPRON FINAL COMMENT']=''
        df_adp['GRD OF EMGEPRON FINAL COMMENT']=''
        df_adp['STATUS AFTER ADP-R']=''

        df_adp_columns=['ADP_x',
                        'GRD',
                        'Data Envio',
                        'Responsible Company GRD-AA',
                        'Subject',
                        'Initial ADP Status',
                        'EGPN',
                        'Title',
                        'Review',
                        'SPE Code',
                        'DeadLine to Argument',
                        'DATE OF SPE ARGUMENT',
                        'GRD OF SPE COMMENT',
                        'DATE OF EMGEPRON FINAL COMMENT',
                        'GRD OF EMGEPRON FINAL COMMENT',
                        'STATUS AFTER ADP-R',
                        'DATE GRD-AA',
                        'GRD-AA'
                        ]
        df_adp=df_adp[df_adp_columns]
        
        
        df_adp_reply=df_merged[df_merged['Tipo Documento']=='ADP-R-Reply'].copy()

        df_adp_reply_columns=['ADP_x','Data Envio','GRD','Initial ADP Status']
        df_adp_reply.drop_duplicates(subset=['ADP_x','GRD'],inplace=True)
        df_adp_reply=df_adp_reply[df_adp_reply_columns]

        return df_adp,df_adp_reply
    
    def excel_control_grd_egpn(self):
        merged_df=self.GRD_capa_items.copy()
        merged_df['Reference 2']=''
        columns=['GRD','Modo de Transmissão','Referencia','Reference 2',
                'Data Envio','Item','EGPN','ESWBS','Review','Title',
                'SPE Code','Purpose','Data Doc','Data aprov']
        merged_df=merged_df[columns]
        return merged_df

    def validation_with_grd_aa(self):
        df_merged_copy=self.df_merged.copy()
        df_merged_copy['Match EGPN']=df_merged_copy.apply(lambda row: check_match(row['EGPN ADP'],row['EGPN GRD-AA']),axis=1)
        df_merged_copy['Match Review']=df_merged_copy.apply(lambda row: check_match(row['Review ADP'],row['Review GRD-AA']),axis=1)
        df_merged_copy['Match SPE']=df_merged_copy.apply(lambda row: check_match(row['SPE ADP'],row['SPE GRD-AA']),axis=1)
        try:
            df_merged_copy['Similarity Title']=df_merged_copy.apply(lambda row: self.TextSimilarity.get_similarity_from_two_strings(row['Title GRD-AA'],row['Title ADP']),axis=1)
        except:
            df_merged_copy['Similarity Title']=''


        columns=['GRD EGPN',
                'Tipo Documento',
                'ADP',
                'GRD-AA',
                'EGPN ADP',
                'EGPN GRD-AA',
                'Match EGPN',
                'Review ADP',
                'Review GRD-AA',
                'Match Review',
                'SPE ADP',
                'SPE GRD-AA',
                'Match SPE',
                'Title ADP',
                'Title GRD-AA',
                'Similarity Title'
                ]
        df_merged_copy=df_merged_copy.loc[:,columns]
        match_columns=['Match EGPN','Match SPE','Match Review']
        idx_max = df_merged_copy.groupby(['GRD-AA','EGPN ADP','Review ADP'])['Similarity Title'].idxmax()
        df_merged_copy=df_merged_copy.loc[idx_max]
        df_merged_copy = df_merged_copy.style.applymap(paint_percent_values_cells, subset=['Similarity Title'])\
            .applymap(highlight_no_match, subset=match_columns)    
        return df_merged_copy
        
    def validation_with_grd_egpn(self):
        #Transform data
        copy_items=self.GRD_items.copy()
        copy_items['Review']=copy_items['Review'].str.strip()
        columns_map_items={'EGPN':'EGPN GRD-EGPN',
                        'Review':'Review GRD-EGPN',
                        'SPE Code':'SPE GRD-EGPN'}
        copy_items.rename(columns=columns_map_items,inplace=True)
        def format_date(datetime):
            try:
                date_time = pd.to_datetime(datetime)
                return date_time.strftime('%d/%m/%Y')
            except:
                return datetime
        copy_items['Data Doc']=copy_items['Data Doc'].apply(format_date)

        def remove_adp_pattern(text):
            if re.search(self.pp.adp_pattern,text,re.IGNORECASE):
                text=re.sub(self.pp.adp_pattern,'',text)
                text=text.lstrip('-').strip()
                return text
            if re.search(self.pp.adp_reply_pattern,text,re.IGNORECASE):
                text=re.sub(self.pp.adp_reply_pattern,'',text)
                text=text.lstrip('-').strip()
                return text

        #Merge tables
        df_items_adp=pd.merge(self.ADP, copy_items, right_on=['EGPN GRD-EGPN', 'Review GRD-EGPN','Filename'], left_on=['EGPN', 'Review','GRD Filename'], how='left')
        try:
            df_items_adp['Title ADP Mod']=df_items_adp.apply(lambda row: remove_adp_pattern(row['Title']) if isinstance(row['Title'], str) else row['Title'],axis=1)
        except:
            df_items_adp['Title ADP Mod']=''
        #Check columns
        df_items_adp['Match EGPN']=df_items_adp.apply(lambda row: check_match(row['EGPN'],row['EGPN GRD-EGPN']),axis=1)
        df_items_adp['Match Review']=df_items_adp.apply(lambda row: check_match(row['Review'],row['Review GRD-EGPN']),axis=1)
        df_items_adp['Match SPE']=df_items_adp.apply(lambda row: check_match(row['SPE Code'],row['SPE GRD-EGPN']),axis=1)
        df_items_adp['Match Date']=df_items_adp.apply(lambda row: check_match(row['Data Doc'],row['Date']),axis=1)
        df_items_adp['Match ADP Inner']=df_items_adp.apply(lambda row: check_match(row['Inner ADP'],row['ADP_x']),axis=1)
        df_items_adp['Similarity Title'] = df_items_adp.apply(lambda row: self.TextSimilarity.get_similarity_from_two_strings(row['Title'], row['Title ADP Mod']) if isinstance(row['Title'], str) and isinstance(row['Title ADP Mod'], str) else '', axis=1)

        columns_map={'EGPN':'EGPN ADP',
                    'Review':'Review ADP',
                    'SPE Code':'SPE ADP',
                    'Date':'Date ADP'}
        df_items_adp.rename(columns=columns_map,inplace=True)

        match_columns=['Match EGPN','Match SPE','Match Review','Match Date','Match ADP Inner']

        columns=['GRD EGPN',
                'Tipo Documento',
                'ADP_x',
                'Inner ADP',
                'Match ADP Inner',
                'EGPN ADP',
                'EGPN GRD-EGPN',
                'Match EGPN',
                'Review ADP',
                'Review GRD-EGPN',
                'Match Review',
                'SPE ADP',
                'SPE GRD-EGPN',
                'Match SPE',
                'Date ADP',
                'Data Doc',
                'Match Date',
                'Title ADP',
                'Title',
                'Similarity Title',
                'Duplicate Status?'
                ]
        df_items_adp=df_items_adp.loc[:,columns]
        df_items_adp = df_items_adp.style.applymap(paint_percent_values_cells, subset=['Similarity Title'])\
            .applymap(highlight_no_match, subset=match_columns)\
                .applymap(paint_cells_yes_no, subset=['Duplicate Status?'])

        return df_items_adp
    
    def validation_with_adp_control(self):
        self.ADP = self.ADP.astype(str).apply(lambda x: x.str.strip())
        self.ADP_Control = self.ADP_Control.astype(str).apply(lambda x: x.str.strip())
        df_adp=self.ADP[self.ADP['Tipo Documento']=='ADP'].copy()
        
        df_validation=pd.merge(df_adp,self.ADP_Control,right_on=['EMGEPRON\'s-CODE','REVIEW EGPN'],left_on=['EGPN','Review'],how='left')
        df_validation.fillna('N/A',inplace=True)
        df_validation.drop_duplicates(subset=['ADP_x','EGPN','Review'],inplace=True)
        df_validation['ADP_x'] = df_validation['ADP_x'].astype(str).str.strip()
        self.ADP_Control['ADP'] = self.ADP_Control['ADP'].astype(str).str.strip()
        df_validation['ADP number exist?'] = np.where(df_validation['ADP_x'].isin(self.ADP_Control['ADP']), 'yes', 'no')


        column_map={'ADP_x':'ADP',
                    'EGPN':'EGPN ADP',
                    'Review':'Review ADP',
                    'EMGEPRON\'s-CODE':'EGPN EXCEL CONTROL',
                    'REVIEW EGPN': 'REVIEW EXCEL CONTROL'
                    }    
        columns=['ADP','EGPN ADP','Review ADP','EGPN EXCEL CONTROL','REVIEW EXCEL CONTROL','ADP number exist?']

        match_columns=['EGPN EXCEL CONTROL','REVIEW EXCEL CONTROL']
        df_validation.rename(columns=column_map,inplace=True)
        df_validation=df_validation[columns]

        df_validation = df_validation.style.applymap(paint_cells_yes_no, subset=['ADP number exist?'])\
            .applymap(paint_cells_if_value, subset=match_columns)
        return df_validation

