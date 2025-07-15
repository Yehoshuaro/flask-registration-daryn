from flask import Flask, request, render_template, redirect, url_for
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
import logging
from flask_session import Session
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openpyxl import load_workbook


app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


# Google API settings
SCOPE = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]
SERVICE_ACCOUNT_FILE = "service_account.json"
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
gc = gspread.authorize(credentials)
drive_service = build('drive', 'v3', credentials=credentials)

@app.route('/', methods=['GET'])
def registration_form():
    areas_with_schools = read_excel_data()
    return render_template('index.html', areas_with_schools=areas_with_schools)

def read_excel_data():
    workbook = load_workbook("Schools.xlsx")
    sheet = workbook.active
    areas_with_schools = {}

    schools_to_remove = [
        '"Құрама бастауыш мектебі" КММ мектептің жабылуына құжаттар дайындалуда',
        '"Андрейниковка бастауыш мектебі" КММ мектептің жабылуына құжаттар дайындалуда',
        'Уақытша жабылды "АЗИЯ" комплекс-мектебі м-сі',
        '"Философиялық бағыттағы жалпы білім беретін жеке мектеп" ЖММ (уақытша жұмысы тоқтатылды)',
        '"№31 жалпы орта білім беретін мектебі" КММ (жұмысы тоқтатылды)',
        '"№44 негізгі орта мектебі" КММ (қызметі уақытша тоқтатылды)',
        '"Ассоциированная школа ЮНЕСКО "ДИАЛОГ" ЖММ (жұмысы тоқтатылған)',
        '(Уақытша жұмысы тоқтатылған) Шығыс Қазақстан облысы білім басқармасы Күршім ауданы бойынша білім бөлімінің «Топтерек бастауыш мектебі» коммуналдық мемлекеттік мекемесі',
        '(Уақытша тоқтатылды) Шығыс Қазақстан облысы білім басқармасы Күршім ауданы бойынша білім бөлімінің «Жиделі бастауыш мектебі» коммуналдық мемлекеттік мекемесі',
        '"Math-Language "SEED SCHOOL" ЖМ (тоқтатылған)',
        'КЕБМ"Экономикалық лицей" (тоқтатылған)',
        '"Қазақ ұлттық хореография академиясы" мектебі ҚЕАҚ (Тоқтатылды)',
        '"MLS ELORDA" ЖШС (Тоқтатылған)',
        ' «National Academy of Education «ULAGAT» мектебі (Тоқтатылған)',
        '-',
        '"Көкшетау қаласындағы ФМБ НЗМ"',
        'Атырау қаласындағы "ХББ НЗМ" филиалы',
        '"Ақтөбе қаласындағы ФМБ НЗМ" филиалы ',
        '"Орал қаласындағы ФМБ НЗМ" филиалы ',
        '"Талдықорған қаласындағы ФМБ НЗМ" филиалы',
        'Қарағанды қаласындағы "ХББ НЗМ" ф-лы',
        '"Қостанай қаласындағы ФМБ НЗМ"',
        '"Тараз қаласындағы ФМБ НЗМ" филиалы',
        'Қызылорда қаласындағы ХББ НЗМ филиалы',
        'Ақтау қаласындағы ХББ НЗМ филиалы',
        'Шымкент қ. "химия-биологиялық бағыттағы НЗМ" филиалы',
        'Шымкент қ. "физика-математикалық бағыттағы НЗМ" филиалы',
        'Павлодар қаласындағы ХББ НЗМ филиалы',
        ' "Өскемен қаласының ХББ НЗМ"  филиалы',
        '"Семей қаласындағы ФМБ НЗМ"',
        '"Петропавл қаласының ХББ НЗМ" филиалы',
        '"НЗМ"  ДБҰ "Астана қаласындағы Назарбаев Зияткерлік мектебі" филиалы',
        'Астана қаласындағы "физика-математикалық бағытындағы Назарбаев Зияткерлік мектебі" "НЗМ"  ДБҰ филиалы',
        '"НЗМ" ДБҰ "Астана қаласындағы Халықаралық мектеп" филиалы',
        '"Алматы қаласындағы ХББ НЗМ" филиалы',
        '"Алматы қаласындағы ФМБ НЗМ" филиалы ',
        'Түркістан қ. "химия-биологиялық бағыттағы НЗМ" филиалы',
        '"Республикалық физика-математикалық мектебі" КЕАҚ филиалы',
        '"Республикалық физика-математика мектебі" КЕАҚ филиалы',
        'Орал қ. «Республикалық физика-математикалық мектебі» Коммерциалық емес акционерлік қоғамының филиалы',
        '"Абай атындағы Республикалық мамандандырылған дарынды балаларға арналған қазақ тілі мен әдебиетін тереңдете оқытатын орта мектеп- интернаты" РММ'

    ]
    for row in sheet.iter_rows(min_row=2, values_only=True):
        area = row[4]  # Assuming area is in the first column (0-indexed)
        school = row[6]  # Assuming schools are in the second column (0-indexed)

        if school in schools_to_remove:
            continue

        if area in areas_with_schools:
            areas_with_schools[area].append(school)
        else:
            areas_with_schools[area] = [school]

    areas_with_schools["«Бөбек» Ұлттық ғылыми-практикалық, білім беру және сауықтыру орталығы» РМҚК"] = ["«Бөбек» Ұлттық ғылыми-практикалық, білім беру және сауықтыру орталығы» РМҚК"]
    areas_with_schools["НЗМ ДББҰ"] = ["Көкшетау қаласындағы ФМБ НЗМ", "Атырау қаласындағы ХББ НЗМ филиалы", "Ақтөбе қаласындағы ФМБ НЗМ филиалы",
                                      "Орал қаласындағы ФМБ НЗМ филиалы", "Талдықорған қаласындағы ФМБ НЗМ филиалы", "Қарағанды қаласындағы ХББ НЗМ филиалы",
                                      "Қостанай қаласындағы ФМБ НЗМ", "Тараз қаласындағы ФМБ НЗМ филиалы", "Қызылорда қаласындағы ХББ НЗМ филиалы",
                                      "Ақтау қаласындағы ХББ НЗМ филиалы", "Шымкент қ. химия-биологиялық бағыттағы НЗМ филиалы", "Шымкент қ. физика-математикалық бағыттағы НЗМ филиалы",
                                      "Өскемен қаласының ХББ НЗМ  филиалы", "Семей қаласындағы ФМБ НЗМ", "Петропавл қаласының ХББ НЗМ филиалы", "НЗМ ДБҰ Астана қаласындағы Назарбаев Зияткерлік мектебі филиалы",
                                      "Астана қаласындағы физика-математикалық бағытындағы Назарбаев Зияткерлік мектебі НЗМ  ДБҰ филиалы", "НЗМ ДБҰ Астана қаласындағы Халықаралық мектеп филиалы",
                                      "Алматы қаласындағы ХББ НЗМ филиалы", "Алматы қаласындағы ФМБ НЗМ филиалы", "Түркістан қ. химия-биологиялық бағыттағы НЗМ филиалы", "Павлодар қаласындағы ХББ НЗМ филиалы"]
    areas_with_schools["РФММ КеАҚ"] = [
        "Астана қ. Республикалық физика-математикалық мектебі КЕАҚ филиалы", "Алматы қ. Республикалық физика-математикалық мектебі КЕАҚ филиалы", "Орал қ. Республикалық физика-математикалық мектебі КЕАҚ филиалы"]
    areas_with_schools["Абай атындағы РММИ"] = ["Абай атындағы Республикалық мамандандырылған дарынды балаларға арналған қазақ тілі мен әдебиетін тереңдете оқытатын орта мектеп- интернаты РММ"]
    return areas_with_schools


