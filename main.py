from tkinter import *
from tkinter.ttk import Combobox
from tkinter import scrolledtext
import tkinter as tk

import random
import string
import datetime
import time
import logging

import requests
from jinja2 import Template
from russian_names import RussianNames

APP_VERSION = 1.2

# -------------------- GUI --------------------
window = Tk()
window.title("Tester Fraud-Analyze")
window.geometry('1196x810')
window.iconbitmap(r'.\cfg\ok.ico')

fixPayer = 0

# -------------------- Logging --------------------
logging.basicConfig(
    filename=r".\log\LOG___" + str(time.strftime('%Y-%m-%d___%H-%M-%S')) + ".log",
    filemode="w",
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='[%Y-%m-%d] %H:%M:%S'
)
logging.info("Запуск программы тестирования")

# -------------------- Helpers --------------------
def read_text(path: str, *, encoding: str | None = None) -> str:
    with open(path, "r", encoding=encoding) as f:
        return f.read()

def soap_envelope(arg0_xml: str) -> str:
    return (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<S:Envelope xmlns:S=\"http://schemas.xmlsoap.org/soap/envelope/\">\n"
        "<S:Body><ns2:process xmlns:ns2=\"http://ws.socket.fraud.bssys.com/\"><arg0>"
        + arg0_xml +
        "</arg0></ns2:process></S:Body></S:Envelope>"
    )

def format_time() -> str:
    t = datetime.datetime.now()
    s = t.strftime('%Y-%m-%d' + 'T' + '%H:%M:%S.%f')
    return s[:-3] + '+03:00'

_ALPHANUM = string.ascii_letters + string.digits

def random_char(n: int) -> str:
    return ''.join(random.choice(_ALPHANUM) for _ in range(n))

def random_acc() -> int:
    return random.randrange(100000000000, 999999999999, 1)

def random_char_min() -> int:
    return random.randrange(1, 9999, 1)

# Одна сессия на всё приложение (быстрее/меньше накладных расходов)
session = requests.Session()
session.headers.update({"Content-Type": "application/soap+xml; charset=utf-8"})

# Один генератор имён (меньше объектов)
rn = RussianNames()

def post_soap(endpoint: str, xml_text: str, *, timeout: int | None = None):
    """Отправка SOAP. Возвращает response или None (если ошибка)."""
    body = xml_text.encode('utf-8')
    # Content-Length зависит от тела — обновляем каждый раз
    session.headers.update({"Content-Length": str(len(body))})
    try:
        return session.post(url=endpoint, data=body, verify=False, timeout=timeout)
    except requests.exceptions.Timeout:
        return "Timeout"
    except requests.exceptions.TooManyRedirects:
        return "TooManyRedirects"
    except requests.exceptions.RequestException:
        return "RequestException"

def _set_total_error(msg: str, endpoint: str):
    txt_total.insert(tk.INSERT, f'Ошибка: {msg}')
    txt_total.configure(bg="#FA8072")
    logging.info(f"{endpoint} ---> Ошибка: {msg}")

def _set_total_ok():
    txt_total.configure(bg="#90EE90")

def _render_to_request(widget: scrolledtext.ScrolledText, text: str):
    widget.delete("1.0", tk.END)
    widget.insert(tk.INSERT, text)

def _reset_answer_total():
    txt_answer.configure(state='normal')
    txt_answer.delete("1.0", tk.END)
    txt_total.delete("1.0", tk.END)

def _safe_show_response(resp, start_time: float):
    """Пишем ответ/время, даже если запроса не было из-за ошибки."""
    if isinstance(resp, requests.Response):
        response_decode = resp.content.decode('utf-8', errors='replace')
        txt_answer.insert(tk.INSERT, response_decode)
        txt_answer.configure(state='disabled')
    else:
        # Если была ошибка или None — оставим ответ пустым, как при сбое
        txt_answer.insert(tk.INSERT, "")
        txt_answer.configure(state='disabled')

    txt_total.insert(tk.INSERT, 'Время выполнения: ')
    txt_total.insert(tk.INSERT, (time.time() - start_time))
    txt_total.insert(tk.INSERT, ' секунд')


