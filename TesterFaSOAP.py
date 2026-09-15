import sys
import os
from tkinter import *
from tkinter.filedialog import asksaveasfilename
from tkinter.ttk import Combobox
from tkinter import scrolledtext
import tkinter as tk
import random
import string
import datetime
import time
from jinja2 import Template
import requests
import logging
from russian_names import RussianNames
import re
from xml.etree import ElementTree as ET

# Получаем директорию текущего скрипта
script_dir = os.path.dirname(os.path.abspath(__file__))
cfg_dir = os.path.join(script_dir, "cfg")
log_dir = os.path.join(script_dir, "log")

# Создаем папки, если их нет
os.makedirs(cfg_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

# Дальше ваш код
print("Программа запущена успешно")

version = 1.3
window = Tk()
window.title("Tester Fraud-Analyze")
window.geometry('1196x830')
window.iconbitmap(os.path.join(cfg_dir, 'ok.ico'))

fixPayer = 0

# Настройки логирования
logging.basicConfig(
    filename=os.path.join(log_dir, "LOG___" + str(time.strftime('%Y-%m-%d___%H-%M-%S')) + ".log"),
    filemode="w",
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='[%Y-%m-%d] %H:%M:%S')

logging.info("Запуск программы тестирования")

# Получение URL из конфига
with open(os.path.join(cfg_dir, "url.cfg"), encoding='utf-8') as file:
    url_cfg = file.read()
    logging.info("Читаем url.cfg")

# Чтение шаблонов документов\запросов
with open(os.path.join(cfg_dir, "Template_decision.xml"), encoding='utf-8') as file:
    Template_decision = file.read()
    logging.info("Читаем Template_decision.xml")

decision = """<?xml version='1.0' encoding='UTF-8'?>
<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
<S:Body><ns2:process xmlns:ns2="http://ws.socket.fraud.bssys.com/"><arg0>""" + Template_decision + """</arg0></ns2:process></S:Body></S:Envelope>"""

with open(os.path.join(cfg_dir, "Template_queryDecision.xml"), encoding='utf-8') as file:
    Template_queryDecision = file.read()
    logging.info("Читаем Template_queryDecision.xml")

query_result = """<?xml version='1.0' encoding='UTF-8'?>
<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
<S:Body><ns2:process xmlns:ns2="http://ws.socket.fraud.bssys.com/"><arg0>""" + Template_queryDecision + """</arg0></ns2:process></S:Body></S:Envelope>"""

with open(os.path.join(cfg_dir, "Template_PaymentDocument.xml"), encoding='utf-8') as file:
    Template_PaymentDocument = file.read()
    logging.info("Читаем Template_PaymentDocument.xml")
list_bucket_result = """<?xml version='1.0' encoding='UTF-8'?>
<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
<S:Body><ns2:process xmlns:ns2="http://ws.socket.fraud.bssys.com/"><arg0>""" + Template_PaymentDocument + """</arg0></ns2:process></S:Body></S:Envelope>"""

with open(os.path.join(cfg_dir, "Template_incomingDocument.xml"), encoding='utf-8') as file:
    Template_incomingDocument = file.read()
    logging.info("Читаем Template_incomingDocument.xml")
incomingDocument = """<?xml version='1.0' encoding='UTF-8'?>
<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
<S:Body><ns2:process xmlns:ns2="http://ws.socket.fraud.bssys.com/"><arg0>""" + Template_incomingDocument + """</arg0></ns2:process></S:Body></S:Envelope>"""

with open(os.path.join(cfg_dir, "Template_DC_checkDocumentRequest.xml"), encoding='utf-8') as file:
    Template_checkDocumentRequest = file.read()
    logging.info("Читаем Template_checkDocumentRequest.xml")
checkDocumentRequest = """<?xml version='1.0' encoding='UTF-8'?>
<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
<S:Body><ns2:process xmlns:ns2="http://ws.socket.fraud.bssys.com/"><arg0>""" + Template_checkDocumentRequest + """</arg0></ns2:process></S:Body></S:Envelope>"""


# Запрос проверки агента ТСП использует тот же SOAP-метод process.
with open(os.path.join(cfg_dir, "requestIPOAgentTSP.xml"), encoding='utf-8') as file:
    Template_requestIPOAgentTSP = file.read()
    logging.info("Читаем requestIPOAgentTSP.xml")
requestIPOAgentTSP = """<?xml version='1.0' encoding='UTF-8'?>
<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
<S:Body><ns2:process xmlns:ns2="http://ws.socket.fraud.bssys.com/"><arg0>""" + Template_requestIPOAgentTSP + """</arg0></ns2:process></S:Body></S:Envelope>"""


def render_ipo_agent_tsp():
    return Template(requestIPOAgentTSP).render(
        time=format_time(),
        payerId=txt_idpayer.get(),
        payerName=txt_payer.get(),
        receiverName=txt_receiver.get(),
        payerAccount=txt_payerAccount.get(),
        docRef=txt_ref.get(),
        payerPhone=txt_phone.get(),
    )


# Сохранение URL в конфиг
def save_url():
    with open(os.path.join(cfg_dir, "url.cfg"), "w") as file:
        file.write(txt_url.get())
        logging.info("URL изменён")


# Генерация данных для полей документа
def format_time():
    t = datetime.datetime.now()
    s = t.strftime('%Y-%m-%d' + 'T' + '%H:%M:%S.%f')
    return s[:-3] + '+03:00'


def random_char(y):
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(y))


def random_acc():
    return random.randrange(100000000000, 999999999999, 1)


def random_char_min():
    return random.randrange(1, 9999, 1)


# Генерация и отправка документа
def gen_doc_and_send_request():
    txt_answer.configure(state="normal")
    txt_answer.delete("1.0", tk.END)
    txt_total.delete("1.0", tk.END)
    x = int(spin_sum_request.get())
    start_time = time.time()
    i = 1
    while i <= x:
        i = i + 1
        template = Template(requestIPOAgentTSP if out_or_in.get() == "requestIPOAgentTSP" else list_bucket_result)
        result = template.render(
            documentType=documentType.get(),
            phys_or_jur=phys_or_jur.get(),
            fps_type=fps_type.get(),
            time=format_time(),
            payerId=random_char_min(),
            documentNumber=random_char_min(),
            amount=random_char_min(),
            # payerName='ООО' + ' Плательщик ' + random_char(8),
            # receiverName='ООО' + ' Получатель ' + random_char(8),
            payerName=RussianNames().get_person(),
            receiverName=RussianNames().get_person(),
            payerAccount='40704810' + str(random_acc()),
            receiverAccount='40899810' + str(random_acc()),
            paymentSBP=sbp_or_no.get(),
            docRef=random_char(40),
            payerPhone=txt_phone.get(),
        )
        endpoint = txt_url.get()
        body = result
        body = body.encode('utf-8')
        session = requests.session()
        session.headers = {"Content-Type": "text/xml; charset=utf-8"}
        session.headers.update({"Content-Length": str(len(body))})
        logging.info("Пробуем отправить документ")
        try:
            response = session.post(url=endpoint, data=body, verify=False)
            txt_total.configure(bg="#90EE90")
            logging.info("Документ успешно отправлен")
            logging.debug("========== Тело документа ==========\n" + str(body))
            txt_history.configure(state="normal")
            txt_history.insert(END, "Наполнение, итерация: " + str(i - 1) + "\n")
            txt_history.configure(state="disabled")
        except requests.exceptions.Timeout:
            txt_total.insert(tk.INSERT, 'Ошибка: Timeout')
            txt_total.configure(bg="#FA8072")
            logging.info(str(endpoint) + " ---> Ошибка: Timeout")
        except requests.exceptions.TooManyRedirects:
            txt_total.insert(tk.INSERT, 'Ошибка: TooManyRedirects')
            txt_total.configure(bg="#FA8072")
            logging.info(str(endpoint) + " ---> Ошибка: TooManyRedirects")
        except requests.exceptions.RequestException as e:
            txt_total.insert(tk.INSERT, 'Ошибка: RequestException')
            txt_total.configure(bg="#FA8072")
            logging.info(str(endpoint) + " ---> Ошибка: RequestException")

    print("Отправлено запросов: ", i - 1)
    print("Время выполнения: %s секунд" % f"{(time.time() - start_time):.3f}")
    response_decode = response.content
    response_decode = (response_decode.decode('utf-8'))
    txt_answer.insert(tk.INSERT, response_decode)
    txt_answer.configure(state='disabled')
    txt_total.delete("1.0", tk.END)
    print("\nВремя выполнения: %s секунд" % f"{(time.time() - start_time):.3f}")
    txt_total.insert(tk.INSERT,
                     'Время выполнения: ' + f"{time.time() - start_time:.3f}"[:5] + ' секунд\n' +
                     'Среднее время: ~ ' + f"{(time.time() - start_time) / (i - 1) if i > 1 else 0:.3f}"[
                                           :5] + ' секунд')