@app.route('/submit', methods=['POST'])
def submit_registration():
    try:
        # Get form data
        field_data = {
            'Аймақтың атауы': request.form['area'],
            'Мектебі': request.form['school'],
            'Қатысушының ЖСНі': request.form['participant_iin'],
            'Қатысушының аты-жөні': request.form['participant_name'],
            'Қатысушының жынысы': request.form['participant_gender'],
            'Топтық / жеке': request.form['group/individual'],
            'Сыныбы': request.form['participant_class'],
            'Қалалық / Ауылдық': request.form['city/rural'],
            'Оқу тілі': request.form['language'],
            'Секциясы': request.form['section'],
            'Тақырыбы': request.form['project_title'],
            '1-ші жетекшінің аты-жөні': request.form['1st_supervisor_name'],
            '1-ші жетекшінің ЖСНі': request.form['1st_supervisor_iin'],
            '2-ші жетекшінің аты-жөні': request.form['2nd_supervisor_name'],
            '2-ші жетекшінің ЖСНі': request.form['2nd_supervisor_iin']
        }

        # Convert field_data values into a list in the desired order
        participant_values = [
            field_data['Аймақтың атауы'],
            field_data['Мектебі'],
            field_data['Қатысушының ЖСНі'],
            field_data['Қатысушының аты-жөні'],
            field_data['Қатысушының жынысы'],
            field_data['Топтық / жеке'],
            field_data['Сыныбы'],
            field_data['Қалалық / Ауылдық'],
            field_data['Оқу тілі'],
            field_data['Секциясы'],
            field_data['Тақырыбы'],
            field_data['1-ші жетекшінің аты-жөні'],
            field_data['1-ші жетекшінің ЖСНі'],
            field_data['2-ші жетекшінің аты-жөні'],
            field_data['2-ші жетекшінің ЖСНі']
        ]


        # Check required fields
        required_fields = ['area', 'participant_name', 'participant_iin', 'participant_gender', 'group/individual',
                           'participant_class', 'school', 'city/rural', 'language', 'section', 'project_title',
                           '1st_supervisor_name', '1st_supervisor_iin', 'file']
        for field in required_fields:
            if not request.form.get(field, None) and field != 'file':
                return "Ошибка: Все поля должны быть заполнены.", 400
            if field == 'file' and 'file' not in request.files:
                return "Ошибка: Файл проекта обязателен.", 400

        # Upload file to Google Drive
        uploaded_file = request.files['file']
        if uploaded_file.filename == "":
            return "Ошибка: Файл не выбран.", 400

        file_data = uploaded_file.read()
        media = MediaIoBaseUpload(BytesIO(file_data), mimetype='application/pdf/xlsx', resumable=True)
        file_metadata = {
            'name': uploaded_file.filename,
            'parents': ['1C5KLj4ex6yIB2k893NcgatN2RJFBsY0j']  # Replace with your Google Drive folder ID
        }
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        # Save data to Google Sheets
        sheet = gc.open('Registration_Data').sheet1
        sheet.append_row(participant_values)

        return redirect(url_for('registration_form'))

    except Exception as e:
        # Error handling and logging
        print(f"Произошла ошибка: {str(e)}")
        return "Внутренняя ошибка сервера", 500

logging.basicConfig(level=logging.INFO, filename='app.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')
logging.info("Приложение запущено")
logging.error("Произошла ошибка при обработке запроса")


def validate_iin(iin):
    """ Validate Kazakhstani ID format. """
    return re.match(r'^\d{12}$', iin)

def validate_email(email):
    """ Validate email format. """
    return re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email)

def send_email(recipient, subject, body):
    """ Send email. """
    msg = MIMEMultipart()
    msg['From'] = 'MYEMAIL'
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.example.com', 587)
    server.starttls()
    server.login(msg['From'], 'your password')
    server.send_message(msg)
    server.quit()

if __name__ == '__main__':
    app.run(debug=True, port=8080)  # SSL for HTTPS