# -------------------- Config / Templates --------------------
# URL из конфига
url_cfg = read_text(r".\cfg\url.cfg", encoding='utf-8')
logging.info("Читаем url.cfg")

# Шаблоны
Template_decision = read_text(r".\cfg\Template_decision.xml", encoding='utf-8')
logging.info("Читаем Template_decision.xml")
decision = soap_envelope(Template_decision)

Template_queryDecision = read_text(r".\cfg\Template_queryDecision.xml", encoding='utf-8')
logging.info("Читаем Template_queryDecision.xml")
query_result = soap_envelope(Template_queryDecision)

Template_PaymentDocument = read_text(r".\cfg\Template_PaymentDocument.xml", encoding='utf-8')
logging.info("Читаем Template_PaymentDocument.xml")
list_bucket_result = soap_envelope(Template_PaymentDocument)

Template_incomingDocument = read_text(r".\cfg\Template_incomingDocument.xml", encoding='utf-8')
logging.info("Читаем Template_incomingDocument.xml")
incomingDocument = soap_envelope(Template_incomingDocument)

Template_checkDocumentRequest = read_text(r".\cfg\Template_DC_checkDocumentRequest.xml", encoding='utf-8')
logging.info("Читаем Template_checkDocumentRequest.xml")
checkDocumentRequest = soap_envelope(Template_checkDocumentRequest)


# -------------------- Actions --------------------
def save_url():
    with open(r".\cfg\url.cfg", "w") as file:
        file.write(txt_url.get())
    logging.info("URL изменён")

def gen_doc_and_send_request():
    txt_answer.configure(state='normal')
    txt_answer.delete("1.0", tk.END)
    txt_total.delete("1.0", tk.END)

    x = int(spin_sum_request.get())
    start_time = time.time()

    endpoint = txt_url.get()
    last_response = None

    # шаблон компилируем один раз
    template = Template(list_bucket_result)

    for it in range(1, x + 1):
        result = template.render(
            phys_or_jur=phys_or_jur.get(),
            time=format_time(),
            payerId=random_char_min(),
            documentNumber=random_char_min(),
            amount=random_char_min(),
            documentType=documentType.get(),
            payerName=rn.get_person(),
            receiverName=rn.get_person(),
            payerAccount='40704810' + str(random_acc()),
            receiverAccount='40899810' + str(random_acc()),
            paymentSBP=sbp_or_no.get(),
            docRef=random_char(40),
        )

        logging.info("Пробуем отправить документ")
        resp = post_soap(endpoint, result, timeout=30)

        if isinstance(resp, requests.Response):
            last_response = resp
            _set_total_ok()
            logging.info("Документ успешно отправлен")
            logging.debug("========== Тело документа ==========\n" + str(result.encode('utf-8')))
            txt_history.configure(state="normal")
            txt_history.insert(END, "Наполнение, итерация: " + str(it) + "\n")
            txt_history.configure(state="disabled")
        else:
            # resp содержит строку ошибки или None
            err = resp if isinstance(resp, str) else "RequestException"
            txt_total.delete("1.0", tk.END)
            _set_total_error(err, endpoint)

    # Показ последнего ответа (как у вас по факту было)
    if isinstance(last_response, requests.Response):
        response_decode = last_response.content.decode('utf-8', errors='replace')
        txt_answer.insert(tk.INSERT, response_decode)
    txt_answer.configure(state='disabled')

    # Итог по времени (формат оставлен как у вас)
    txt_total.delete("1.0", tk.END)
    elapsed = time.time() - start_time
    avg = (elapsed / x) if x else 0
    txt_total.insert(
        tk.INSERT,
        'Время выполнения: ' + str(elapsed)[:4] + ' секунд\nСреднее время: ~ ' + str(avg)[:7] + ' секунд'
    )


# чекбокс фиксации id плательщика
checkbuttonFixPayer = BooleanVar()
enabled_checkbutton = Checkbutton(text="ФИКС Плательщика", variable=checkbuttonFixPayer)
enabled_checkbutton.grid(column=1, row=4, sticky="E", padx=2)

