import re
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



# FILE PER TUTTE LE FUNZIONI DI SCRAPING:

# COSTANTI:
APPELLI_DIEF_COD = "10005"
COURSE_CATALOG_DIEF_COD = "6: 120"
TITLE_AULE_PAGINA_2 = "a[title='Aula P1.5 (Fa-1e), Aula P1.6 (Fa-1f), Aula P2.1 (Fa-2a), Aula P2.2 (Fa-2b), Aula P2.3 (Fa-2c), Aula P2.4 (Fa-2d), Aula P2.7 (Fa-2g)']"
TITLE_AULE_PAGINA_3 = "a[title='Lab. P0.1 (FA-0A), Lab. P2.5 (FA-2E), Laboratorio P2.6 (FA-2F Linfa)']"


# FUNZIONI:
def initializeDriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

def cleanFacolta(corsi_studio_ingegneria):
    real_courses = {}
    for c in corsi_studio_ingegneria:
        cod = getFacultyCod(c)
        if cod == '20-218' or cod == '20-268' or cod == '20-200' or cod == '20-204' or cod == '20-261' or cod == '20-202' or cod == '20-265' or cod == '20-206' or cod == '20-267' or cod == '20-203' or cod == '20-201' or cod == '20-215' or cod == '20-205' or cod == '20-266':
            continue
        else:
            real_courses[c] = corsi_studio_ingegneria.get(c)

    return real_courses


def getFacoltafromAppelli():
    corsi_studio_ingegneria = {}  # dizionario con Facoltà e durata
    url = "https://www.esse3.unimore.it/Guide/PaginaListaAppelli.do"
    driver = initializeDriver()
    driver.get(url)
    wait_time = WebDriverWait(driver, 5)
    accept_cookie_button = wait_time.until(EC.element_to_be_clickable((By.ID, "c-p-bn")))
    accept_cookie_button.click()
    dipartimento = Select(wait_time.until(EC.presence_of_element_located((By.ID, "FAC_ID"))))
    dipartimento.select_by_value(APPELLI_DIEF_COD)
    corsi = Select(wait_time.until(EC.presence_of_element_located((By.ID, "CDS_ID"))))
    options = corsi.options
    options.pop(0)

    for option in options:
        cod = option.text[4:7]
        durata_corsi = 3
        if int(cod) >= 250:
            durata_corsi = 2
        corsi_studio_ingegneria[option.text] = durata_corsi

    driver.quit()
    corsi_studio_ingegneria = cleanFacolta(corsi_studio_ingegneria)
    return corsi_studio_ingegneria


def getFacultyCod(facolta):
    return facolta[1:7]


def extractCourseCod(course_string):
    match = re.search(r'\[(\d+-\d+)\]', course_string)
    if match:
        return match.group(1)
    return None


def setPage(driver, faculty_code, line_index, year=None):
    wait_time = WebDriverWait(driver, 10)
    dipartimento = Select(wait_time.until(EC.presence_of_element_located((By.ID, "dipartimento"))))
    dipartimento.select_by_value(COURSE_CATALOG_DIEF_COD)
    if year is not None:
        anno_offerta = Select(wait_time.until(EC.presence_of_element_located((By.ID, "anno-offerta"))))
        options_anno_offerta = anno_offerta.options
        for o in options_anno_offerta:
            if o.get_attribute('value').__contains__(year):
                o.click()
                break

    time.sleep(1)
    input_form = driver.find_element(By.CSS_SELECTOR, '[aria-autocomplete="list"]')
    input_form.send_keys(" ")
    corsi = driver.find_elements(By.CSS_SELECTOR, '[role="option"]')

    if line_index != 0:
        corsi[line_index].click()
    else:
        for c in corsi:
            cod = extractCourseCod(c.text)
            if cod == faculty_code:
                c.click()
                break
            line_index += 1

    search_button = wait_time.until(EC.element_to_be_clickable((By.CLASS_NAME, "primary")))
    search_button.click()
    div_result = wait_time.until(EC.presence_of_element_located((By.CLASS_NAME, "cerca-insegnamenti-risultati")))
    ul_result = div_result.find_element(By.TAG_NAME, "ul")
    insegnamenti = ul_result.find_elements(By.CLASS_NAME, "insegnamenti-leaf")

    return insegnamenti, line_index


