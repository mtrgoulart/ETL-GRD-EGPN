import pandas as pd
import re
import spacy
import os
import sys


def list_to_dict_with_incremental_index(my_list):
    return {index: value for index, value in enumerate(my_list)}

def convert_to_list(value):
    if not isinstance(value, list):
        return [value]
    return value

def transform_list(lst):
    return [(i, item[1]) for i, item in enumerate(lst)]

def format_date(datetime):
        try:
            date_time = pd.to_datetime(datetime)
            return date_time.strftime('%d/%m/%Y')
        except:
            return datetime
        
def replace_hifen_for_dash_egpncode(code):
    pattern=r'[0-9]{3}-[0-9]{1}-'
    match=re.match(pattern,code)
    if match:
        code=code[:match.end()-3]+'/'+code[match.end()-2:]
        return code
    else:
        return code

def split_if_whitespace(value):
 value=value.strip()
 if (value is not None and ('\n' in value or re.search(r'\s\s+', value) or re.search(r'\d[^\S\n]\w{3}',value))):
     value=re.sub(r'\s+','\n',value)
     return value.split('\n')
 return value

def find_match_start_position(pattern, text):
    match = re.search(pattern, text)
    if match:
        return match.start()
    else:
        return -1
    
def replace_minus_for_dash(code):
    try: 
        if code=='-' or code is None:
            code='N/A'
            return code
        elif re.match("/",code):
            return code
        elif re.match(r'-\w',code[-2:]):
            code=code[:-2]+"/"+code[-1]
        else:
            return code
        return code
    except:
        return code
    
def remove_extension_from_title_grd_aa(title_value_grd_aa):
    if isinstance(title_value_grd_aa,str):
        match_extension=re.search(r'\.\w{3}',title_value_grd_aa,re.IGNORECASE)
        if match_extension:
            start_position=match_extension.start()
            title_value_grd_aa=title_value_grd_aa[:start_position]
            return title_value_grd_aa
        else:
            return title_value_grd_aa
    else:
        return title_value_grd_aa

def check_match(text1, text2):
    if text1 == text2:
        return 'match'
    else:
         return 'no match'
    
def paint_percent_values_cells(value):
    if isinstance(value, (int, float)):
        if value<50:
            return 'background-color: #DB5346'
        elif value>=50 and value<70:
            return 'background-color: #FCDC58'
        elif value>=70 and value<99:
            return 'background-color: #A2CBFF'
        elif value>=99:
            return ''
    else:
        return ''
    
def highlight_no_match(val):
    if val == 'no match':
        return 'background-color: #DB5346'
    else:
        return ''
    
def paint_cells_yes_no(value):
    if value.lower()=='yes':
        return 'background-color: #DB5346' 
    else:
        return ''

def paint_cells_if_value(value):
    if value !='N/A':
        return 'background-color: #DB5346' 
    else:
        return ''

def print_path(path):
    dir_path, filename = os.path.split(path)
    last_two_folders = os.path.basename(os.path.dirname(dir_path)), os.path.basename(dir_path)
    path = os.path.join(*last_two_folders, filename)
    print(f'\n File generated on {path}\n')

def generate_excel(folder_path,dataframes, sheet_names=None):
        save_path=os.path.join(folder_path,'Validação de documentos.xlsx')

        #Check if file is already open
        counter = 0
        while os.path.exists(save_path):
            try:
                with open(save_path, 'r'):
                    pass
                counter += 1
                save_path = os.path.join(folder_path, f'Validação de documentos({counter}).xlsx')
            except Exception as e:
                print(f"Error: {e}")


        with pd.ExcelWriter(save_path) as writer:
            for i, df in enumerate(dataframes):
                sheet_name = sheet_names[i] if sheet_names and i < len(sheet_names) else f'Sheet{i+1}'
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        print_path(save_path)

def get_path_name(path):
    dir_path, filename = os.path.split(path)
    last_two_folders = os.path.basename(os.path.dirname(dir_path)), os.path.basename(dir_path)
    path = os.path.join(*last_two_folders, filename)
    return f'{path}\n'

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class TextSimilarity(metaclass=SingletonMeta):
    def __init__(self):
        self.model_path=os.path.join(os.path.dirname(sys.executable), 'en_core_web_md-3.6.0')
        self.nlp=spacy.load(self.model_path)

    def get_similarity_from_two_strings(self,string1,string2):
        string1_nlp=self.nlp(string1.lower())
        string2_nlp=self.nlp(string2.lower())
        similarity=string1_nlp.similarity(string2_nlp)*100
        return(int(similarity))