# чекбокс фиксации id плательщика
checkbuttonFixPayer = BooleanVar()
enabled_checkbutton = Checkbutton(text="ФИКС Плательщика", variable=checkbuttonFixPayer)
enabled_checkbutton.grid(column=1, row=4, sticky="E", padx=2)

def update_fps_type(event=None):
    if sbp_or_no.get() == "НЕТ":
        fps_type['values'] = ("NULL", "SBPQR", "B2B")
        fps_type.current(0)
    else:
        fps_type['values'] = ("C2C", "SBPQR", "B2C", "B2B")
        fps_type.current(0)
        documentType.current(0)

    # Сбросить значение fps_type, если текущее не входит в новый список
    current_val = fps_type.get()
    if current_val and current_val not in fps_type['values']:
        fps_type.set('')

# Генерация документа
def gen_doc():
    txt_request.delete("1.0", tk.END)
    txt_answer.configure(state='normal')
    txt_answer.delete("1.0", tk.END)
    txt_total.delete("1.0", tk.END)
    # txt_idpayer.delete("0", tk.END)
    # txt_payer.delete("0", tk.END)
    txt_receiver.delete("0", tk.END)
    txt_ref.delete("0", tk.END)
    txt_receiverAccount.delete("0", tk.END)

    if checkbuttonFixPayer.get():
        fixPayer = 1
        logging.info("Генерация документа с ФИКС Плательщик")
        txt_idpayer.configure(bg="#FFCCCC")
        txt_payer.configure(bg="#FFCCCC")
        txt_payerAccount.configure(bg="#FFCCCC")
    else:
        fixPayer = 0
        txt_idpayer.configure(bg="#FFFFFF")
        txt_payer.configure(bg="#FFFFFF")
        txt_payerAccount.configure(bg="#FFFFFF")

    if fixPayer == 0:
        txt_idpayer.delete("0", tk.END)
        txt_payer.delete("0", tk.END)
        txt_payerAccount.delete("0", tk.END)
        txt_docnum.delete("0", tk.END)
        txt_idpayer.insert(tk.INSERT, random_char_min())
        txt_payer.insert(tk.INSERT, RussianNames().get_person())
        txt_payerAccount.insert(tk.INSERT, '40704810' + str(random_acc()))
        txt_docnum.insert(tk.INSERT, random_char_min())
    else:
        id_payer_temp = txt_idpayer.get()
        payer_temp = txt_payer.get()
        payerAccount_temp = txt_payerAccount.get()
        docnum_temp = txt_docnum.get()
        txt_idpayer.delete("0", tk.END)
        txt_payer.delete("0", tk.END)
        txt_payerAccount.delete("0", tk.END)
        txt_docnum.delete("0", tk.END)
        txt_idpayer.insert(tk.INSERT, id_payer_temp)
        txt_payer.insert(tk.INSERT, payer_temp)
        txt_payerAccount.insert(tk.INSERT, payerAccount_temp)
        txt_docnum.insert(tk.INSERT, str(int(docnum_temp) + 1))


    update_fps_type()

    # txt_payer.insert(tk.INSERT, 'ООО' + ' Плательщик ' + random_char(8))
    # txt_receiver.insert(tk.INSERT, 'ООО' + ' Получатель ' + random_char(8))
    # txt_payer.insert(tk.INSERT, RussianNames().get_person())
    txt_receiver.insert(tk.INSERT, RussianNames().get_person())
    txt_ref.insert(tk.INSERT, random_char(40))
    txt_receiverAccount.insert(tk.INSERT, '40899810' + str(random_acc()))

    if out_or_in.get() == "paymentDocument":
        sbp_or_no.configure(state="readonly")
        phys_or_jur.configure(state="readonly")
        fps_type.configure(state="readonly")
        template = Template(list_bucket_result)
        result = template.render(
            fps_type=fps_type.get(),
            documentType=documentType.get(),
            phys_or_jur=phys_or_jur.get(),
            time=format_time(),
            payerId=txt_idpayer.get(),
            documentNumber=txt_docnum.get(),
            amount=random_char_min(),
            payerName=txt_payer.get(),
            receiverName=txt_receiver.get(),
            payerAccount=txt_payerAccount.get(),
            receiverAccount=txt_receiverAccount.get(),
            paymentSBP=sbp_or_no.get(),
            docRef=txt_ref.get(),
            payerPhone=txt_phone.get(),
        )
        txt_request.insert(tk.INSERT, result)
        txt_answer.insert(tk.INSERT, "Сгенерирован новый ИСХОДЯЩИЙ документ, нажмите кнопку\n<Отправка документа>\n\n"
                                     "Если требуется изменить реквизиты документа - отредактировать значения в полях"
                                     " и нажать:\n<Сохранить изменения>, далее для отправки - <Отправка документа>\n\n"
                                     "Если редактируете сам запрос (тело) - сразу <Отправить запрос>")
        logging.info(
            "Сгенерирован новый ИСХОДЯЩИЙ документ № " + str(txt_docnum.get()) + ", референс " + str(txt_ref.get()))
    elif out_or_in.get() == "requestIPOAgentTSP":
        txt_request.insert(tk.INSERT, render_ipo_agent_tsp())
        txt_answer.insert(tk.INSERT, "Сгенерирован новый requestIPOAgentTSP, нажмите кнопку\n<Отправка документа>")
        logging.info("Сгенерирован новый requestIPOAgentTSP, референс " + str(txt_ref.get()))
    else:
        sbp_or_no.current(0)
        phys_or_jur.current(0)
        documentType.current(0)
        sbp_or_no.configure(state="disable")
        phys_or_jur.configure(state="disable")
        fps_type.configure(state="readonly")
        template = Template(incomingDocument)
        result = template.render(
            fps_type=fps_type.get(),
            documentType=documentType.get(),
            phys_or_jur=phys_or_jur.get(),
            time=format_time(),
            payerId=txt_idpayer.get(),
            documentNumber=txt_docnum.get(),
            amount=random_char_min(),
            payerName=txt_payer.get(),
            receiverName=txt_receiver.get(),
            payerAccount=txt_payerAccount.get(),
            receiverAccount=txt_receiverAccount.get(),
            docRef=txt_ref.get(),
            payerPhone=txt_phone.get(),
        )
        txt_request.insert(tk.INSERT, result)
        txt_answer.insert(tk.INSERT, "Сгенерирован новый ВХОДЯЩИЙ документ, нажмите кнопку\n<Отправка документа>\n\n"
                                     "Если требуется изменить реквизиты документа - отредактировать значения в полях"
                                     " и нажать:\n<Сохранить изменения>, далее для отправки - <Отправка документа>")
        logging.info(
            "Сгенерирован новый ВХОДЯЩИЙ документ № " + str(txt_docnum.get()) + ", референс " + str(txt_ref.get()))