def getSemestre(periodo):
    if "Primo" in periodo:
        return 1
    elif "Secondo" in periodo:
        return 2

    return 3


def getExamsInformation(faculty_code, year=None):
    nomi_list = []
    anni_list = []
    semestri_list = []
    crediti_list = []
    line_index = 0
    url = 'https://unimore.coursecatalogue.cineca.it/cerca-insegnamenti'
    driver = initializeDriver()
    driver.get(url)
    wait_time = WebDriverWait(driver, 10)
    accept_cookie_button = wait_time.until(EC.element_to_be_clickable((By.ID, "c-p-bn")))
    accept_cookie_button.click()
    insegnamenti, line_index = setPage(driver, faculty_code, line_index, year)
    num_exams = len(insegnamenti)

    for j in range(num_exams):
        h3_tag = insegnamenti[j].find_element(By.TAG_NAME, "h3")
        div_a = h3_tag.find_element(By.CLASS_NAME, "flex-container")
        a_tag = div_a.find_element(By.TAG_NAME, "a")
        nome_esame = a_tag.text
        if nome_esame in nomi_list:
            continue
        else:
            a_tag.click()
            dl_container = wait_time.until(EC.presence_of_element_located((By.CLASS_NAME, "accordion")))
            first_dd = dl_container.find_element(By.TAG_NAME, "dd")
            dl_list_container = first_dd.find_element(By.CLASS_NAME, "u-dl-orizzontale")
            dl_list = dl_list_container.find_elements(By.TAG_NAME, "dl")
            anno_esame = dl_list[2].find_element(By.TAG_NAME, "dd").find_element(By.TAG_NAME, "span").text
            crediti_esame = dl_list[6].find_element(By.TAG_NAME, "dd").find_element(By.TAG_NAME, "span").text
            periodo_esame = dl_list[10].find_element(By.TAG_NAME, "dd").find_element(By.TAG_NAME, "span").text
            nomi_list.append(nome_esame)
            anni_list.append(anno_esame)
            crediti_list.append(crediti_esame)
            semestre = getSemestre(periodo_esame)
            semestri_list.append(semestre)
            driver.back()
            insegnamenti, line_index = setPage(driver, faculty_code, line_index, year)

    driver.quit()
    result = [nomi_list, anni_list, crediti_list, semestri_list]
    return result


def getAppelliInformation(facolta):
    exam_list = []
    date_list = []
    url = 'https://www.esse3.unimore.it/Guide/PaginaListaAppelli.do'
    driver = initializeDriver()
    driver.get(url)
    wait_time = WebDriverWait(driver, 10)
    accept_cookie_button = wait_time.until(EC.element_to_be_clickable((By.ID, "c-p-bn")))
    accept_cookie_button.click()
    dipartimento = Select(wait_time.until(EC.presence_of_element_located((By.ID, "FAC_ID"))))
    dipartimento.select_by_value(APPELLI_DIEF_COD)
    corsi = Select(wait_time.until(EC.presence_of_element_located((By.ID, "CDS_ID"))))
    corsi.select_by_visible_text(facolta)
    search_button = wait_time.until(EC.element_to_be_clickable((By.NAME, "actionBar1")))
    search_button.click()
    result_table = wait_time.until(EC.presence_of_element_located((By.ID, "tableAppelli")))
    result_table_body = result_table.find_element(By.CLASS_NAME, "table-1-body")
    rows_table = result_table_body.find_elements(By.TAG_NAME, "tr")
    number_rows = len(rows_table)

    for i in range(number_rows):
        columns_row = rows_table[i].find_elements(By.TAG_NAME, "td")
        esame = columns_row[0].text.upper()
        data = columns_row[2].text
        exam_list.append(esame)
        date_list.append(data)

    driver.quit()
    result = [exam_list, date_list]
    return result


