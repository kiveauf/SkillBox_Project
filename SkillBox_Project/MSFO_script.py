"""
script to collect and analyze data from msfo sheets and real stock price
use python 3.9
"""

import PyPDF2
import requests
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import os
from tinkoff.invest import Client
import mysql.connector as sql
from dotenv import load_dotenv
from DocsTest import docs 
import camelot
import pandas as pd
import re
#import matplotlib
                                             
load_dotenv() #using this to get enviroment custom-made constant
logger = logging.getLogger("PyPDF2")
logger.setLevel(logging.CRITICAL)

class Ticker():
    def __init__(self):
        self.url = str()
        self.name = str()
        self.pribyl = 0
        self.viruchka = 0
        self.price = float()
        self.amount = 0
        self.capitalization = float()
        self.measuring_unit = int()
        self.pe = float()
        self.ps = float()
    def __iter__(self):
        for i in self.__dict__.keys():
            yield i
    
def get_file(name): # take url of the file
    file = requests.get(ticker.url)
    ticker.name = name.lower()
    filename = f"{ticker.name}_MSFO.pdf"
    with open(file = filename, mode = 'wb') as f:
        f.write(file.content)
    print(ticker.name)
    return filename

def read_content(filename): #takes file and returns dict with all lines on info pages
    #print("Reading content")
    content_pages = list()
    content_pages = camel(filename, pages= '3-20', table_areas=['50,800,550,40']) #now dict with page info
    """ In case we need to read all data"""
    #pdf_file = PyPDF2.PdfFileReader(filename, strict=False)
    #page_dohod = pdf_file.pages
    #for page in page_dohod:
    #    info = page.extract_text() #just strings
    #for page in content_pages:
    #    for line in page:
    #        print(line)
    return content_pages

def camel(filename, pages, table_areas, st = ""): #takes file and number of pages and returns 
    pages_list_raw = list()
    pages_dicts = dict()
    pdf_file = camelot.read_pdf(filename, flavor = "stream", pages = pages, table_areas = table_areas, strip_text = st, edge_tol=200)
    for page in pdf_file:
        #camelot.plot(i, kind = 'contour').show() # to display areas
        #matplotlib.pyplot.show(block=True)       # to display areas
        result = page.df
        pd.set_option('display.max_rows', 500)
        pd.set_option('display.max_columns', 2000)
        pd.set_option('display.width', 500)
        result_dict = result.to_dict(orient = "index")
        if read_data(result_dict.items()):
            pages_list_raw.append(result_dict.items()) #this is list of dict_items
    #for i in pages_list_raw:
    #    for line in i:
    #        print(line)
    pages_dicts = take_info(pages_list_raw)
    return pages_dicts

def read_data(dict_text): #takes whole page id dict_items format and return True/False if page contains needed tables and read amount of stocks and measure units of pages
    """to do if amount of shares not available on recources"""
    #if ticker.amount == 0:
    #    find_amount(dict_text, counter, filename)
    if check(dict_text): #checks if the page is in the list
        return True
    return False

