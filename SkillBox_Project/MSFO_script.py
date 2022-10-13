#script to collect and analyze data from msfo sheets and real stock price

from string import whitespace
import PyPDF2
import tabula
import os
import requests
import pdfplumber

class Ticker():
    def _init_(self):
        self.ticker_name = str()
        self.pribyl = 0
        self.viruchka = int()
        self.stock_price = int()

def get_file(tkr, url): # take url of the file
    global filename
    file = requests.get(url)
    tkr.ticker_name = "ticker" #input("Type ticker: ")
    filename = f"{tkr.ticker_name}_MSFO.pdf"
    open(filename,'wb').write(file.content)
    print("Done")

def edit_data(text): #takes whole str doc and return list of str
    global ed
    clear_text = str()
    stroki = list()
    for stroka in text.splitlines():
        if len(stroka.strip()) == 0 or stroka == "\n":
            stroka = stroka.strip(" \n")
            continue
        if stroka[0].isupper() == True:
            clear_text = del_whitespaces(clear_text)
            stroki.append(clear_text)
            clear_text = ""
        clear_text += stroka + " "
        for word in stroka.split():
            if word in ["тыс.", "тыс", "тысячах", "thousands"]:
                ed = 1000 #measuring unit
            if word in ["млн.", "млн", "миллионах", "millions"]:
                ed = 1000000 #measuring unit
    #print(ed)
    return stroki

def del_whitespaces(clear_text):
    while clear_text.count("  ") != 0:
        whitespaces = clear_text.find("  ")
        if (whitespaces - 1 >= 0) and (whitespaces + 2 < len(clear_text)):
            if clear_text[whitespaces - 1].isdigit() == False and clear_text[whitespaces + 2].isdigit() == False:
                clear_text = clear_text.replace("  ", " ", 1)
            else:
                break
        elif (whitespaces == 0) and (whitespaces + 2 < len(clear_text)):
            if clear_text[whitespaces + 2].isdigit() == False:
                clear_text = clear_text.replace("  ", " ", 1)
            else:
                break
        elif (whitespaces - 1 >= 0) and (whitespaces + 2 == len(clear_text) - 1):
            if clear_text[whitespaces - 1].isdigit() == False:
                clear_text = clear_text.replace("  ", " ", 1)
            else:
                break
        else:
            break
    return clear_text

def read_content(tkr, filename):
    info_pribyl = "No data"
    _pdf = open(filename, 'rb')
    pdf_file = PyPDF2.PdfFileReader(_pdf, strict=False)
    page_dohod = pdf_file.pages
    for page in page_dohod:
        info = page.extract_text()
        info = edit_data(text = info) #info now is list
        for i in info:
            print(i)
    #for param in info.splitlines():
    #    if param.startswith("Прибыль за год") == True or param.startswith("Чистая прибыль") == True:
    #        info_pribyl = f"{param}"
    #        tkr.pribyl = param.split("  ")[1].lstrip()
    #        break
    #print(info_pribyl, "необходимое число -", tkr.pribyl)
        
def analyze_data():
    pass

#def tab(url):
#    data = tabula.read_pdf(url, pages = '12', stream = True, guess=False)
#    print(data)

#def plumb(url):
#    pdf = pdfplumber.open(url)
#    table_setting={
#    "vertical_strategy": "text",
#    "horizontal_strategy": "text",
#    }
#    print(pdf.pages[9].extract_table(table_setting)) 
#tab(url = filename)
#plumb(url = filename)#сторонние библиотеки для обработки pdf и таблиц


docs = ["https://www.magnit.com/upload/iblock/4e4/%D0%905.12_%D0%9F%D0%BE%D0%B4%D0%BF%D0%B8%D1%81%D0%B0%D0%BD%D0%BD%D0%B0%D1%8F%20%D1%84%D0%B8%D0%BD%D0%B0%D0%BD%D1%81%D0%BE%D0%B2%D0%B0%D1%8F%20%D0%BE%D1%82%D1%87%D0%B5%D1%82%D0%BD%D0%BE%D1%81%D1%82%D1%8C%20%D1%81%20%D0%90%D0%97_%D0%9C%D0%B0%D0%B3%D0%BD%D0%B8%D1%82_2021%20(%D1%80%D1%83%D1%81%D1%81).pdf",
        "https://mts.ru/upload/contents/10677/mts_ras_fs_21-r.pdf",
        "https://acdn.tinkoff.ru/static/documents/223e5d7f-6d12-429f-aae1-a25b154ea3e2.pdf",
        ]

file_url = docs[0]
ticker = Ticker()

get_file(tkr = ticker, url = file_url)
read_content(tkr = ticker, filename = filename)