# Сохранение документа
def save_doc():
    txt_request.delete("1.0", tk.END)
    txt_answer.configure(state='normal')
    txt_answer.delete("1.0", tk.END)
    txt_total.delete("1.0", tk.END)
    if out_or_in.get() == "paymentDocument":
        template = Template(list_bucket_result)
        result = template.render(
            fps_type=fps_type.get(),
            documentType=documentType.get(),
            phys_or_jur=phys_or_jur.get(),
            time=format_time(),
            payerId=txt_idpayer.get(),
            documentNumber=txt_docnum.get(),
            amount=random_char_min(),
            payerName=txt_payer.get(),
            receiverName=txt_receiver.get(),
            payerAccount=txt_payerAccount.get(),
            receiverAccount=txt_receiverAccount.get(),
            paymentSBP=sbp_or_no.get(),
            docRef=txt_ref.get(),
            payerPhone=txt_phone.get(),
        )

        txt_request.insert(tk.INSERT, result)
        txt_answer.insert(tk.INSERT, "Изменённый ИСХОДЯЩИЙ документ сохранён, нажмите кнопку\n<Отправка документа>")
        logging.info("Сохранён изменённый ИСХОДЯЩИЙ документ <" + str(out_or_in.get()) + "> № " + str(
            txt_docnum.get()) + ", референс " + str(txt_ref.get()))
    elif out_or_in.get() == "requestIPOAgentTSP":
        txt_request.insert(tk.INSERT, render_ipo_agent_tsp())
        txt_answer.insert(tk.INSERT, "Изменённый документ сохранён: requestIPOAgentTSP, нажмите кнопку\n<Отправка документа>")
        logging.info("Изменённый документ сохранён: requestIPOAgentTSP, референс " + str(txt_ref.get()))
    else:
        sbp_or_no.current(0)
        phys_or_jur.current(0)
        sbp_or_no.configure(state="disable")
        phys_or_jur.configure(state="disable")
        fps_type.configure(state="readonly")
        template = Template(incomingDocument)
        result = template.render(
            fps_type=fps_type.get(),
            phys_or_jur=phys_or_jur.get(),
            time=format_time(),
            payerId=txt_idpayer.get(),
            documentNumber=txt_docnum.get(),
            amount=random_char_min(),
            payerName=txt_payer.get(),
            receiverName=txt_receiver.get(),
            payerAccount=txt_payerAccount.get(),
            receiverAccount=txt_receiverAccount.get(),
            docRef=txt_ref.get(),
            payerPhone=txt_phone.get(),
        )
        txt_request.insert(tk.INSERT, result)
        txt_answer.insert(tk.INSERT, "Изменённый ВХОДЯЩИЙ документ сохранён, нажмите кнопку:\n<Отправка документа>")
        logging.info("Сохранён изменённый ВХОДЯЩИЙ документ <" + str(out_or_in.get()) + "> № " + str(
            txt_docnum.get()) + ", референс " + str(txt_ref.get()))


# Отправка документа
def send_request():
    global response, last_execution_time
    txt_answer.configure(state='normal')
    txt_answer.delete("1.0", tk.END)
    txt_total.configure(state="normal")
    txt_total.delete("1.0", tk.END)
    start_time = time.time()
    endpoint = txt_url.get()
    body = txt_request.get("1.0", tk.END)
    body = body.encode('utf-8')
    session = requests.session()
    session.headers = {"Content-Type": "text/xml; charset=utf-8"}
    session.headers.update({"Content-Length": str(len(body))})
    logging.info("Пробуем отправить документ, референс " + str(txt_ref.get()))
    try:
        response = session.post(url=endpoint, data=body, verify=False, timeout=30)
        logging.info("Успешно отправлен документ <" + str(out_or_in.get()) + "> № " + str(
            txt_docnum.get()) + ", референс " + str(txt_ref.get()))
        logging.debug("========== Тело документа ==========\n" + str(body))
        txt_total.configure(bg="#90EE90")
        txt_history.configure(state="normal")
        if out_or_in.get() == "requestIPOAgentTSP":
            txt_history.insert("1.0", "[requestIPOAgentTSP] id " + txt_idpayer.get() + " | " + txt_ref.get() + "\n", "query")
        elif ((sbp_or_no.get() == "1") or (sbp_or_no.get() == "2")) and documentType.get() == "PDR":
            txt_history.insert("1.0",
                               "id " + txt_idpayer.get() + " | N " + txt_docnum.get() + " | СБП " + sbp_or_no.get() + " итерация\n",
                               "sbp")
        elif (sbp_or_no.get() == "НЕТ") and (documentType.get() == "PDR") and out_or_in.get() == "paymentDocument":
            txt_history.insert("1.0",
                               "> Исх: id " + txt_idpayer.get() + " | N " + txt_docnum.get() + " | СБП " + sbp_or_no.get() + "\n",
                               "nosbp")
        elif (sbp_or_no.get() == "НЕТ") and (documentType.get() == "PDR") and out_or_in.get() == "incomingDocument":
            txt_history.insert("1.0",
                               "< Вх: id " + txt_idpayer.get() + " | N " + txt_docnum.get() + " | Вх СБП " + "\n",
                               "nosbp")
        else:
            txt_history.insert("1.0", "id " + txt_idpayer.get() + " | N " + txt_docnum.get() + " | Цифр. рубль" + "\n",
                               "dc")
        txt_history.configure(state="disabled")
        txt_ref2.delete(0, END)
        txt_ref2.insert(END, txt_ref.get())
        txt_ref2.delete(0, END)
        txt_ref2.insert(END, txt_ref.get())
        txt_ref2.delete(0, END)
        txt_ref2.insert(END, txt_ref.get())

    except requests.exceptions.Timeout:
        txt_total.insert(tk.INSERT, 'Ошибка: Timeout')
        logging.info(str(endpoint) + " ---> Ошибка: Timeout")
        txt_total.configure(bg="#FA8072")
        return
    except requests.exceptions.TooManyRedirects:
        txt_total.insert(tk.INSERT, 'Ошибка: TooManyRedirects')
        logging.info(str(endpoint) + " ---> Ошибка: TooManyRedirects")
        txt_total.configure(bg="#FA8072")
        return
    except requests.exceptions.RequestException as e:
        txt_total.insert(tk.INSERT, 'Ошибка: RequestException')
        logging.info(str(endpoint) + " ---> Ошибка: RequestException")
        txt_total.configure(bg="#FA8072")
        return

    response_decode = response.content
    response_decode = (response_decode.decode('utf-8'))
    txt_answer.insert(tk.INSERT, response_decode)
    txt_answer.configure(state='disabled')
    #txt_total.insert(tk.INSERT, 'Время выполнения: ')
    #txt_total.insert(tk.INSERT, f"{(time.time() - start_time):.3f}")
    #txt_total.insert(tk.INSERT, ' секунд')
    last_execution_time = time.time() - start_time
    analyzeResult(last_execution_time)


# Генерация и отправка запроса queryDecision
def gen_query_result():
    txt_request.delete("1.0", tk.END)
    txt_answer.configure(state='normal')
    txt_answer.delete("1.0", tk.END)
    txt_total.delete("1.0", tk.END)
    template = Template(query_result)
    result = template.render(
        docRef=txt_ref2.get(),
    )

    txt_request.insert(tk.INSERT, result)

    start_time = time.time()
    endpoint = txt_url.get()
    body = txt_request.get("1.0", tk.END)
    body = body.encode('utf-8')
    session = requests.session()
    session.headers = {"Content-Type": "text/xml; charset=utf-8"}
    session.headers.update({"Content-Length": str(len(body))})
    logging.info("Пробуем отправить запрос <queryDecision> к референсу " + str(txt_ref2.get()))
    try:
        response = session.post(url=endpoint, data=body, verify=False)
        txt_total.configure(bg="#90EE90")
        logging.info("Запрос <queryDecision> успешно отправлен к референсу " + str(txt_ref2.get()))
        logging.debug("========== Тело запроса ==========\n" + str(body))
        txt_history.configure(state="normal")
        txt_history.insert("1.0", "[queryDec] " + str(txt_ref2.get())[:11] + "...\n", "query")
        txt_history.configure(state="disabled")
    except requests.exceptions.Timeout:
        txt_total.insert(tk.INSERT, 'Ошибка: Timeout')
        logging.info(str(endpoint) + " ---> Ошибка: Timeout")
        txt_total.configure(bg="#FA8072")
    except requests.exceptions.TooManyRedirects:
        txt_total.insert(tk.INSERT, 'Ошибка: TooManyRedirects')
        logging.info(str(endpoint) + " ---> Ошибка: TooManyRedirects")
        txt_total.configure(bg="#FA8072")
    except requests.exceptions.RequestException as e:
        txt_total.insert(tk.INSERT, 'Ошибка: RequestException')
        logging.info(str(endpoint) + " ---> Ошибка: RequestException")
        txt_total.configure(bg="#FA8072")

    response_decode = response.content
    response_decode = (response_decode.decode('utf-8'))
    txt_answer.insert(tk.INSERT, response_decode)
    txt_answer.configure(state='disabled')
    txt_total.insert(tk.INSERT, 'Время выполнения: ')
    txt_total.insert(tk.INSERT, f"{(time.time() - start_time):.3f}")
    txt_total.insert(tk.INSERT, ' секунд')
    analyzeResult()


