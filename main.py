#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os, sys, time, random
import requests, json
import datetime, calendar
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

class userdata:
    tusur_group = "" #Format: 000-0

    bot_api_token = ""
    bot_api_group_id = ""

    bot_target_peer_id = ""

    '''
    def get_from_files():
        if len(userdata.tusur_group) <= 1:
            try:
                pars_SEND_TO=open("tusur_group.txt")
                _SEND_TO=pars_SEND_TO.read()
                _SEND_TO=_SEND_TO.split("\n")
                _SEND_TO=int(_SEND_TO[0])
            except:
                pars_SEND_TO=open("tusur_group.txt", 'w')
                pars_SEND_TO.write("Enter your tusur group here")
                pars_SEND_TO.close()
                raise SystemExit(228)

        if len(userdata.bot_api_token) <= 1:
            try:
                pars_SEND_TO=open("bot_target_peer_id.txt")
                _SEND_TO=pars_SEND_TO.read()
                _SEND_TO=_SEND_TO.split("\n")
                _SEND_TO=int(_SEND_TO[0])
                if len(_SEND_TO) != 9:
                    print("[ ERROR ] Invalid id length")
            except:
                pars_SEND_TO=open("bot_target_peer_id.txt", 'w')
                pars_SEND_TO.write("Enter your target peer_id here")
                pars_SEND_TO.close()
                raise SystemExit(228)

        if len(userdata.bot_api_token) <= 1:
            try:
                pars_TOKEN=open("bot_api_token.txt")
                api_token=str(pars_TOKEN.read())
                api_token=api_token.replace("\n","")
                api_token=api_token.replace(" ","")
                if len(_SEND_TO) != 85:
                    print("[ ERROR ] Invalid token length")
            except:
                pars_TOKEN=open("bot_api_token.txt", 'w')
                pars_TOKEN.write("Enter your bot token here")
                pars_TOKEN.close()
                raise SystemExit(228)

        if len(userdata.group_bot_id) <= 1:
            try:
                pars_GROUP_ID=open("group_bot_id.txt")
                api_group_id=pars_GROUP_ID.read()
                api_group_id=api_group_id.split("\n")
                api_group_id=int(api_group_id[0])
            except:
                pars_GROUP_ID=open("group_bot_id.txt", 'w')
                pars_GROUP_ID.write("Enter your bot id here")
                pars_GROUP_ID.close()
                raise SystemExit(228)
        '''

url = "https://timetable.tusur.ru/faculties/fsu/groups/"+userdata.tusur_group+".ics"

#EXTRA CODE
#if ("--release" in sys.argv): print(" >>> Отправляю в беседу"); userdata.bot_target_peer_id = "###"

class color:
    good = '\033[92m]'
    ok = '\033[96]'
    warn = '\033[93]'
    bad = '\033[91]'
    readme = '\033[95]'
    info = '\033[94]'
    clear = '\033[0]'
    font_bold = '\033[1]'

###Check for call arguments
def interface_args():
    global _verbose; _verbose = False

    if ("--verbose" in sys.argv or "-v" in sys.argv):
        print("[  "+color.readme+"INFO"+color.clear+"  ] Verbose "+color.info+"enabled"+color.clear)
        _verbose = True
    
    global _date_now

    if("--date" in sys.argv or "-d" in sys.argv):
        for i in range(1, len(sys.argv)):
            try:
                if (sys.argv[i] == "--date" or sys.argv[i] == "-d"):
                    if len(sys.argv[i+1]) == 8:
                        _date_now = str(sys.argv[i+1])
                    else:
                        raise ValueError
            except:
                raise ValueError

def get_date():
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    return tomorrow.strftime('%Y%m%d')

def get_week_parity(date: str) -> str:
    year = int(date[0:4]); month = int(date[4:6]); day = int(date[6:8])
    calendar_ = calendar.TextCalendar(calendar.MONDAY)
    lines = calendar_.formatmonth(year, month).split('\n')
    days_by_week = [week.lstrip().split() for week in lines[2:]]
    str_day = str(day)
    for index, week in enumerate(days_by_week):
        if str_day in week:
            if (index+1)%2==0:
                return True
            else:
                return False
    raise ValueError("[ ERROR ] GET_WEEK_PARITY: Wrong date!")

def verbose(log_text: str) -> str:
    global _verbose
    if _verbose:
        print(log_text)

def captcha_handler(captcha):
    key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()
    return captcha.try_again(key)

### ### MAIN ###

_date_now = get_date()

interface_args()

week_parity = get_week_parity(_date_now)

response = requests.get(url)
verbose(" >>> Все данные: " + response.text)
raw_data = response.text.split("\n")

_in_event = False
_was_print = False
_json = {}
_json_temp = {}
_lessons_count = -1