def gen_doc():
    global fixPayer

    txt_request.delete("1.0", tk.END)
    txt_answer.configure(state='normal')
    txt_answer.delete("1.0", tk.END)
    txt_total.delete("1.0", tk.END)

    txt_receiver.delete("0", tk.END)
    txt_ref.delete("0", tk.END)

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
        txt_payer.insert(tk.INSERT, rn.get_person())
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

    if sbp_or_no.get() == ("НЕТ"):
        fps_type['values'] = ("NULL", "SBPQR", "B2B")
    else:
        fps_type['values'] = ("C2C", "SBPQR", "B2C", "B2B")
        documentType.current(0)

    txt_receiver.insert(tk.INSERT, rn.get_person())
    txt_ref.insert(tk.INSERT, random_char(40))

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
            receiverAccount='40899810' + str(random_acc()),
            paymentSBP=sbp_or_no.get(),
            docRef=txt_ref.get(),
        )
        txt_request.insert(tk.INSERT, result)
        txt_answer.insert(
            tk.INSERT,
            "Сгенерирован новый ИСХОДЯЩИЙ документ, нажмите кнопку\n<Отправка документа>\n\n"
            "Если требуется изменить реквизиты документа - отредактировать значения в полях"
            " и нажать:\n<Сохранить изменения>, далее для отправки - <Отправка документа>"
        )
        logging.info("Сгенерирован новый ИСХОДЯЩИЙ документ № " + str(txt_docnum.get()) + ", референс " + str(txt_ref.get()))
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
            receiverAccount='40899810' + str(random_acc()),
            docRef=txt_ref.get(),
        )
        txt_request.insert(tk.INSERT, result)
        txt_answer.insert(
            tk.INSERT,
            "Сгенерирован новый ВХОДЯЩИЙ документ, нажмите кнопку\n<Отправка документа>\n\n"
            "Если требуется изменить реквизиты документа - отредактировать значения в полях"
            " и нажать:\n<Сохранить изменения>, далее для отправки - <Отправка документа>"
        )
        logging.info("Сгенерирован новый ВХОДЯЩИЙ документ № " + str(txt_docnum.get()) + ", референс " + str(txt_ref.get()))

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
            payerAccount='40704810' + str(random_acc()),
            receiverAccount='40899810' + str(random_acc()),
            paymentSBP=sbp_or_no.get(),
            docRef=txt_ref.get(),
        )
        txt_request.insert(tk.INSERT, result)
        txt_answer.insert(tk.INSERT, "Изменённый ИСХОДЯЩИЙ документ сохранён, нажмите кнопку\n<Отправка документа>")
        logging.info("Сохранён изменённый ИСХОДЯЩИЙ документ <" + str(out_or_in.get()) + "> № " + str(txt_docnum.get()) + ", референс " + str(txt_ref.get()))
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
            payerAccount='40704810' + str(random_acc()),
            receiverAccount='40899810' + str(random_acc()),
            docRef=txt_ref.get(),
        )
        txt_request.insert(tk.INSERT, result)
        txt_answer.insert(tk.INSERT, "Изменённый ВХОДЯЩИЙ документ сохранён, нажмите кнопку:\n<Отправка документа>")
        logging.info("Сохранён изменённый ВХОДЯЩИЙ документ <" + str(out_or_in.get()) + "> № " + str(txt_docnum.get()) + ", референс " + str(txt_ref.get()))

