from flask import Flask, request
import logging
import json
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
sessionStorage = {}
score = 0

ans = {
    'альберт эйнштейн': ['997614/ad486a2dc41ae1ed8777', 'Физик-теоретик, один из основателей современной теоретической физики, лауреат Нобелевской премии по физике 1921 года, общественный деятель-гуманист.'],
    'александр пушкин': ["1652229/6154b7afccd7eef0355b", 'русский поэт, драматург и прозаик, заложивший основы русского реалистического направления, критик и теоретик литературы, историк, публицист; один из самых авторитетных литературных деятелей первой трети XIX века.'],
    'томас эдисон': ["1521359/01d8aacf9e31622c39e8", 'Американский изобретатель и предприниматель, получивший в США 1093 патента и около 3 тысяч в других странах мира; создатель фонографа; усовершенствовал телеграф, телефон, киноаппаратуру, разработал один из первых коммерчески успешных вариантов электрической лампы накаливания.'],
    'зигмунд фрейд': ["1540737/696e85405dc5ef6fbc70", 'Австрийский психолог, психоаналитик, психиатр и невролог.'],
    'лев толстой': ["1652229/b702d60143cbce0b432c", 'Один из наиболее известных русских писателей и мыслителей, один из величайших писателей-романистов мира. Участник обороны Севастополя.'],
    'федор достоевский': ["1030494/4b07e8abd1a04fcdc78d", 'Русский писатель, мыслитель, философ и публицист. Член-корреспондент Петербургской АН с 1877 года.']
}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return json.dumps(response)