# Генерация и отправка запроса decision
def gen_decision():
    txt_request.delete("1.0", tk.END)
    txt_answer.configure(state='normal')
    txt_answer.delete("1.0", tk.END)
    txt_total.delete("1.0", tk.END)
    template = Template(decision)
    result = template.render(
        docRef=txt_ref2.get(),
        decision=get_decision_value(),
        time=format_time(),
    )
    txt_request.insert(tk.INSERT, result)
    start_time = time.time()
    endpoint = txt_url.get()
    body = txt_request.get("1.0", tk.END)
    body = body.encode('utf-8')
    session = requests.session()
    session.headers = {"Content-Type": "text/xml; charset=utf-8"}
    session.headers.update({"Content-Length": str(len(body))})
    logging.info("Пробуем отправить запрос <decision> к референсу " + str(txt_ref2.get()))
    try:
        response = session.post(url=endpoint, data=body, verify=False)
        txt_total.configure(bg="#90EE90")
        logging.info("Запрос <decision> успешно отправлен к референсу " + str(txt_ref2.get()))
        logging.debug("========== Тело запроса ==========\n" + str(body))
        txt_history.configure(state="normal")
        txt_history.insert("1.0", "[decision] " + str(txt_ref2.get())[:11] + "...\n", "query")
        txt_history.configure(state="disabled")
    except requests.exceptions.Timeout:
        txt_total.insert(tk.INSERT, 'Ошибка: Timeout')
        logging.info(str(endpoint) + " ---> Ошибка: Timeout")
        txt_total.configure(bg="#FA8072")
    except requests.exceptions.TooManyRedirects:
        txt_total.insert(tk.INSERT, 'Ошибка: TooManyRedirects')
        logging.info(str(endpoint) + " ---> Ошибка: TooManyRedirects")
        txt_total.configure(bg="#FA8072")
    except requests.exceptions.RequestException as e:
        txt_total.insert(tk.INSERT, 'Ошибка: RequestException')
        logging.info(str(endpoint) + " ---> Ошибка: RequestException")
        txt_total.configure(bg="#FA8072")

    response_decode = response.content
    response_decode = (response_decode.decode('utf-8'))
    txt_answer.insert(tk.INSERT, response_decode)
    txt_answer.configure(state='disabled')
    txt_total.insert(tk.INSERT, 'Время выполнения: ')
    txt_total.insert(tk.INSERT, f"{(time.time() - start_time):.3f}")
    txt_total.insert(tk.INSERT, ' секунд')


def gen_checkDocumentRequest():
    txt_request.delete("1.0", tk.END)
    txt_answer.configure(state='normal')
    txt_answer.delete("1.0", tk.END)
    txt_total.delete("1.0", tk.END)
    template = Template(checkDocumentRequest)
    result = template.render(
        docRef=txt_ref2.get(),
        time=format_time(),
    )
    txt_request.insert(tk.INSERT, result)
    start_time = time.time()
    endpoint = txt_url.get()
    body = txt_request.get("1.0", tk.END)
    body = body.encode('utf-8')
    session = requests.session()
    session.headers = {"Content-Type": "text/xml; charset=utf-8"}
    session.headers.update({"Content-Length": str(len(body))})
    logging.info("Пробуем отправить запрос <checkDocumentRequest> к референсу " + str(txt_ref2.get()))
    try:
        response = session.post(url=endpoint, data=body, verify=False)
        txt_total.configure(bg="#90EE90")
        logging.info("Запрос <checkDocumentRequest> успешно отправлен к референсу " + str(txt_ref2.get()))
        logging.debug("========== Тело запроса ==========\n" + str(body))
        txt_history.configure(state="normal")
        txt_history.insert("1.0", "[check] " + str(txt_ref2.get())[:11] + "...\n", "query")
        txt_history.configure(state="disabled")
    except requests.exceptions.Timeout:
        txt_total.insert(tk.INSERT, 'Ошибка: Timeout')
        logging.info(str(endpoint) + " ---> Ошибка: Timeout")
        txt_total.configure(bg="#FA8072")
    except requests.exceptions.TooManyRedirects:
        txt_total.insert(tk.INSERT, 'Ошибка: TooManyRedirects')
        logging.info(str(endpoint) + " ---> Ошибка: TooManyRedirects")
        txt_total.configure(bg="#FA8072")
    except requests.exceptions.RequestException as e:
        txt_total.insert(tk.INSERT, 'Ошибка: RequestException')
        logging.info(str(endpoint) + " ---> Ошибка: RequestException")
        txt_total.configure(bg="#FA8072")

    response_decode = response.content
    response_decode = (response_decode.decode('utf-8'))
    txt_answer.insert(tk.INSERT, response_decode)
    txt_answer.configure(state='disabled')
    txt_total.insert(tk.INSERT, 'Время выполнения: ')
    txt_total.insert(tk.INSERT, f"{(time.time() - start_time):.3f}")
    txt_total.insert(tk.INSERT, ' секунд')


# Поиск по текстовому полю txt_request
def setup_search_for_txt_request():
    global search_positions, current_search_index

    search_positions = []
    current_search_index = -1

    search_frame = tk.Frame(window)
    search_frame.grid(column=0, row=18, columnspan=2, sticky="w", padx=10, pady=(0, 5))

    search_var = tk.StringVar()

    def search():
        text = search_var.get().strip()
        if not text:
            return

        txt_request.tag_remove("highlight", "1.0", tk.END)
        txt_request.tag_remove("current", "1.0", tk.END)
        search_positions.clear()

        pos = "1.0"
        while True:
            pos = txt_request.search(text, pos, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(text)}c"
            search_positions.append((pos, end))
            txt_request.tag_add("highlight", pos, end)
            pos = end

        txt_request.tag_config("highlight", background="#FFFACD")
        txt_request.tag_config("current", background="#FFA500")

        if search_positions:
            global current_search_index
            current_search_index = 0
            show_current()
            count_label.config(text=f"{current_search_index + 1}/{len(search_positions)}")

    def show_current():
        if not search_positions: return
        txt_request.tag_remove("current", "1.0", tk.END)
        start, end = search_positions[current_search_index]
        txt_request.tag_add("current", start, end)
        txt_request.see(start)

    def next():
        global current_search_index
        if search_positions:
            current_search_index = (current_search_index + 1) % len(search_positions)
            show_current()
            count_label.config(text=f"{current_search_index + 1}/{len(search_positions)}")
        else:
            search()

    def prev():
        global current_search_index
        if search_positions:
            current_search_index = (current_search_index - 1) % len(search_positions)
            show_current()
            count_label.config(text=f"{current_search_index + 1}/{len(search_positions)}")
        else:
            search()

    def clear():
        txt_request.tag_remove("highlight", "1.0", tk.END)
        txt_request.tag_remove("current", "1.0", tk.END)
        search_var.set("")
        search_positions.clear()
        count_label.config(text="")

    # Все в одну строку
    tk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=(0, 2))

    e = tk.Entry(search_frame, textvariable=search_var, width=18)
    e.pack(side=tk.LEFT, padx=(0, 2))

    tk.Button(search_frame, text="✕", command=clear,
              bg="#8B0000", fg="#eee", width=2).pack(side=tk.LEFT, padx=(1, 2))

    tk.Button(search_frame, text="Найти", command=search,
              bg="#ffcc00", width=6).pack(side=tk.LEFT, padx=(0, 2))

    tk.Button(search_frame, text="<", command=prev,
              bg="#ffcc00", fg="black", width=2).pack(side=tk.LEFT, padx=(0, 1))

    tk.Button(search_frame, text=">", command=next,
              bg="#ffcc00", fg="black", width=2).pack(side=tk.LEFT, padx=(0, 2))

    count_label = tk.Label(search_frame, text="", width=5)
    count_label.pack(side=tk.LEFT, padx=(0, 2))

    # Горячие клавиши
    e.bind('<Return>', lambda x: search())
    e.bind('<F3>', lambda x: next())
    e.bind('<Shift-F3>', lambda x: prev())