def getListaAule(wait_time):
    aule_list = []
    for i in range(3):
        if i == 1:
            page_2 = wait_time.until(EC.presence_of_element_located((By.CSS_SELECTOR, TITLE_AULE_PAGINA_2)))
            page_2.click()
        elif i == 2:
            page_3 = wait_time.until(EC.presence_of_element_located((By.CSS_SELECTOR, TITLE_AULE_PAGINA_3)))
            page_3.click()

        main_table = wait_time.until(EC.presence_of_element_located((By.CLASS_NAME, "timegrid")))
        table_head = main_table.find_element(By.TAG_NAME, "thead")
        table_head_columns = table_head.find_elements(By.TAG_NAME, "td")
        table_head_columns.pop(0)
        for c in table_head_columns:
            nome_aula = c.text.split('\n')[0]
            if not nome_aula.__eq__(' '):
                aule_list.append(nome_aula)

    return aule_list


def getAule():
    url = 'http://www.aule.unimore.it/index.php?page=0&content=view_prenotazioni&vista=day&area=27&_lang=it&day='
    driver = initializeDriver()
    driver.get(url)
    wait_time = WebDriverWait(driver, 10)
    aule_list = getListaAule(wait_time)

    return aule_list


def fixDisponibilita(disponibilita):
    intervalli_accorpati = []
    inizio_corrente = None
    fine_corrente = None

    def to_datetime(ora_str):
        return datetime.strptime(ora_str, "%H:%M")

    def to_str(ora):
        return ora.strftime("%H:%M")

    for intervallo in disponibilita:
        inizio, fine = intervallo.split('-')
        inizio_dt = to_datetime(inizio)
        fine_dt = to_datetime(fine)
        if inizio_dt >= to_datetime("19:00"):
            break

        if inizio_corrente is None:
            inizio_corrente = inizio_dt
            fine_corrente = fine_dt
        elif fine_corrente == inizio_dt:
            fine_corrente = fine_dt
        else:
            intervalli_accorpati.append(f"{to_str(inizio_corrente)}-{to_str(fine_corrente)}")
            inizio_corrente = inizio_dt
            fine_corrente = fine_dt

    if inizio_corrente is not None:
        intervalli_accorpati.append(f"{to_str(inizio_corrente)}-{to_str(fine_corrente)}")

    return intervalli_accorpati


def getAuleDisponibilita(wait_time, aule_disponibilita):
    for i in range(3):
        if i == 1:
            page_2 = wait_time.until(EC.presence_of_element_located((By.CSS_SELECTOR, TITLE_AULE_PAGINA_2)))
            page_2.click()
        elif i == 2:
            page_3 = wait_time.until(EC.presence_of_element_located((By.CSS_SELECTOR, TITLE_AULE_PAGINA_3)))
            page_3.click()
        main_table = wait_time.until(EC.presence_of_element_located((By.CLASS_NAME, "timegrid")))
        table_body = main_table.find_element(By.TAG_NAME, "tbody")
        table_body_rows = table_body.find_elements(By.TAG_NAME, "tr")
        for r in table_body_rows:
            columns_of_row = r.find_elements(By.TAG_NAME, "td")

            for c in columns_of_row:
                titolo_colonna = c.get_attribute('title')
                pattern = r"^([\d]{2}:[\d]{2}-[\d]{2}:[\d]{2}), (.+?) \d+ posti"
                match = re.match(pattern, titolo_colonna)
                if match:
                    orario = match.group(1)
                    aula = match.group(2)
                    aule_disponibilita.get(aula).append(orario)

    return aule_disponibilita


def getAuleInformation(day, month, year):
    url = 'http://www.aule.unimore.it/index.php?page=0&content=view_prenotazioni&vista=day&area=27&_lang=it&day=' + day + \
          '&month=' + month + '&year=' + year
    driver = initializeDriver()
    driver.get(url)
    wait_time = WebDriverWait(driver, 10)
    aule_disponibilita = {}
    aule_list = getListaAule(wait_time)
    for a in aule_list:
        aule_disponibilita[a] = []

    driver.get(url)
    aule_disponibilita = getAuleDisponibilita(wait_time, aule_disponibilita)
    driver.quit()
    for a in aule_disponibilita:
        disp_correct = fixDisponibilita(aule_disponibilita.get(a))
        aule_disponibilita[a] = disp_correct
    return aule_disponibilita