for i in range(len(raw_data)):

    if raw_data[i][0:5] == "BEGIN":
        VALUE = raw_data[i][6:len(raw_data[i])]
        if VALUE == "VEVENT":
            if not _in_event:
                _in_event = True
            else:
                raise ValueError("Двойное вхождение в event!")

    if raw_data[i][0:5] == "DTEND":
        VALUE = raw_data[i][6:len(raw_data[i])]
        if str(_date_now) == str(VALUE[38:46]):
            _was_print = True
            _json_temp['STOP'] = str(VALUE[47:51])

                
    if raw_data[i][0:7] == "DTSTART":
             VALUE = raw_data[i][8:len(raw_data[i])]
             if _was_print:
                _json_temp['START'] = str(VALUE[47:51])

    if raw_data[i][0:11] == "DESCRIPTION":
             VALUE = raw_data[i][12:len(raw_data[i])]
             if _was_print:
                 _json_temp['DESCRIPTION'] = str(VALUE)
                             
    if raw_data[i][0:7] == "SUMMARY":
             VALUE = raw_data[i][8:len(raw_data[i])]
             if _was_print:
                 _json_temp['SUMMARY'] = str(VALUE)

    if raw_data[i][0:8] == "LOCATION":
             VALUE = raw_data[i][9:len(raw_data[i])]
             if _was_print:
                 _json_temp['LOCATION'] = str(VALUE)

    if raw_data[i][0:3] == "END":
             VALUE = raw_data[i][4:len(raw_data[i])]
             if VALUE == "VEVENT":
                if _in_event:
                    _in_event = False
                    if len(_json_temp) > 0:
                        _lessons_count += 1
                        _json[_lessons_count] = _json_temp
                        verbose(" >>> Промежуточный json["+str(_lessons_count)+"]: " + str(_json_temp))
                    _json_temp = {} #Errase
                    _was_print = False
                else:
                    raise ValueError("Двойной выход из event!")


verbose("\n >>> Готовый json пакет: " + str(_json))

errCout = 0
while True:
    try:
        vk_session = vk_api.VkApi(token=userdata.bot_api_token, captcha_handler=captcha_handler)
        longpoll = VkBotLongPoll(vk_session, userdata.bot_api_group_id)
        session_api = vk_session.get_api()
        vk = vk_session.get_api()
        break

    except vk_api.AuthError as error_msg:
        print(error_msg)
        errCout = errCout+1
        if(errCout < 10):
            print("[\033[31m!!\033[0m]Ошибка авторизации!");
            print("Проверьте подключение к интернету");
            print("Проверьте правильность токена");
            print("Попробуйте получить новый токен");print();
            print("Повтор ...");print();
            time.sleep(5)
        else:
            print("[\033[31m!!\033[0m]Превышенно количество попыток авторизации!");
            raise SystemExit(401)

text = "✅ Расписание на " + _date_now[6:8] + "." + _date_now[4:6] + " | Неделя "
if week_parity:
    text += "чётная\n"
else:
    text += "нечётная\n"

#Sort by time:
_sorted_json = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}}

times_mass = ['0850', '1040', '1315', '1500', '1645', '1830', '2015']
_tmp = 0

for ii in range(0,7):
    try:
        for i in range(7):
            if str(_json[i]['START']) == str(times_mass[ii]):
                _sorted_json[_tmp] = _json[i]
                _tmp += 1
                break
    except: pass

verbose("\n >>> Сортированный json :" + str(_sorted_json))
if _lessons_count+1 != _tmp: raise ValueError("Потерялось значение во время сортирвки")
_json = _sorted_json

for i in range(7):
    try:
        text += "\n-------["+str(_json[i]['START'])[0:2]+":"+str(_json[i]['START'])[2:4]+" - "+str(_json[i]['STOP'])[0:2]+":"+str(_json[i]['STOP'])[2:4]+"]-------\n"
        text += "📋 Предмет: "+str(_json[i]['SUMMARY']).replace("\\"," ")+"\n"
        if len(_json[i]['DESCRIPTION']) > 0:
            text += "✏ Примечания: "+str(_json[i]['DESCRIPTION']).replace("\\"," ")+"\n"
        if len(_json[i]['LOCATION']) > 0:
            text += "🗺️ Где: "+str(_json[i]['LOCATION']).replace("\\"," ")+"\n"
        else:
            #if str(_json[i]['SUMMARY']).replace("\\"," ") == "Основы проектной деятельности": text += "🔗 Ссылка: https://sdo.tusur.ru/course/view.php?id=####"
            #if str(_json[i]['SUMMARY']).replace("\\"," ") == "Физическая культура и спорт": text += "Обычная физра" #Тут нужно потом реализовать своё расписание по физре
            #elif ...
            
    except: pass

vk.messages.send(
    peer_id = userdata.bot_target_peer_id,
    random_id = 0,
    dont_parse_links = 1,
    message = text)