def send_request():
    global response

    _reset_answer_total()
    start_time = time.time()

    endpoint = txt_url.get()
    body_text = txt_request.get("1.0", tk.END)

    logging.info("Пробуем отправить документ, референс " + str(txt_ref.get()))
    resp = post_soap(endpoint, body_text, timeout=30)

    if isinstance(resp, requests.Response):
        response = resp
        logging.info("Успешно отправлен документ <" + str(out_or_in.get()) + "> № " + str(txt_docnum.get()) + ", референс " + str(txt_ref.get()))
        logging.debug("========== Тело документа ==========\n" + str(body_text.encode('utf-8')))

        _set_total_ok()

        txt_history.configure(state="normal")
        if ((sbp_or_no.get() == "1") or (sbp_or_no.get() == "2")) and documentType.get() == "PDR":
            txt_history.insert("1.0", "id " + txt_idpayer.get() + " | N " + txt_docnum.get() + " | СБП " + sbp_or_no.get() + " итерация\n", "sbp")
        elif (sbp_or_no.get() == "НЕТ") and (documentType.get() == "PDR") and out_or_in.get() == "paymentDocument":
            txt_history.insert("1.0", "> Исх: id " + txt_idpayer.get() + " | N " + txt_docnum.get() + " | СБП " + sbp_or_no.get() + "\n", "nosbp")
        elif (sbp_or_no.get() == "НЕТ") and (documentType.get() == "PDR") and out_or_in.get() == "incomingDocument":
            txt_history.insert("1.0", "< Вх: id " + txt_idpayer.get() + " | N " + txt_docnum.get() + " | Вх СБП " + "\n", "nosbp")
        else:
            txt_history.insert("1.0", "id " + txt_idpayer.get() + " | N " + txt_docnum.get() + " | Цифр. рубль" + "\n", "dc")
        txt_history.configure(state="disabled")

        txt_ref2.delete(0, END); txt_ref2.insert(END, txt_ref.get())
        txt_ref3.delete(0, END); txt_ref3.insert(END, txt_ref.get())
        txt_ref4.delete(0, END); txt_ref4.insert(END, txt_ref.get())
    else:
        err = resp if isinstance(resp, str) else "RequestException"
        _set_total_error(err, endpoint)

    _safe_show_response(resp if isinstance(resp, requests.Response) else None, start_time)

def gen_query_result():
    txt_request.delete("1.0", tk.END)
    _reset_answer_total()

    template = Template(query_result)
    result = template.render(docRef=txt_ref2.get())
    txt_request.insert(tk.INSERT, result)

    start_time = time.time()
    endpoint = txt_url.get()
    logging.info("Пробуем отправить запрос <queryDecision> к референсу " + str(txt_ref2.get()))

    resp = post_soap(endpoint, result, timeout=30)
    if isinstance(resp, requests.Response):
        _set_total_ok()
        logging.info("Запрос <queryDecision> успешно отправлен к референсу " + str(txt_ref2.get()))
        logging.debug("========== Тело запроса ==========\n" + str(result.encode('utf-8')))
        txt_history.configure(state="normal")
        txt_history.insert("1.0", "[queryDecision] реф:\n" + str(txt_ref2.get()) + "\n", "query")
        txt_history.configure(state="disabled")
    else:
        err = resp if isinstance(resp, str) else "RequestException"
        _set_total_error(err, endpoint)

    _safe_show_response(resp if isinstance(resp, requests.Response) else None, start_time)

def gen_decision():
    txt_request.delete("1.0", tk.END)
    _reset_answer_total()

    template = Template(decision)
    result = template.render(
        docRef=txt_ref3.get(),
        decision=decision_combo.get(),
        time=format_time(),
    )
    txt_request.insert(tk.INSERT, result)

    start_time = time.time()
    endpoint = txt_url.get()
    logging.info("Пробуем отправить запрос <decision> к референсу " + str(txt_ref3.get()))

    resp = post_soap(endpoint, result, timeout=30)
    if isinstance(resp, requests.Response):
        _set_total_ok()
        logging.info("Запрос <decision> успешно отправлен к референсу " + str(txt_ref3.get()))
        logging.debug("========== Тело запроса ==========\n" + str(result.encode('utf-8')))
        txt_history.configure(state="normal")
        txt_history.insert("1.0", "[decision] реф:\n" + str(txt_ref3.get()) + "\n", "query")
        txt_history.configure(state="disabled")
    else:
        err = resp if isinstance(resp, str) else "RequestException"
        _set_total_error(err, endpoint)

    _safe_show_response(resp if isinstance(resp, requests.Response) else None, start_time)