# Функция для настройки поиска в новом окне
def setup_search_for_new_window(text_widget, top_window):
    search_frame = tk.Frame(top_window)
    search_frame.pack(fill=tk.X, padx=8, pady=(0, 5))

    search_positions_new = []
    current_search_index_new = -1
    search_var_new = tk.StringVar()

    def search_new():
        nonlocal search_positions_new, current_search_index_new
        text = search_var_new.get().strip()
        if not text:
            return

        text_widget.tag_remove("highlight", "1.0", tk.END)
        text_widget.tag_remove("current", "1.0", tk.END)
        search_positions_new.clear()

        pos = "1.0"
        while True:
            pos = text_widget.search(text, pos, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(text)}c"
            search_positions_new.append((pos, end))
            text_widget.tag_add("highlight", pos, end)
            pos = end

        text_widget.tag_config("highlight", background="#FFFACD")
        text_widget.tag_config("current", background="#FFA500")

        if search_positions_new:
            current_search_index_new = 0
            show_current_new()
            count_label_new.config(text=f"{current_search_index_new + 1}/{len(search_positions_new)}")

    def show_current_new():
        if not search_positions_new: return
        text_widget.tag_remove("current", "1.0", tk.END)
        start, end = search_positions_new[current_search_index_new]
        text_widget.tag_add("current", start, end)
        text_widget.see(start)

    def next_new():
        nonlocal current_search_index_new
        if search_positions_new:
            current_search_index_new = (current_search_index_new + 1) % len(search_positions_new)
            show_current_new()
            count_label_new.config(text=f"{current_search_index_new + 1}/{len(search_positions_new)}")
        else:
            search_new()

    def prev_new():
        nonlocal current_search_index_new
        if search_positions_new:
            current_search_index_new = (current_search_index_new - 1) % len(search_positions_new)
            show_current_new()
            count_label_new.config(text=f"{current_search_index_new + 1}/{len(search_positions_new)}")
        else:
            search_new()

    def clear_new():
        text_widget.tag_remove("highlight", "1.0", tk.END)
        text_widget.tag_remove("current", "1.0", tk.END)
        search_var_new.set("")
        search_positions_new.clear()
        count_label_new.config(text="")

    # Все в одну строку
    tk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=(0, 2))

    e = tk.Entry(search_frame, textvariable=search_var_new, width=18)
    e.pack(side=tk.LEFT, padx=(0, 2))

    tk.Button(search_frame, text="✕", command=clear_new,
              bg="#8B0000", fg="#eee", width=2).pack(side=tk.LEFT, padx=(1, 2))

    tk.Button(search_frame, text="Найти", command=search_new,
              bg="#ffcc00", width=6).pack(side=tk.LEFT, padx=(0, 2))

    tk.Button(search_frame, text="<", command=prev_new,
              bg="#ffcc00", fg="black", width=2).pack(side=tk.LEFT, padx=(0, 1))

    tk.Button(search_frame, text=">", command=next_new,
              bg="#ffcc00", fg="black", width=2).pack(side=tk.LEFT, padx=(0, 2))

    count_label_new = tk.Label(search_frame, text="", width=5)
    count_label_new.pack(side=tk.LEFT, padx=(0, 2))

    # Горячие клавиши
    e.bind('<Return>', lambda x: search_new())
    e.bind('<F3>', lambda x: next_new())
    e.bind('<Shift-F3>', lambda x: prev_new())


# кнопка сохранить URL
btn_save_url = tk.Button(
    master=window,
    text="Сохранить URL ->",
    command=save_url,
    width=18,
    bg="#ffcc00",
)
btn_save_url.grid(column=0, row=0)

# URL запроса
txt_url = Entry(window, width=50)
txt_url.grid(column=1, row=0)
txt_url.insert(tk.INSERT, url_cfg)

# версия
version = Label(text="v " + str(version), fg="#868686")
version.grid(column=3, row=0, sticky="E", padx=14)

# выбор: Исходящий или Входящий
label_out_or_in = Label(text="ИСХ / ВХ / ЦР (DC)", fg="#eee", bg="#333", width=18)
label_out_or_in.grid(column=0, row=1)
out_or_in = Combobox(window, width=22, state="readonly")
out_or_in['values'] = ("paymentDocument", "incomingDocument", "requestIPOAgentTSP")
out_or_in.current(0)  # установите вариант по умолчанию
out_or_in.grid(column=1, row=1, sticky="W", padx=4)

# выбор: Тип документа: Обычный PDR или Цифровой Рубль
documentType = Combobox(window, width=21, state="readonly")
documentType['values'] = ("PDR", "DCTransfer", "DCWithdrawal", "DCRefill", "DCSelfExectTransactionCreat")
documentType.current(0)  # установите вариант по умолчанию
documentType.grid(column=1, row=1, sticky="E", padx=4)

# выбор: СБП или нет
label_sbp_or_no = Label(text="СБП или нет", fg="#eee", bg="#8B0000", width=18)
label_sbp_or_no.grid(column=0, row=2)
sbp_or_no = Combobox(window, width=22, state="readonly")
sbp_or_no.bind('<<ComboboxSelected>>', update_fps_type)
sbp_or_no['values'] = ("НЕТ", 1, 2)
sbp_or_no.current(0)  # установите вариант по умолчанию
sbp_or_no.grid(column=1, row=2, sticky="W", padx=4)

# выбор: СБП тип
fps_type = Combobox(window, width=21, state="readonly")
fps_type['values'] = ("NULL", "C2C", "SBPQR", "B2C", "B2B")
fps_type.current(0)  # установите вариант по умолчанию
fps_type.grid(column=1, row=2, sticky="E", padx=4)

# выбор: ФЛ или ЮЛ
label_phys_or_jur = Label(text="ФЛ или ЮЛ", fg="#eee", bg="#333", width=18)
label_phys_or_jur.grid(column=0, row=3)
phys_or_jur = Combobox(window, width=47, state="readonly")
phys_or_jur['values'] = ("PHYSICAL", "JURIDICAL")
phys_or_jur.current(0)  # установите вариант по умолчанию
phys_or_jur.grid(column=1, row=3)

# поле сгенерированного документа - id плательщика
label_idpayer = Label(text="id плательщика", fg="#eee", bg="#333", width=18)
label_idpayer.grid(column=0, row=4)
txt_idpayer = Entry(window, width=22)
txt_idpayer.grid(column=1, row=4, sticky="W", padx=4)

# поле сгенерированного документа - счёт плательщика
label_payer = Label(text="Счёт плат | получ", fg="#eee", bg="#333", width=18)
label_payer.grid(column=0, row=5)
txt_payerAccount = Entry(window, width=24)
txt_payerAccount.grid(column=1, row=5, sticky=W, padx=4)

txt_receiverAccount = Entry(window, width=25)
txt_receiverAccount.grid(column=1, row=5, sticky=E, padx=4)

# поле сгенерированного документа - плательщик
label_payer = Label(text="Имя плательщика", fg="#eee", bg="#333", width=18)
label_payer.grid(column=0, row=6)
txt_payer = Entry(window, width=50)
txt_payer.grid(column=1, row=6)

# поле сгенерированного документа - получатель
label_receiver = Label(text="Имя получателя", fg="#eee", bg="#333", width=18)
label_receiver.grid(column=0, row=7)
txt_receiver = Entry(window, width=50)
txt_receiver.grid(column=1, row=7)

# поле сгенерированного документа - референс
label_ref = Label(text="Референс документа", fg="#eee", bg="#333", width=18)
label_ref.grid(column=0, row=8)
txt_ref = Entry(window, width=50)
txt_ref.grid(column=1, row=8)



# поле сгенерированного документа - номер документа
label_docnum = Label(text="№ док | телефона", fg="#eee", bg="#333", width=18)
label_docnum.grid(column=0, row=9)
txt_docnum = Entry(window, width=24)
txt_docnum.grid(column=1, row=9, sticky=W, padx=4)
# поле номер телефона
txt_phone = Entry(window, width=25)
txt_phone.grid(column=1, row=9, sticky=E, padx=4)
txt_phone.insert(0, "79191234567")

