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

    bot_api_token =""
    bot_api_group_id = ""

    bot_target_peer_id = ""

    def checkdata():
        if not(userdata.tusur_group and userdata.bot_api_token
        and userdata.bot_api_group_id and userdata.bot_target_peer_id):
            print("Не введены данные (группа/токен/id)\nПроверьте строчки 11-16")
            raise ValueError()

url_icalc = "https://timetable.tusur.ru/faculties/fsu/groups/"+userdata.tusur_group+".ics"
url_parser = "https://timetable.tusur.ru/faculties/fsu/groups/"+userdata.tusur_group

class color:
    good = '\033[92m'
    ok = '\033[96m'
    warn = '\033[93m'
    bad = '\033[91m'
    readme = '\033[95m'
    info = '\033[94m'
    clear = '\033[0m'
    font_bold = '\033[1m'

###Проверяем аргументы
def interface_args():
    try:
        
        if("--help" in sys.argv or "-h" in sys.argv):
            print(color.readme+"\nhttps://github.com/6yntar05/tusur_timetable_bot\n\n"+color.clear,
                    "<Команда>/<Сокращение> ["+color.info+"аргумент"+color.clear+"] : Значение\n\n",
                    "--help/-h   : Помощь\n",
                    "--vebose/-v : Подробный вывод\n\n",
                    "--date/-d       ["+color.info+color.font_bold+"%Y%m%d"+color.clear+"]  : Использовать дату формата "+color.font_bold+"%Y%m%d\n"+color.clear,
                    "--peer_id/-p    ["+color.info+"peer_id"+color.clear+"] : Использовать указанный peer_id\n",
                    "--additional/-a ["+color.info+"текст"+color.clear+"]   : Дополнительное сообщение/объявление\n",
                    "--only-msg/-o   ["+color.info+"текст"+color.clear+"]   : Отправить только сообщение (без расписания)\n")
            raise SystemExit(0)
            raise ValueError()
                
        global _verbose; _verbose = False

        if("--verbose" in sys.argv or "-v" in sys.argv):
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
                            raise ValueError(color.bad+color.font_bold+"Неверный формат даты!"+color.clear+" Используйте "+color.good+color.font_bold+"%Y%m%d"+color.clear+" : 20201225")
                except:
                    raise ValueError(color.bad+"Аргумент --date/-d нераспознан"+color.clear)


        #global custom_bot_target_peer_id; custom_bot_target_peer_id = ""
        
        if("--peer_id" in sys.argv or "-p" in sys.argv):
            for i in range(1, len(sys.argv)):
                try:
                    if (sys.argv[i] == "--peer_id" or sys.argv[i] == "-p"):
                        userdata.bot_target_peer_id = str(sys.argv[i+1])
                except:
                    raise ValueError(color.bad+"Аргумент --peer_id/-p нераспознан"+color.clear)
                    

        global _additional_msg; _additional_msg = ""
            
        if("--additional" in sys.argv or "-a" in sys.argv):
            for i in range(1, len(sys.argv)):
                try:
                    if (sys.argv[i] == "--additional" or sys.argv[i] == "-a"):
                        _additional_msg = str(sys.argv[i+1])
                except:
                    raise ValueError(color.bad+"Аргумент --additional/-a нераспознан"+color.clear)

                    
        global _only_msg; _only_msg = ""
                
        if("--only-msg" in sys.argv or "-o" in sys.argv):
            for i in range(1, len(sys.argv)):
                try:
                    if (sys.argv[i] == "--only-msg" or sys.argv[i] == "-o"):
                        _only_msg = str(sys.argv[i+1])
                except:
                    raise ValueError(color.bad+"Аргумент --only-msg/-o нераспознан"+color.clear)
                    
    except ValueError as error:
            print("\n\nНераспознанны аргументы:\n--help / -h - помощь\n\n")
            raise ValueError(error)

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
    raise ValueError("[ "+color.bad+color.bold_font+"ERROR"+color.clear+" ] GET_WEEK_PARITY: Неверная дата")

def verbose(log_text: str) -> str:
    global _verbose
    if _verbose:
        print(log_text)

def captcha_handler(captcha):
    key = input("Введите капчу {0}: ".format(captcha.get_url())).strip()
    return captcha.try_again(key)

class timetable_get:
    def from_icalc(url):
        response = requests.get(url)
        verbose(" >>> Все данные: " + response.text)
        raw_data = response.text.split("\n")

        global _date_now
        
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
        return _json, _lessons_count
        
    def from_parser(url):
        #Возможно тут будет ещё реализация парсинга
        #<table class="table table-bordered table-condensed hidden-xs hidden-sm table-lessons even" aria-hidden="true">...</table>
        _json = {}
        _lessons_count = 0
        
        global _date_now
        
        response = requests.get(url)

        tmp = response.text.split('<table class="table table-bordered table-condensed hidden-xs hidden-sm table-lessons even" aria-hidden="true">')

        tmp = tmp[1].split('</table>')[0]

        #<tr class="lesson_i">..</tr>
        #   <td class="lesson_cell day_ii">..</td>
        
        verbose(" >>> Все данные: " + tmp)
        
        return _json, _lessons_count

### ### MAIN

userdata.checkdata()

_date_now = get_date()

interface_args()

week_parity = get_week_parity(_date_now)

_json, _lessons_count = timetable_get.from_icalc(url_icalc)
#_json, _lessons_count = timetable_get.from_parser(url_parser)

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
            print("[ "+color.bad+"ERROR"+color.clear+" ] Ошибка авторизации!");
            print("  >>> Проверьте подключение к интернету");
            print("  >>> Проверьте правильность токена");
            print("  >>> Попробуйте получить новый токен");print();
            print("Повтор ...");print();
            time.sleep(5)
        else:
            print("[ "+color.bad+"ERROR"+color.clear+" ] Превышенно количество попыток авторизации!");
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
            if str(_json[i]['SUMMARY']).replace("\\"," ") == "Физическая культура и спорт": text += "🕹️ Режим: Чекните по ссылке: null \n"
            #Тут кастомные примечания
            
    except: pass

if _additional_msg: text += "\n⚠️ ИНФОРМАЦИЯ ⚠️: " + _additional_msg

if _only_msg: text = _only_msg

print("[  "+color.good+color.font_bold+"OK"+color.clear+"  ] Message id: "+color.info+ str(vk.messages.send(
    peer_id = userdata.bot_target_peer_id,
    random_id = 0,
    dont_parse_links = 1,
    message = text)))

raise SystemExit(0)