#TODO algo to now what actual number to get
def take_info(pages_list_raw): #takes list with dicts and returns dict (info: latest number)
    pages_list = list()
    for page in pages_list_raw: 
        page_dict = dict()
        years_dict = dict()
        raw_line = list()
        last_line=list()
        note_column = -1
        """to make dicts more readable, to fix sentence"""
        for number, line_info in page:  #line looks like (number, {number1:column1, number2:column2 ...})
            line_info_list = list(line_info.values())
            number_of_columns = len(line_info_list)
            #print(number, line_info)
            #print(line_info_list[0])
            if len([i for i in line_info.values() if i != ""]) == 1 and line_info_list[0] == '':  #if starts with ''
                raw_line.append("".join([i for i in line_info.values() if i != ""]))
                continue
            if len([i for i in line_info.values() if i != ""]) > 1 and line_info_list[0] == '':   #if starts with ''
                if len(raw_line):
                    for line in raw_line:
                        page_dict.setdefault(line, [""] * (number_of_columns-1))
                page_dict.setdefault(f"?{number}", line_info_list[1:])
                raw_line.clear()
                continue
            if len([i for i in line_info.values() if i != ""]) == 1 and line_info_list[0][0].islower() != True:  #if starts with upper and rest empty
                raw_line.append(line_info_list[0])
                continue
            if len([i for i in line_info.values() if i != ""]) == 1 and line_info_list[0][0].islower():  #if starts with lower or ( and rest empty
                line = raw_line.pop(-1)
                raw_line.append(line +" " + line_info_list[0])
                continue
            if len([i for i in line_info.values() if i != ""]) > 1 and line_info_list[0][0].islower(): #if starts with lower or ( 
                for line in raw_line[:len(raw_line)-1]:
                    page_dict.setdefault(line, [""] * (number_of_columns-1))
                if len(raw_line):
                    page_dict.setdefault(raw_line[-1]+" "+line_info_list[0], line_info_list[1:])
                    last_line.append(raw_line[-1])      # to know the start of sentence when its x: -y; -z. to combine and make xy, xz.
                else:
                    page_dict.setdefault(last_line[0]+" "+line_info_list[0], line_info_list[1:])
                raw_line.clear()
                continue
            if len([i for i in line_info.values() if i != ""]) > 1 and line_info_list[0][0].isupper(): #if starts with upper 
                if len(raw_line):
                    for line in raw_line:
                        page_dict.setdefault(line, [""] * (number_of_columns-1))
                page_dict.setdefault(line_info_list[0], line_info_list[1:])
                raw_line.clear()
                last_line.clear()
                continue
        """to know where find the notes"""
        for value in page_dict.values():
            for i, line in enumerate(value):
                if know_notes(line):
                    note_column = i
                    #print(f"{note_column} for column {line}")
                    break
        """to know where find info by year"""
        for value in page_dict.values():
            for i, line in enumerate(value):
                if len(years_dict.items()) > 3:
                    break
                result = know_years(line)
                if result != None:
                    years_dict.setdefault(result.group(), i)
                    #print(f"{i} for column {result.group()}")
            if years_dict.items():
                last_year = max([int(i) for i in years_dict.keys()]) # last year in MSFO
        if note_column != -1:
            page_dict.setdefault("Note", note_column)
        else:
            page_dict.setdefault("Note", None)
        if len(years_dict.items()) != 0:
            page_dict.setdefault('year', years_dict[str(last_year)])
        else:
            page_dict.setdefault('year', None)
        pages_list.append(page_dict)
        for k, v in page_dict.items():
            print(k ,v)
    #return pages_list

def check(page): #takes dict_items and check if page is needed
    """may be work with re???"""
    report = {"консолидированный отчет о финансовом положении": 1, "бухгалтерский баланс": 1, "консолидированный отчет о финансовом положении": 1,
              "консолидированный отчет о совокупном доходе": 1, "консолидированные отчеты о совокупном доходе": 1, "отчет о финансовых результатах": 1, "консолидированный отчет о прибылях и убытках и прочем совокупном доходе": 1,
              "консолидированный отчет о движении денежных средств": 1, "отчеты об изменениях капитала": 1, "консолидированные отчеты об изменениях капитала": 1,
              "консолидированный отчет об изменениях в капитале": 1, "отчет о движении денежных средств": 1, "консолидированные отчеты о движении денежных средств": 1,
              "консолидированный отчет о прибыли или убытке": 1,"консолидированные отчеты о прибылях или убытках": 1, "консолидированные отчеты о финансовом положении": 1,
              "консолидированный отчет о финансовом положении": 1, "консолидированный отчет о прибылях и убытках": 1, "консолидированный отчет о совокупном доходе": 1, 
              "консолидированный отчет о движении денежных средств": 1, "консолидированные отчеты о прибылях и убытках": 1
              }
    #for line in page:
    #    print(line)
    for _,line_info in page:
        if len(line_info.values()) <= 2: # to throw away pages without tables 
            return False
        for column in line_info.values():
            if column != "":
                if ticker.measuring_unit == 0:
                    know_measure(column)
                if report.get(column.lower()):
                    return True
    return False