# сколько раз отправить
label_docnum = Label(text="Наполнение от разных плательщиков. Количество документов:", width=50)
label_docnum.grid(column=2, row=13)
spin_sum_request = Spinbox(window, from_=1, to=100, width=5)
spin_sum_request.grid(column=2, row=14)

# кнопка генерация и отправки
btn = tk.Button(
    master=window,
    text="Генерация и отправка исходящих док.",
    command=gen_doc_and_send_request,
    width=32,
    bg="#ffcc00",
)
btn.grid(column=2, row=15)

# лэйбл queryDecision и поле ввода docRef
label_queryDecision = Label(text="\nЗапр. решения, docRef:", width=18)
label_queryDecision.grid(column=0, row=13)
txt_ref2 = Entry(window, width=21)
txt_ref2.grid(column=0, row=14)

# кнопка генерации запроса queryDecision
btn = tk.Button(
    master=window,
    text="queryDecision",
    command=gen_query_result,
    width=18,
    bg="#ffcc00",
)
btn.grid(column=0, row=15, pady=5)

# лэйбл decision и поле ввода docRef
label_decision = Label(text="\nИзменить решение:", width=18)
label_decision.grid(column=1, row=13, sticky="W", padx=4)

# Список кортежей (значение, отображаемый текст)
DECISION_CHOICES = [
    (1, "OK"),
    (2, "FRAUD"),
    (3, "Unknown"),
    (4, "Отозван"),
    (5, "Отказан")
]

# выбор: решение по документу decision
decision_combo = Combobox(window, width=12, state="readonly")
decision_combo['values'] = [text for _, text in DECISION_CHOICES]
decision_combo.current(0)  # установите вариант по умолчанию
decision_combo.grid(column=1, row=14, sticky="W", padx=4)


def get_decision_value():
    selected_text = decision_combo.get()
    # Ищем цифру по тексту
    for value, text in DECISION_CHOICES:
        if text == selected_text:
            return value
    return 1  # значение по умолчанию


# кнопка генерации запроса decision
btn = tk.Button(
    master=window,
    text="decision",
    command=gen_decision,
    width=22,
    bg="#ffcc00",
)
btn.grid(column=1, row=15, sticky="W", padx=4)

# лэйбл checkDocumentRequest и поле ввода docRef
label_checkDocumentRequest = Label(text="\nЗапр. по Цифр. рубль:", width=18)
label_checkDocumentRequest.grid(column=1, row=13, sticky="E", padx=4)

# кнопка генерации запроса checkDocumentRequest
btn = tk.Button(
    master=window,
    text="checkDocumentReq",
    command=gen_checkDocumentRequest,
    width=17,
    bg="#ffcc00",
)
btn.grid(column=1, row=15, sticky="E", padx=4, pady=5)

# кнопка генерации документа
btn_gen = tk.Button(
    master=window,
    text="Генерация документа",
    command=gen_doc,
    width=18,
    bg="#ffcc00",
)
btn_gen.grid(column=0, row=10)

# кнопка отправки
btn_send = tk.Button(
    master=window,
    text="Отправка документа",
    command=send_request,
    width=18,
    bg="#ffcc00",
)
btn_send.grid(column=0, row=11)

# кнопка сохранить изменения
btn = tk.Button(
    master=window,
    text="Сохранить изменения",
    command=save_doc,
    width=18,
    bg="#ffcc00",
)
btn.grid(column=1, row=10, sticky=E)

def analyzeResult(execution_time=None):
    """Подсветка первого тега &lt;result&gt; в ответе"""
    try:
        # Очищаем предыдущую подсветку
        txt_answer.tag_remove("result_highlight", "1.0", tk.END)
        txt_answer.tag_remove("result_value", "1.0", tk.END)

        # Получаем текст ответа
        answer_text = txt_answer.get("1.0", tk.END)

        # Ищем тег &lt;result&gt; с любым содержимым
        import re

        # Паттерн для поиска &lt;result&gt;значение&lt;/result&gt;
        pattern = r'(&lt;result&gt;.*?&lt;/result&gt;)'
        match = re.search(pattern, answer_text, re.DOTALL | re.IGNORECASE)

        # Используем существующий глобальный DECISION_CHOICES
        # Преобразуем в словарь для удобного поиска по значению
        decision_dict = {str(value): text for value, text in DECISION_CHOICES}

        if match:
            start_pos = f"1.0 + {match.start()} chars"
            end_pos = f"1.0 + {match.end()} chars"

            # Подсветка всего тега желтым фоном
            txt_answer.tag_add("result_highlight", start_pos, end_pos)
            txt_answer.tag_config("result_highlight", background="#FFD700", foreground="#000000")

            # Дополнительно выделяем жирным
            txt_answer.tag_config("result_highlight", font=("Arial", 10, "bold"))

            # Извлекаем значение для отображения
            value_match = re.search(r'&lt;result&gt;(.*?)&lt;/result&gt;', match.group(1), re.DOTALL | re.IGNORECASE)
            if value_match:
                result_value = value_match.group(1).strip()

                # Получаем расшифровку только для кодов 1-5
                description = decision_dict.get(result_value, "")

                # Показываем код и расшифровку в статусной строке
                txt_total.configure(state='normal')
                txt_total.delete("1.0", tk.END)
                txt_total.configure(bg="#90EE90")
                txt_total.insert(tk.INSERT, f"Время выполнения: {execution_time:.3f} секунд\n")
                if description:
                    txt_total.insert(tk.INSERT, f"Результат: {result_value} — {description}\n")
                    txt_total.insert(tk.INSERT, "Реф: " + str(txt_ref2.get()))
                else:
                    txt_total.insert(tk.INSERT, f"Результат: {result_value}\n")
                    txt_total.insert(tk.INSERT, "Реф: " + str(txt_ref2.get()))

                txt_total.configure(state='disabled')

                logging.info(f"Найден результат обработки: {result_value}{' — ' + description if description else ''}")
            else:
                txt_total.configure(state='normal')
                txt_total.delete("1.0", tk.END)
                txt_total.configure(bg="#FFD700")
                txt_total.insert(tk.INSERT, "Найден тег &lt;result&gt; (значение не определено)")
                txt_total.configure(state='disabled')

            # Прокручиваем к найденному тегу
            txt_answer.see(start_pos)

            return True
        else:
            txt_total.configure(state='normal')
            txt_total.delete("1.0", tk.END)
            txt_total.configure(bg="#FA8072")
            txt_total.insert(tk.INSERT, "Тег &lt;result&gt; не найден")
            txt_total.configure(state='disabled')
            logging.info("Тег &lt;result&gt; не найден в ответе")
            return False

    except Exception as e:
        txt_total.configure(state='normal')
        txt_total.delete("1.0", tk.END)
        txt_total.configure(bg="#FA8072")
        txt_total.insert(tk.INSERT, f"Ошибка анализа: {str(e)}")
        txt_total.configure(state='disabled')
        logging.error(f"Ошибка при анализе ответа: {str(e)}")
        return False