# функция созданная для подсчета очков игрока
def sett(st=None):
    global score
    # удаляет очки за помощь игроку
    if st == 'help':
        score -= 25
    # правильный ответ с 1-ой попытки +100
    elif st == 'ok1':
        score += 100
    # правильный ответ со 2-ой попытки -50
    # но потом снова прибавится 100, тем самым за ответ со 2-ой попытки
    # игрок подучит 50 оч
    elif st == 'ok2':
        score -= 50


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови герой!'
        sessionStorage[user_id] = {
            'first_name': None,  # здесь будет храниться имя
            'game_started': False  # здесь информация о том, что пользователь начал игру. По умолчанию False
        }
        res['response']['buttons'] = [
            {
                'title': 'Что ты можешь?',
                'hide': True
            },
            {
                'title': 'помощь',
                'hide': True
            }
        ]
        return
    if 'что' in req['request']['nlu']['tokens']:
            res['response']['text'] = f'Я Алиса. Отгадаешь знаменитую личность? \n ' \
                f'правильный ответ = 100 оч \n ответ со второй попытки = 50 оч \n помощь = -25 оч \n ' \
                f'Назови имя, чтоб сыграть'
    elif 'помощь' in req['request']['nlu']['tokens'] and 'ответом' not in req['request']['nlu']['tokens']:
            res['response']['text'] = f'Я Алиса. Отгадаешь знаменитую личность? \n ' \
                f'правильный ответ = 100 оч \n ответ со второй попытки = 50 оч \n помощь = -25 оч \n '
    elif sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            # создаём пустой массив, в который будем записывать варианты, которые пользователь уже отгадал
            sessionStorage[user_id]['guessed_ans'] = []
            # как видно из предыдущего навыка, сюда мы попали, потому что пользователь написал своем имя.
            # Предлагаем ему сыграть и два варианта ответа "Да" и "Нет".
            res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. ' \
                f'Я Алиса. Отгадаешь знаменитую личность? \n ' \
                f'правильный ответ = 100 оч \n ответ со второй попытки = 50 оч \n помощь = -25 оч'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]
    else:
        # У нас уже есть имя, и теперь мы ожидаем ответ на предложение сыграть.
        # В sessionStorage[user_id]['game_started'] хранится True или False в зависимости от того,
        # начал пользователь игру или нет.
        if not sessionStorage[user_id]['game_started']:
            # игра не начата, значит мы ожидаем ответ на предложение сыграть.
            if 'да' in req['request']['nlu']['tokens']:
                # если пользователь согласен, то проверяем не отгадал ли он уже все.
                # По схеме можно увидеть, что здесь окажутся и пользователи, которые уже отгадывали все
                if len(sessionStorage[user_id]['guessed_ans']) == 6:
                    # если все отгаданы, то заканчиваем игру
                    res['response']['text'] = 'Ты отгадал всех, поздравсляю! Твой счет: ' + str(score)
                    res['end_session'] = True
                    res['response']['buttons'] = [
                        {
                            'title': 'Спасибо за игру',
                            'hide': True
                        }
                    ]
                else:
                    # если есть неотгаданные варианты, то продолжаем игру
                    sessionStorage[user_id]['game_started'] = True
                    # номер попытки, чтобы показывать фото по порядку
                    sessionStorage[user_id]['attempt'] = 1
                    # функция, которая выбирает вариант для игры и показывает фото
                    play_game(res, req)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['end_session'] = True
            # описание функции с пощью игроку и показа очков
            elif 'ответом' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Здесь будет помощь, но она стоит 25 оч. \n Твой счет: ' + str(score)
                res['end_session'] = True
            elif 'игру' in req['request']['nlu']['tokens']:
                res['response']['text'] = ':)'
            else:
                res['response']['text'] = 'Не поняла ответа! Так да или нет?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                        'title': 'Помощь с ответом',
                        'hide': True
                    }
                ]
        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if attempt == 1:
        # если попытка первая, то случайным образом выбираем вариант для гадания
        name = random.choice(list(ans))
        # выбираем его до тех пор пока не выбираем варниант, которого нет в sessionStorage[user_id]['guessed_ans']
        while name in sessionStorage[user_id]['guessed_ans']:
            name = random.choice(list(ans))
        # записываем город в информацию о пользователе
        sessionStorage[user_id]['ans'] = name
        # добавляем в ответ картинку
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Как его зовут?'
        res['response']['card']['image_id'] = ans[name][attempt - 1]
        res['response']['text'] = 'Тогда сыграем!'
        res['response']['buttons'] = [
                    {
                        'title': 'Помощь с ответом',
                        'hide': True
                    }]
    elif 'ответом' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ваш счет: ' + str(score) + '\n' + sessionStorage[user_id]['ans']
                sett('help')
                res['end_session'] = True
    else:
        # сюда попадаем, если попытка отгадать не первая
        name = sessionStorage[user_id]['ans']
        # проверяем есть ли правильный ответ в сообщение
        if get_name(req) is not None and get_name(req) in name:
            sett('ok1')
            # если да, то добавляем город к sessionStorage[user_id]['guessed_cities'] и
            # отправляем пользователя на второй круг. Обратите внимание на этот шаг на схеме.
            res['response']['text'] = 'Правильно! Сыграем ещё?'
            sessionStorage[user_id]['guessed_ans'].append(name)
            sessionStorage[user_id]['game_started'] = False
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': 'Помощь с ответом',
                    'hide': True
                }
            ]
            return

        else:
            # если нет
            if attempt == 3:
                # если попытка третья, то значит, что все картинки мы показали.
                # В этом случае говорим ответ пользователю,
                # добавляем город к sessionStorage[user_id]['guessed_cities'] и отправляем его на второй круг.
                # Обратите внимание на этот шаг на схеме.
                res['response']['text'] = f'Вы пытались. Это {name.title()}. Сыграем ещё?'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_ans'].append(name)
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                        'title': 'Помощь с ответом',
                        'hide': True
                    }
                ]
                return
            else:
                # иначе показываем следующую картинку
                sett('ok2')
                res['response']['text'] = 'А если я покажу описание? \n' + ans[name][1]
                res['response']['buttons'] = [
                    {
                        'title': 'Помощь с ответом',
                        'hide': True
                    }]
    # увеличиваем номер попытки доля следующего шага
    sessionStorage[user_id]['attempt'] += 1


def get_name(req):
    for i in req['request']['nlu']['entities']:
        if i['type'] == 'YANDEX.FIO':
            if 'first_name' in i['value']:
                return i['value'].get('first_name', None)
            elif 'last_name' in i['value']:
                return i['value'].get('last_name', None)
        else:
            return None


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