def gen_checkDocumentRequest():
    txt_request.delete("1.0", tk.END)
    _reset_answer_total()

    template = Template(checkDocumentRequest)
    result = template.render(
        docRef=txt_ref4.get(),
        time=format_time(),
    )
    txt_request.insert(tk.INSERT, result)

    start_time = time.time()
    endpoint = txt_url.get()
    logging.info("Пробуем отправить запрос <checkDocumentRequest> к референсу " + str(txt_ref3.get()))

    resp = post_soap(endpoint, result, timeout=30)
    if isinstance(resp, requests.Response):
        _set_total_ok()
        logging.info("Запрос <checkDocumentRequest> успешно отправлен к референсу " + str(txt_ref3.get()))
        logging.debug("========== Тело запроса ==========\n" + str(result.encode('utf-8')))
        txt_history.configure(state="normal")
        txt_history.insert("1.0", "[checkDocumentRequest] реф:\n" + str(txt_ref3.get()) + "\n", "query")
        txt_history.configure(state="disabled")
    else:
        err = resp if isinstance(resp, str) else "RequestException"
        _set_total_error(err, endpoint)

    _safe_show_response(resp if isinstance(resp, requests.Response) else None, start_time)


# -------------------- Widgets (UI unchanged) --------------------
btn_save_url = tk.Button(master=window, text="Сохранить URL ->", command=save_url, width=18, bg="#ffcc00")
btn_save_url.grid(column=0, row=0)

txt_url = Entry(window, width=50)
txt_url.grid(column=1, row=0)
txt_url.insert(tk.INSERT, url_cfg)

version = Label(text="v " + str(APP_VERSION), fg="#868686")
version.grid(column=3, row=0, sticky="E", padx=14)

label_out_or_in = Label(text="ИСХ / ВХ / ЦР (DC)", fg="#eee", bg="#333", width=18)
label_out_or_in.grid(column=0, row=1)
out_or_in = Combobox(window, width=22, state="readonly")
out_or_in['values'] = ("paymentDocument", "incomingDocument")
out_or_in.current(0)
out_or_in.grid(column=1, row=1, sticky="W", padx=4)

documentType = Combobox(window, width=21, state="readonly")
documentType['values'] = ("PDR", "DCTransfer", "DCWithdrawal", "DCRefill", "DCSelfExectTransactionCreat")
documentType.current(0)
documentType.grid(column=1, row=1, sticky="E", padx=4)

label_sbp_or_no = Label(text="СБП или нет", fg="#eee", bg="#8B0000", width=18)
label_sbp_or_no.grid(column=0, row=2)
sbp_or_no = Combobox(window, width=22, state="readonly")
sbp_or_no['values'] = ("НЕТ", 1, 2)
sbp_or_no.current(0)
sbp_or_no.grid(column=1, row=2, sticky="W", padx=4)

fps_type = Combobox(window, width=21, state="readonly")
fps_type['values'] = ("NULL", "C2C", "SBPQR", "B2C", "B2B")
fps_type.current(0)
fps_type.grid(column=1, row=2, sticky="E", padx=4)

label_phys_or_jur = Label(text="ФЛ или ЮЛ", fg="#eee", bg="#333", width=18)
label_phys_or_jur.grid(column=0, row=3)
phys_or_jur = Combobox(window, width=47, state="readonly")
phys_or_jur['values'] = ("PHYSICAL", "JURIDICAL")
phys_or_jur.current(0)
phys_or_jur.grid(column=1, row=3)

label_idpayer = Label(text="id плательщика", fg="#eee", bg="#333", width=18)
label_idpayer.grid(column=0, row=4)
txt_idpayer = Entry(window, width=22)
txt_idpayer.grid(column=1, row=4, sticky="W", padx=4)

label_payer = Label(text="Счёт плательщика", fg="#eee", bg="#333", width=18)
label_payer.grid(column=0, row=5)
txt_payerAccount = Entry(window, width=50)
txt_payerAccount.grid(column=1, row=5)

label_payer = Label(text="Имя плательщика", fg="#eee", bg="#333", width=18)
label_payer.grid(column=0, row=6)
txt_payer = Entry(window, width=50)
txt_payer.grid(column=1, row=6)