# открыть запрос в отдельном окне с возможностью редактирования
def open_request_window():
    top = tk.Toplevel()
    top.title("Редактирование запроса")
    top.geometry("900x700")
    top.iconbitmap(os.path.join(cfg_dir, 'ok.ico'))
    top.focus_force()

    def save_changes():
        try:
            # Получаем текст из виджета (сохраняем оригинальное форматирование)
            edited_text = text_in_top.get("1.0", tk.END).strip()

            # Функция для экранирования содержимого между тегами arg0
            def escape_arg0_content(match):
                # match.group(0) - это весь найденный текст от <arg0> до </arg0>
                # match.group(1) - содержимое между тегами
                content = match.group(1)
                # Экранируем специальные символы только в содержимом
                escaped_content = content.replace('&', '&amp;')
                escaped_content = escaped_content.replace('<', '&lt;')
                escaped_content = escaped_content.replace('>', '&gt;')
                # Возвращаем теги + экранированное содержимое + закрывающий тег
                return f'<arg0>{escaped_content}</arg0>'

            # Используем регулярное выражение для поиска содержимого между <arg0> и </arg0>
            import re
            # Шаблон ищет <arg0>, затем захватывает все содержимое (не жадное) до </arg0>
            pattern = r'<arg0>(.*?)</arg0>'
            edited_text = re.sub(pattern, escape_arg0_content, edited_text, flags=re.DOTALL)

            # Очищаем и вставляем отредактированный текст
            txt_request.delete("1.0", tk.END)
            txt_request.insert("1.0", edited_text)

            # Сообщение об успехе
            txt_total.delete("1.0", tk.END)
            txt_total.configure(bg="#90EE90")
            txt_total.insert(tk.INSERT, "Запрос успешно обновлен")

            logging.info("Запрос отредактирован и сохранен через отдельное окно")

            # Закрываем окно
            top.destroy()

        except Exception as e:
            # Сообщение об ошибке
            txt_total.delete("1.0", tk.END)
            txt_total.configure(bg="#FA8072")
            txt_total.insert(tk.INSERT, f"Ошибка сохранения: {str(e)}")
            logging.error(f"Ошибка сохранения отредактированного запроса: {str(e)}")

    # Создаем фрейм для текстового поля
    text_frame = tk.Frame(top)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

    # Создаем текстовое поле (редактируемое)
    text_in_top = scrolledtext.ScrolledText(
        text_frame,
        width=100,
        height=38,
        pady=10,
        padx=10,
        font=("Courier New", 10),
        wrap=tk.NONE,
        tabs=('1c', '2c', '3c', '4c', '5c', '6c', '7c', '8c', '9c', '10c')
    )
    text_in_top.pack(fill=tk.BOTH, expand=True)

    # Добавляем горизонтальный скроллбар
    h_scrollbar = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text_in_top.xview)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    text_in_top.configure(xscrollcommand=h_scrollbar.set)

    # Получаем текст из txt_request - СОХРАНЯЕМ ОРИГИНАЛЬНЫЕ ПЕРЕВОДЫ СТРОК
    xml_content = txt_request.get("1.0", tk.END)

    # Преобразуем сущности в символы для отображения
    xml_content = xml_content.replace('&lt;', '<')
    xml_content = xml_content.replace('&gt;', '>')

    # Вставляем XML КАК ЕСТЬ - с оригинальными переводами строк
    text_in_top.insert(1.0, xml_content)

    # Устанавливаем табуляцию
    text_in_top.config(tabs=('1c', '2c', '3c', '4c', '5c', '6c', '7c', '8c', '9c', '10c'))

    # Делаем текстовое поле редактируемым
    text_in_top.configure(state='normal')

    # Устанавливаем курсор в начало
    text_in_top.mark_set(tk.INSERT, "1.0")
    text_in_top.focus()

    # СОЗДАЕМ ОДИН ОБЩИЙ ФРЕЙМ ДЛЯ ВСЕХ КНОПОК ВНИЗУ
    bottom_frame = tk.Frame(top, bg='#f0f0f0')
    bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10), side=tk.BOTTOM)

    # Фрейм для поиска (слева в общем фрейме)
    search_frame = tk.Frame(bottom_frame)
    search_frame.pack(side=tk.LEFT)

    # Добавляем функционал поиска (он сам создаст свои виджеты внутри search_frame)
    # Нам нужно адаптировать setup_search_for_new_window для работы с переданным frame
    def setup_search_modified(text_widget, parent_frame):
        search_positions_new = []
        current_search_index_new = -1
        search_var_new = tk.StringVar()

        def search_new():
            nonlocal search_positions_new, current_search_index_new
            text = search_var_new.get().strip()
            if not text:
                return

            text_widget.tag_remove("highlight", "1.0", tk.END)
            text_widget.tag_remove("current", "1.0", tk.END)
            search_positions_new.clear()

            pos = "1.0"
            while True:
                pos = text_widget.search(text, pos, stopindex=tk.END, nocase=True)
                if not pos:
                    break
                end = f"{pos}+{len(text)}c"
                search_positions_new.append((pos, end))
                text_widget.tag_add("highlight", pos, end)
                pos = end

            text_widget.tag_config("highlight", background="#FFFACD")
            text_widget.tag_config("current", background="#FFA500")

            if search_positions_new:
                current_search_index_new = 0
                show_current_new()
                count_label_new.config(text=f"{current_search_index_new + 1}/{len(search_positions_new)}")

        def show_current_new():
            if not search_positions_new: return
            text_widget.tag_remove("current", "1.0", tk.END)
            start, end = search_positions_new[current_search_index_new]
            text_widget.tag_add("current", start, end)
            text_widget.see(start)

        def next_new():
            nonlocal current_search_index_new
            if search_positions_new:
                current_search_index_new = (current_search_index_new + 1) % len(search_positions_new)
                show_current_new()
                count_label_new.config(text=f"{current_search_index_new + 1}/{len(search_positions_new)}")
            else:
                search_new()

        def prev_new():
            nonlocal current_search_index_new
            if search_positions_new:
                current_search_index_new = (current_search_index_new - 1) % len(search_positions_new)
                show_current_new()
                count_label_new.config(text=f"{current_search_index_new + 1}/{len(search_positions_new)}")
            else:
                search_new()

        def clear_new():
            text_widget.tag_remove("highlight", "1.0", tk.END)
            text_widget.tag_remove("current", "1.0", tk.END)
            search_var_new.set("")
            search_positions_new.clear()
            count_label_new.config(text="")

        # Все в одну строку
        tk.Label(parent_frame, text="Поиск:").pack(side=tk.LEFT, padx=(0, 2))

        e = tk.Entry(parent_frame, textvariable=search_var_new, width=18)
        e.pack(side=tk.LEFT, padx=(0, 2))

        tk.Button(parent_frame, text="✕", command=clear_new,
                  bg="#8B0000", fg="#eee", width=2).pack(side=tk.LEFT, padx=(1, 2))

        tk.Button(parent_frame, text="Найти", command=search_new,
                  bg="#ffcc00", width=6).pack(side=tk.LEFT, padx=(0, 2))

        tk.Button(parent_frame, text="<", command=prev_new,
                  bg="#ffcc00", fg="black", width=2).pack(side=tk.LEFT, padx=(0, 1))

        tk.Button(parent_frame, text=">", command=next_new,
                  bg="#ffcc00", fg="black", width=2).pack(side=tk.LEFT, padx=(0, 2))

        count_label_new = tk.Label(parent_frame, text="", width=5)
        count_label_new.pack(side=tk.LEFT, padx=(0, 2))

        # Горячие клавиши
        e.bind('<Return>', lambda x: search_new())
        e.bind('<F3>', lambda x: next_new())
        e.bind('<Shift-F3>', lambda x: prev_new())

    # Вызываем модифицированную функцию поиска
    setup_search_modified(text_in_top, search_frame)

    # Фрейм для кнопки сохранения (справа в общем фрейме)
    save_frame = tk.Frame(bottom_frame)
    save_frame.pack(side=tk.RIGHT)

    # Кнопка сохранения в желтом стиле
    btn_save = tk.Button(
        save_frame,
        text="Сохранить изменения",
        command=save_changes,
        width=20,
        bg="#ffcc00",
        fg="black",
        font=("Arial", 10)
    )
    btn_save.pack()

    # Горячие клавиши
    def on_ctrl_s(event):
        save_changes()
        return "break"

    def on_escape(event):
        top.destroy()
        return "break"

    text_in_top.bind('<Control-s>', on_ctrl_s)
    text_in_top.bind('<Control-S>', on_ctrl_s)
    text_in_top.bind('<Escape>', on_escape)

    try:
        top.mainloop()
    except KeyboardInterrupt:
        pass


button = tk.Button(window, text=" Открыть запрос ", command=open_request_window, bg="#ffcc00")
button.grid(column=1, row=20, sticky=W)