def collect_data(pages): #takes dict and finds needed params
    #print("Find necessary data")
    viruchka_list = ["Выручка"]
    pribyl_list = ["Прибыль за год", "Чистая прибыль отчетного периода", "Прибыль за отчетный год"]
    for name in viruchka_list:
        if pages.get(name) != None:
            viruchka_line = pages.get(name)
            viruchka = "".join(viruchka_line.split())
            #print(measuring_unit)
            ticker.viruchka = int(viruchka) * ticker.measuring_unit
            print(f"Выручка - {ticker.viruchka}")
    for name in pribyl_list:
        if pages.get(name) != None:
            pribyl_line = pages.get(name)
            pribyl = "".join(pribyl_line.split())
            #print(measuring_unit)
            ticker.pribyl = int(pribyl) * ticker.measuring_unit
            print(f"Прибыль - {ticker.pribyl}")

def know_notes(line): #checks if there notes
    notes_list = ["Примечание", "Поясн", "Прим", "Прим."]
    for word in notes_list:
        if line.find(word) >= 0:
            return True
    return False

def know_years(line): #checks if there years
    years_re = r"20\d\d"
    return re.search(years_re,line)

def know_measure(text):
    global measure_unit
    for word in text:
        if word in ["тыс.", "тыс", "тысячах", "thousands"]:
            ticker.measure_unit = 1000 #measuring unit
        if word in ["млн.", "млн", "миллионах", "millions", "Млн"]:
            ticker.measure_unit = 1000000 #measuring unit
        
def print_pages(pages):
    for page in pages:
        for line in page:
            print(line)
            print("____________________________")

def print_data():
    for i in ticker:
        print(i)

def get_price(method):
    if method == "p":
        parser()
    if method == "t":
        tinkoff_api()