label_receiver = Label(text="Имя получателя", fg="#eee", bg="#333", width=18)
label_receiver.grid(column=0, row=7)
txt_receiver = Entry(window, width=50)
txt_receiver.grid(column=1, row=7)

label_ref = Label(text="Референс документа", fg="#eee", bg="#333", width=18)
label_ref.grid(column=0, row=8)
txt_ref = Entry(window, width=50)
txt_ref.grid(column=1, row=8)

label_docnum = Label(text="Номер документа", fg="#eee", bg="#333", width=18)
label_docnum.grid(column=0, row=9)
txt_docnum = Entry(window, width=50)
txt_docnum.grid(column=1, row=9)

label_docnum = Label(text="Наполнение от разных плательщиков. Количество документов:", width=50)
label_docnum.grid(column=2, row=13)
spin_sum_request = Spinbox(window, from_=1, to=100, width=5)
spin_sum_request.grid(column=2, row=14)

btn = tk.Button(master=window, text="Генерация и отправка исходящих док.", command=gen_doc_and_send_request, width=32, bg="#ffcc00")
btn.grid(column=2, row=15)

label_queryDecision = Label(text="\nЗапр. решения, docRef:", width=18)
label_queryDecision.grid(column=0, row=13)
txt_ref2 = Entry(window, width=21)
txt_ref2.grid(column=0, row=14)

btn = tk.Button(master=window, text="queryDecision", command=gen_query_result, width=18, bg="#ffcc00")
btn.grid(column=0, row=15, pady=5)

label_decision = Label(text="\nИзм. решение, docRef:", width=18)
label_decision.grid(column=1, row=13, sticky="W", padx=4)
txt_ref3 = Entry(window, width=20)
txt_ref3.grid(column=1, row=14, sticky="W", padx=46)

decision_combo = Combobox(window, width=3, state="readonly")
decision_combo['values'] = (1, 2, 3, 4, 5)
decision_combo.current(0)
decision_combo.grid(column=1, row=14, sticky="W", padx=4)

btn = tk.Button(master=window, text="decision", command=gen_decision, width=22, bg="#ffcc00")
btn.grid(column=1, row=15, sticky="W", padx=4)

label_decision_info = Label(text="[1]ок [2]fraud [3]unknown\n[4]отозван [5]отказан", width=24)
label_decision_info.grid(column=1, row=16, sticky="W", padx=4)

label_checkDocumentRequest = Label(text="\nЗапр. по Цифр. рубль:", width=18)
label_checkDocumentRequest.grid(column=1, row=13, sticky="E", padx=4)
txt_ref4 = Entry(window, width=21)
txt_ref4.grid(column=1, row=14, sticky="E", padx=4)

btn = tk.Button(master=window, text="checkDocumentReq", command=gen_checkDocumentRequest, width=17, bg="#ffcc00")
btn.grid(column=1, row=15, sticky="E", padx=4, pady=5)

btn_gen = tk.Button(master=window, text="Генерация документа", command=gen_doc, width=18, bg="#ffcc00")
btn_gen.grid(column=0, row=10)

btn_send = tk.Button(master=window, text="Отправка документа", command=send_request, width=18, bg="#ffcc00")
btn_send.grid(column=0, row=11)

btn = tk.Button(master=window, text="Сохранить изменения", command=save_doc, width=18, bg="#ffcc00")
btn.grid(column=0, row=12)

def open_request_window():
    top = tk.Toplevel()
    top.title("Тело запроса (только просмотр)")
    top.iconbitmap(r'.\cfg\ok.ico')
    top.focus_force()
    top.grab_set()
    text_in_top = scrolledtext.ScrolledText(top, width=84, height=44, pady=8, padx=8)
    txt_request_replace = txt_request.get("1.0", tk.END)
    txt_request_replace = txt_request_replace.replace('&lt;', '<').replace('&gt;', '>')
    txt_request_replace = txt_request_replace.replace('<arg0>', '<arg0>\n\n').replace('</arg0>', '\n\n</arg0>')
    text_in_top.insert(1.0, txt_request_replace)
    text_in_top.configure(state='disabled')
    text_in_top.grid(column=0, row=0)
    try:
        top.mainloop()
    except KeyboardInterrupt:
        pass