def open_answer_window():
    top = tk.Toplevel()
    top.title("Тело ответа (только просмотр)")
    top.iconbitmap(os.path.join(cfg_dir, 'ok.ico'))
    top.focus_force()
    top.grab_set()

    # Создаем фрейм для поиска
    search_frame = tk.Frame(top)
    search_frame.pack(fill=tk.X, padx=8, pady=(8, 5))

    text_in_top = scrolledtext.ScrolledText(top, width=84, height=44, pady=8, padx=8)
    text_in_top.pack(fill=tk.BOTH, expand=True)

    txt_answer_replace = txt_answer.get("1.0", tk.END)
    txt_answer_replace = txt_answer_replace.replace('&lt;', '<')
    txt_answer_replace = txt_answer_replace.replace('&gt;', '>')
    txt_answer_replace = txt_answer_replace.replace('><', '>\n<')
    txt_answer_replace = txt_answer_replace.replace('<criterion>', '\n<criterion>')
    txt_answer_replace = txt_answer_replace.replace('<return>', '<return>\n')
    txt_answer_replace = txt_answer_replace.replace('</return>', '\n</return>')
    text_in_top.insert(1.0, txt_answer_replace)
    text_in_top.configure(state='disabled')

    # Добавляем функционал поиска
    setup_search_for_new_window(text_in_top, top)

    try:
        top.mainloop()
    except KeyboardInterrupt:
        pass


button = tk.Button(window, text=" Открыть ответ ", command=open_answer_window, bg="#ffcc00")
button.grid(column=2, row=20)


# Функция сохранения XML в файл
def save_xml_to_file():
    # Получаем текущий docref из поля txt_ref
    docref = txt_ref.get().strip()
    if not docref:
        # Если поле пустое, используем текущую дату и время
        docref = time.strftime('%Y%m%d_%H%M%S')

    # Предлагаем имя файла по умолчанию
    default_filename = f"docref_{docref}.xml"

    # Открываем диалог сохранения файла
    filepath = asksaveasfilename(
        defaultextension=".xml",
        filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        initialfile=default_filename,
        title="Сохранить XML документ"
    )

    if filepath:
        try:
            # Получаем содержимое из txt_request
            txt_request_replace = txt_request.get("1.0", tk.END)
            txt_request_replace = txt_request_replace.replace('&lt;', '<')
            txt_request_replace = txt_request_replace.replace('&gt;', '>')
            txt_request_replace = txt_request_replace.replace('<arg0>', '<arg0>\n\n')
            txt_request_replace = txt_request_replace.replace('</arg0>', '\n\n</arg0>')

            # Сохраняем в файл
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(txt_request_replace)

            # Показываем сообщение об успехе
            txt_total.delete("1.0", tk.END)
            txt_total.configure(bg="#90EE90")
            txt_total.insert(tk.INSERT, f"XML сохранен в: {filepath}")

            logging.info(f"XML документ сохранен в файл: {filepath}")

        except Exception as e:
            txt_total.delete("1.0", tk.END)
            txt_total.configure(bg="#FA8072")
            txt_total.insert(tk.INSERT, f"Ошибка сохранения: {str(e)}")
            logging.error(f"Ошибка сохранения XML: {str(e)}")


# КНОПКА: Сохранить в файл
btn_save_file = tk.Button(
    master=window,
    text="Сохранить в файл",
    command=save_xml_to_file,
    width=16,
    bg="#ffcc00",  # Зеленый цвет для кнопки сохранения
    fg="black"
)
btn_save_file.grid(column=0, row=20, pady=5)

# тело запроса
label_docnum = Label(text="Запрос (редактируемый) :", font=("Arial", 12))
label_docnum.grid(column=1, row=17, sticky=W)
txt_request = scrolledtext.ScrolledText(window, width=52, height=14)
txt_request.grid(column=0, row=19, sticky=W, columnspan=2, padx=10, pady=10)

# Вызов функции настройки поиска
setup_search_for_txt_request()

# ответ запроса
label_docnum = Label(text="Ответ:", font=("Arial", 12))
label_docnum.grid(column=2, row=18)
txt_answer = scrolledtext.ScrolledText(window, width=54, height=14)
txt_answer.grid(column=2, row=19, padx=10, pady=10)

# Общий результат
label_docnum = Label(text="\nОбщий результат:", font=("Arial", 12))
label_docnum.grid(column=2, row=16)
txt_total = scrolledtext.ScrolledText(window, width=54, height=1)
txt_total.grid(column=2, row=17, padx=10, pady=10)


# Очистка истории
def clear_history():
    txt_history.configure(state="normal")
    txt_history.delete("1.0", tk.END)


# История
label_history = Label(text="История:", font=("Arial", 12))
label_history.grid(column=3, row=18)
txt_history = scrolledtext.ScrolledText(window, width=27, height=14)
txt_history.tag_config('nosbp', foreground='#691900', background='#eee8aa', font=("Arial", 10, "bold"))
txt_history.tag_config('sbp', foreground='#eee8aa', background='#691900', font=("Arial", 10, "bold"))
txt_history.tag_config('dc', foreground='#fff', background='#00599C', font=("Arial", 10, "bold"))
txt_history.tag_config('query', background='#ebebeb')
txt_history.configure(state="disabled")
txt_history.grid(column=3, row=19, padx=10, pady=10)
button = tk.Button(window, text=" Очистить ", command=clear_history, fg="#eee", bg="#8B0000")
button.grid(column=3, row=20)

# ИНФО

label_info1 = Label(text="ИНФО:")
label_info1.grid(column=2, row=2)

label_info2 = Label(text="◎ Не подходит для нагрузок")
label_info2.grid(column=2, row=3, sticky="W", padx=30)

label_info3 = Label(text="◎ Если не работает CTRL+V (CTRL+C) - переключить клавиатуру на ENG")
label_info3.grid(column=2, row=4, sticky="W", padx=30)

label_info4 = Label(text="◎ Шаблон документа и запроса можно редактировать в /cfg/Template_*.xml")
label_info4.grid(column=2, row=5, sticky="W", padx=30)

label_info6 = Label(text="◎ URL GlassFish: host:port/fa/wssocket")
label_info6.grid(column=2, row=6, sticky="W", padx=30)

label_info7 = Label(text="◎ URL TomEE: host:port/wssocket/webservices/fa/wssocket")
label_info7.grid(column=2, row=7, sticky="W", padx=30)

label_info8 = Label(text="◎ По вопросам di.barbashin@gmail.com")
label_info8.grid(column=2, row=8, sticky="W", padx=30)

# ПОДСКАЗКИ ПО КНОПКАМ
label_info1 = Label(text="❮--- 1. Создание документа")
label_info1.grid(column=1, row=10, sticky="W")

label_info2 = Label(text="❮--- 2. Отправка документа")
label_info2.grid(column=1, row=11, sticky="W")

"""
def check_host_availability():

    host_url = "http://kc-13-133.bss.lan:8500/"

    try:
        response = requests.get(host_url, timeout=5)

        if response.status_code == 200:
            # Хост доступен - разблокируем кнопки
            btn_gen.config(state="normal")
            btn_send.config(state="normal")
            btn.config(state="normal")  # кнопка "Сохранить изменения"

            # Убираем сообщение, если было
            txt_total.delete("1.0", tk.END)
            txt_total.configure(bg="#FFFFFF")  # белый фон

            return True

        else:
            # Хост недоступен - блокируем кнопки
            btn_gen.config(state="disabled")
            btn_send.config(state="disabled")
            btn.config(state="disabled")  # кнопка "Сохранить изменения"

            # Показываем сообщение
            txt_total.delete("1.0", tk.END)
            txt_total.configure(bg="#FA8072")  # красный фон
            txt_total.insert(tk.INSERT, f"ОШИБКА: Запуск не из сети организации!\n"
                                        f"Доступные функции ограничены.")

            return False

    except requests.exceptions.RequestException as e:
        # Ошибка соединения
        btn_gen.config(state="disabled")
        btn_send.config(state="disabled")
        btn.config(state="disabled")

        txt_total.delete("1.0", tk.END)
        txt_total.configure(bg="#FA8072")
        txt_total.insert(tk.INSERT, f"ОШИБКА: Запуск не из сети организации!\n"
                                    f"Доступные функции ограничены.")
        return False

check_host_availability()

# Создаем периодическую проверку каждые 30 секунд
def periodic_host_check():
    check_host_availability()
    # Планируем следующую проверку через 30 секунд
    window.after(60000, periodic_host_check)

# Запускаем периодическую проверку
window.after(60000, periodic_host_check)
"""

def check_expiry_date():
    expiry_date = datetime.datetime(2026, 10, 30, 23, 59, 59)  # datetime.datetime
    if datetime.datetime.now() > expiry_date:
        print("=" * 50)
        print("error")
        sys.exit(1)
    return True

check_expiry_date()

window.mainloop()