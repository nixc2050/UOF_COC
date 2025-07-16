from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
app = FastAPI()

class WaferRequest(BaseModel):
    account: str
    password: str
    start_date: str  # 格式: YYYY/MM/DD
    end_date: str    # 格式: YYYY/MM/DD
    status: str      # "all", "0", "1", ...
    done_start_date: Optional[str] = None
    done_end_date: Optional[str] = None

def run_selenium_script(account, password, start_date, end_date, status, done_start_date=None, done_end_date=None):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    prefs = {
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'safebrowsing.enabled': True,
        'download.default_directory': '/tmp'   # 通用於 Docker/雲端
    }
    options.add_experimental_option('prefs', prefs)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        login_url = 'https://eip.playnitride.com/UOF/'
        driver.get(login_url)
        driver.find_element(By.ID, 'txtAccount').send_keys(account)
        driver.find_element(By.ID, 'txtPwd').send_keys(password)
        driver.find_element(By.ID, 'btnSubmit').click()
        time.sleep(2)
        driver.get('https://eip.playnitride.com/UOF/WKF/Reader/FormReaderManager.aspx')
        time.sleep(2)
        select = Select(driver.find_element(By.NAME, 'ctl00$ContentPlaceHolder1$DropDownListFormName'))
        select.select_by_value('f7b85329-c326-4af8-b2eb-59d0390b0c0c')
        time.sleep(3)
        status_select = Select(driver.find_element(By.NAME, 'ctl00$ContentPlaceHolder1$DropDownListFormStatus'))
        status_select.select_by_value(status)
        time.sleep(2)
        update_date_and_client_state(driver, "ctl00_ContentPlaceHolder1_rdpBeginTime_dateInput",
                                     "ctl00_ContentPlaceHolder1_rdpBeginTime_dateInput_ClientState", start_date)
        update_date_and_client_state(driver, "ctl00_ContentPlaceHolder1_rdpEndTime_dateInput",
                                     "ctl00_ContentPlaceHolder1_rdpEndTime_dateInput_ClientState", end_date)
        if status == '1':
            if done_start_date:
                update_date_and_client_state(driver, "ctl00_ContentPlaceHolder1_rdpEndFormStart_dateInput",
                                             "ctl00_ContentPlaceHolder1_rdpEndFormStart_dateInput_ClientState",
                                             done_start_date)
            if done_end_date:
                update_date_and_client_state(driver, "ctl00_ContentPlaceHolder1_rdpEndFormEnd_date_input",
                                             "ctl00_ContentPlaceHolder1_rdpEndFormEnd_date_input_ClientState", done_end_date)
        search_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'ctl00_ContentPlaceHolder1_btn_Search')))
        search_button.click()
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, 'GridExportExcel'))).click()
        time.sleep(10)
    finally:
        driver.quit()

def update_date_and_client_state(driver, date_element_id, client_state_element_id, date_value):
    date_element = driver.find_element(By.ID, date_element_id)
    driver.execute_script(f"arguments[0].value = '{date_value}';", date_element)
    client_state_value = date_value.replace("/", "-") + "-00-00-00"
    client_state_element = driver.find_element(By.ID, client_state_element_id)
    driver.execute_script(f"""
        arguments[0].value = JSON.stringify({{
            "enabled":true,
            "emptyMessage":"",
            "validationText":"{client_state_value}",
            "valueAsString":"{client_state_value}",
            "minDateStr":"1900-01-01-00-00-00",
            "maxDateStr":"9999-12-31-00-00-00",
            "lastSetTextBoxValue":"{date_value}"
        }});
    """, client_state_element)
    driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", date_element)

@app.post("/auto_wafer_dw")
def auto_wafer_dw(req: WaferRequest):
    try:
        run_selenium_script(
            req.account,
            req.password,
            req.start_date,
            req.end_date,
            req.status,
            req.done_start_date,
            req.done_end_date
        )
        return {"success": True, "msg": "下載流程已完成"}
    except Exception as e:
        return {"success": False, "error": str(e)}
