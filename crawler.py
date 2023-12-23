import time
import schedule
from datetime import datetime
from os.path import join, isfile

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_argument('--headless')
options.page_load_strategy = 'eager'

WHITE_LIST = ['...']

def _row(main_list: list):
    main_string = ''
    for row_list in main_list:
        if len(row_list[3]) == 0:
            region = ' - '
            c = 'region'

        else:
            region = "<ul>"
            for reg in row_list[3]:
                region += f'<li>{reg}</li>'
            region += "</ul>"
            c = ''

        main_string += f"""
        <tr>
            <td>{row_list[0]}</td>
            <td>${row_list[1]}</td>
            <td class='{row_list[2].lower()}'>{row_list[2]}</td>
            <td class='{c}'>{region}</td>
        </tr>
        """
    return main_string


def login(driver):
    email = driver.find_element(By.XPATH, "//input[@id='email-input']")
    email.click()
    email.send_keys('...')
    time.sleep(0.5)
    password = driver.find_element(By.XPATH, "//input[@id='password-input']")
    password.click()
    password.send_keys('...')
    time.sleep(0.5)
    sign_button = driver.find_element(By.XPATH, "//button[@ng-click='logIn()']")
    sign_button.click()

    log_file = open('log.txt', 'a')
    log_file.write(f">>> Successful login    {datetime.now().strftime('%H:%M;  %B %d, %Y')} \n")
    log_file.close()


def gpu_availability_check(driver):
    try:
        driver.find_element(By.XPATH, "//div[contains(@class, '_column-name') and text() = 'Name']")
        log_file = open('log.txt', 'a')
        log_file.write(f">>> GPU already lunched!    {datetime.now().strftime('%H:%M;  %B %d, %Y')} \n")
        log_file.close()
        return None

    except NoSuchElementException:
        pass

    launch_button = driver.find_element(By.XPATH, "//button[@title='Launch instance']")
    launch_button.click()
    time.sleep(1)

    names = []
    for n in driver.find_elements(By.XPATH,
                                  "//div[contains(@class, '_option-list_')]//span[contains(@class,'_instance-type-title_')]"):
        names.append(n.text)

    prices = []
    for p in driver.find_elements(By.XPATH,
                                  "//div[contains(@class, '_option-list_')]//span[contains(@class, '_price_')]"):
        prices.append(p.text)

    availability = []
    regions = []

    availability_names = []
    get_regions = []
    elements = driver.find_elements(By.XPATH, "//div[contains(@class, '_option-list_')]/div")
    for idx, ele in enumerate(elements):

        try:
            ele.find_element(By.XPATH, ".//div[contains(@class, '_request-button_')]")
            availability.append("Unavailable")
            regions.append([])

        except NoSuchElementException:
            availability.append("Available")
            availability_names.append(names[idx])
            get_regions.append(idx)
            regions.append([])

    if len(get_regions) > 0:
        for reg_idx in get_regions:
            try:
                elements = driver.find_elements(By.XPATH, "//div[contains(@class, '_option-list_')]/div")
                driver.execute_script("arguments[0].scrollIntoView()", elements[reg_idx])
                time.sleep(1)
                elements[reg_idx].click()
                time.sleep(3)
                region_elements = driver.find_elements(By.XPATH, "//div[contains(@class, '_option-list_')]/div")
                for idx, reg in enumerate(region_elements):
                    info = reg.find_element(By.XPATH, ".//div[contains(@class, '_region-pretty_')]").text
                    if '—Not available' not in info:
                        regions[reg_idx].append(info)
                back = driver.find_element(By.XPATH, "//div[contains(@class, '_icon-button_st')]")
                back.click()
                time.sleep(2)

            except Exception as e:
                print(f'Error in region collection: \n{str(e)}')

    main = []
    text = ''
    for name, price, ava, reg in zip(names, prices, availability, regions):
        main.append([name, price, ava, reg])
        text += f"  {names.index(name) + 1}: {name}, price: ${price}, status: {ava}, regions: {reg}\n"

    if availability.count('Available') == 0:
        text = '    No Available GPU at the moment\n'

    log_file = open('log.txt', 'a')
    log_file.write(f">>> Successful scrape    {datetime.now().strftime('%H:%M;  %B %d, %Y')} \n{text}\n")
    log_file.close()

    if availability.count('Available') > 0:
        if len(WHITE_LIST) > 0:
            for w in WHITE_LIST:
                for reg in get_regions:
                    if w in regions[reg]:
                        return main, True
            if 'No Available GPU' not in text:
                for ava_n in availability_names:
                    if ava_n in WHITE_LIST:
                        return main, True

            log_file = open('log.txt', 'a')
            log_file.write(
                f">>> Regions from White_list not available    {datetime.now().strftime('%H:%M;  %B %d, %Y')}    White_list: {WHITE_LIST}\n\n")
            log_file.close()
            return main, False
        else:
            return main, True
    return main, False


def send_email(main: list):
    sender_email = "..."
    receiver_email = "..."
    password = "..."

    message = MIMEMultipart("alternative")
    message["Subject"] = "GPU Availability"
    message["From"] = sender_email
    message["To"] = receiver_email

    NOW = datetime.now()
    html = '''
    <html>
    <head><style>
        table {
          font-family: Georgia, sans-serif;
          border-collapse: collapse;
          width: 75%; }
        td, th {
          border: 1px solid #dddddd;
          text-align: left;
          padding: 8px; }
        tr:nth-child(even) {
          background-color: #dddddd; }
        .available {
            color: #007517;
            font-weight: 700;}
        .unavailable {
        color: #960303; }
        .region { padding-left: 30px;}
        li {float: left;
        margin-left: 30px;}
        ul {display: inline;}
        h3 { padding-left: 28px; }
        p { padding-left: 18px; }
    </style></head> ''' + f'''
  <body>
  	<h3>Hi Boss!!!</h3>
    <p>On {NOW.strftime("%B %d, %Y")} at {NOW.strftime('%H:%M')} there are some avaible GPUs at <a href="https://cloud.lambdalabs.com/instances"><b>Lambda Labs</b></a>:
    </p>

    <table style="width:90%;">
    	<tbody>
            <tr>
            	<th>GPU</th>
                <th>Price</th>
                <th>Availability</th>
                <th style="width:50%">Region</th>
            </tr>
        	{_row(main)}
        </tbody>
    </table>
  </body>
</html>
    '''

    message.attach(MIMEText(html, 'html'))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )
        log_file = open('log.txt', 'a')
        log_file.write(f">>> Successful email_sent    {datetime.now().strftime('%H:%M;  %B %d, %Y')} \n\n")
        log_file.close()

def execute():

    driver = webdriver.Chrome(options=options)
    driver.get('https://cloud.lambdalabs.com/login')
    driver.implicitly_wait(2)

    login(driver)
    main, send = gpu_availability_check(driver)
    if send:
        send_email(main)
    driver.close()


if __name__ == "__main__":
    execute()
    schedule.every(25).to(45).minutes.do(execute)
    while 1:
        time.sleep(100)
        schedule.run_pending()