button = tk.Button(window, text=" Открыть запрос ", command=open_request_window, bg="#ffcc00")
button.grid(column=1, row=20, sticky=W)

def open_answer_window():
    top = tk.Toplevel()
    top.title("Тело ответа (только просмотр)")
    top.iconbitmap(r'.\cfg\ok.ico')
    top.focus_force()
    top.grab_set()
    text_in_top = scrolledtext.ScrolledText(top, width=84, height=44, pady=8, padx=8)
    txt_answer_replace = txt_answer.get("1.0", tk.END)
    txt_answer_replace = txt_answer_replace.replace('&lt;', '<').replace('&gt;', '>')
    txt_answer_replace = txt_answer_replace.replace('><', '>\n<')
    txt_answer_replace = txt_answer_replace.replace('<criterion>', '\n<criterion>')
    txt_answer_replace = txt_answer_replace.replace('<return>', '<return>\n').replace('</return>', '\n</return>')
    text_in_top.insert(1.0, txt_answer_replace)
    text_in_top.configure(state='disabled')
    text_in_top.grid(column=0, row=0)
    try:
        top.mainloop()
    except KeyboardInterrupt:
        pass

button = tk.Button(window, text=" Открыть ответ ", command=open_answer_window, bg="#ffcc00")
button.grid(column=2, row=20)

label_docnum = Label(text="Запрос (редактируемый) :", font=("Arial", 12))
label_docnum.grid(column=1, row=18, sticky=W)
txt_request = scrolledtext.ScrolledText(window, width=52, height=14)
txt_request.grid(column=0, row=19, sticky=W, columnspan=2, padx=10, pady=10)

label_docnum = Label(text="Ответ:", font=("Arial", 12))
label_docnum.grid(column=2, row=18)
txt_answer = scrolledtext.ScrolledText(window, width=54, height=14)
txt_answer.grid(column=2, row=19, padx=10, pady=10)

label_docnum = Label(text="\nОбщий результат:", font=("Arial", 12))
label_docnum.grid(column=2, row=16)
txt_total = scrolledtext.ScrolledText(window, width=54, height=1)
txt_total.grid(column=2, row=17, padx=10, pady=10)

def clear_history():
    txt_history.configure(state="normal")
    txt_history.delete("1.0", tk.END)

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

label_info1 = Label(text="ИНФОРМАЦИЯ:")
label_info1.grid(column=2, row=2)
label_info2 = Label(text="◎ Не подходит для нагрузок")
label_info2.grid(column=2, row=3, sticky="W", padx=30)
label_info3 = Label(text="◎ Если не работает CTRL+V (CTRL+C) - переключить клавиатуру на ENG")
label_info3.grid(column=2, row=4, sticky="W", padx=30)
label_info4 = Label(text="◎ Шаблон документа и запроса можно редактировать в /cfg/Template_*.xml")
label_info4.grid(column=2, row=5, sticky="W", padx=30)
label_info5 = Label(text="◎ Логирование: /cfg/log")
label_info5.grid(column=2, row=6, sticky="W", padx=30)
label_info6 = Label(text="◎ URL GlassFish: host:port/fa/wssocket")
label_info6.grid(column=2, row=7, sticky="W", padx=30)
label_info7 = Label(text="◎ URL TomEE: host:port/wssocket/webservices/fa/wssocket")
label_info7.grid(column=2, row=8, sticky="W", padx=30)
label_info8 = Label(text="◎ По вопросам di.barbashin@gmail.com")
label_info8.grid(column=2, row=9, sticky="W", padx=30)

label_info1 = Label(text="❮--- 1. Создание документа")
label_info1.grid(column=1, row=10, sticky="W")
label_info2 = Label(text="❮--- 2. Отправка документа")
label_info2.grid(column=1, row=11, sticky="W")
label_info3 = Label(text="❮--- 3. После редактирования, для отправки п.2")
label_info3.grid(column=1, row=12, sticky="W")

window.mainloop()