def parser(): #using selenium to get all info because of javascript
    #print("Getting price and amount of shares")
    site_url = f"https://bcs-express.ru/kotirovki-i-grafiki/{ticker.name}"
    service = Service(executable_path='C:\Program Files\ChromeDriver\chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    page = webdriver.Chrome(service=service, options= options)
    page.implicitly_wait(2) # just to wait until page will load 
    page.get(site_url)
    price_sel = page.find_element(By.CLASS_NAME, 'Here.EWHp.Dlhk').text
    ticker.price = float(price_sel.replace(" ", "").replace(",", "."))
    page.quit()
    #amount_sel = page.find_elements(By.CLASS_NAME, 'Yai9')
    #ticker.amount = float(amount_sel[5].text.replace(" ", "").replace(",", "."))

def find_amount(text, counter, filename): #takes text and find amount of shares 
    amount_key = str()
    amount_value = int()
    measure_unit_thousands_list = ["в тысячах", "тысяч"]
    measure_unit_mil_list = ["в млн", "млн"]
    shares_amount_list = ["Средневзвешенное количество выпущенных обыкновенных акций", "Средневзвешенное количество обыкновенных акций",
                          "Средневзвешенное количество акций"]
    for line in text.splitlines():
        line = line.strip()
        #print(line)
        if len(line) != 0:
            for name in shares_amount_list:
                if line.count(name) >= 1:
                    #print(line)
                    amount_dict = camel(filename, str(counter), ['90,800,550,40'], "\n") #dict with info on the page
                    items = list(amount_dict.items()) #making list to have indexes in case when info splitted into 2 lines
                    amount_key, amount_value = get_key_value(items, name) 
                    for mu in measure_unit_thousands_list:
                        if amount_key.count(mu) > 0:
                            ticker.amount = float(amount_value) * 1000       
                            #print(f"Количество акций - {ticker.amount} шт.")
                            return True
                    for mu in measure_unit_mil_list:
                        if amount_key.count(mu) > 0:
                            ticker.amount = float(amount_value) * 1000000
                            #print(f"Количество акций - {ticker.amount} шт.")
                            return True
                    ticker.amount = float(amount_value)
                    #print(f"Количество акций - {ticker.amount} шт.")
                    return True

def get_key_value(items, name): #func in case line splitted into 2 lines, we get next line
    for key,value in items:
        #print(key, value)
        if key.count(name) > 0:
            amount_key = key
            amount_value = value
            #print(amount_key, amount_value)
            if amount_value == "": 
                index_actual_pair = items.index((key, value))
                amount_tuple = items[index_actual_pair + 1] #tuple (info, data) from next line
                amount_value = amount_tuple[1].split("  ")[0]
                amount_key = amount_tuple[0]
                amount_value = amount_tuple[1]
            amount_key, amount_value = correct_data(amount_key, amount_value) #check if key = info and values = numbers and all correct
            amount_value = "".join(amount_value.split())
            #print(amount_key, "|", amount_value)
            return (amount_key, amount_value)

def alldigit(line):
    edited_line = "".join(line.split())
    edited_line = edited_line.replace("(","")
    edited_line = edited_line.replace(")","")
    if edited_line.isdigit() == True:
        return True
    return False

def tinkoff_api():
    ticker_data = str()
    ticker_price_quotation = str()
    ticker_price_response = str()
    token = os.environ["TOKEN"]
    with Client(token) as client:
        ticker_data = client.instruments.find_instrument(query = ticker.name).instruments
        #print(ticker_data)
        for i in ticker_data:
            if i.ticker.lower() == ticker.name:
                ticker_data_choice = i
        ticker_price_response = client.market_data.get_last_prices(figi = [ticker_data_choice.figi])
        ticker_price_quotation = ticker_price_response.last_prices[0].price
        ticker.price = float(str(ticker_price_quotation.units) + "." + str(ticker_price_quotation.nano))
        #print(ticker_price)

def write_db():
    if ticker.pe != 0 and ticker.ps != 0:
        try:
            with sql.connect(host="127.0.0.1", user = "Kirill", #input("Type user name: "), 
                             password = "password", #getpass.getpass("Type password: "), 
                             database = "fm") as connection:
                query_select =  "SELECT * from fm_table"
                query_insert = "INSERT INTO fm_table (ticker, revenue, income, pe, ps, amount, price, cap) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                with connection.cursor() as cursor:
                    #to see columns
                    cursor.execute("desc fm_table")
                    print_db([column[0] for column in cursor.fetchall()])   
                    #to add data
                    data = (ticker.name, ticker.viruchka, ticker.pribyl, ticker.pe,
                           ticker.ps, ticker.amount, ticker.price, ticker.capitalization)
                    cursor.execute(query_insert, data)
                    connection.commit()
                    #to print all lines
                    cursor.execute(query_select)
                    result = cursor.fetchall()
                    for line in result:
                        print_db(line)
        except sql.Error as e:
            print(e)

def print_db(line):
    for i in line:
        print(f'{i:<18}',end = "")
    print(end="\n")

def analyze_data(): #just do the math
    ticker.capitalization = ticker.price * ticker.amount
    if ticker.pribyl != 0:
        ticker.pe = ticker.capitalization / ticker.pribyl
    if ticker.viruchka != 0:
        ticker.ps = ticker.capitalization / ticker.viruchka

def timetrack(func):
    def count_time(*arg):
        start_time = time.time() #checking how long code executes
        result = func(*arg)
        print(f"--- {time.time() - start_time} seconds ---")
        return result
    return count_time

@timetrack
def run(url, name, method):#just run the program
    ticker.url = url
    filename = get_file(name) 
    pages = read_content(str(filename))
    #collect_data(pages)
    #get_price(method)
    #analyze_data()
    #write_db()
    #print_data()
    #return (ticker.pe, ticker.ps)

ticker = Ticker()
filename = str()
pages = list()
method = "t"

if __name__ == "__main__":
    name = "mtss"#input("Type ticker name: ")
    run(docs[1], name, method)
    

