from settings__ import files_content

from loguru import logger
import io
import telebot

bot = telebot.TeleBot(files_content['TB_API'])

def log_decorator(func):
    def wrapper(*args):
        logger.remove()
        logger.add(
            'log.log', 
            format="{time} {level} {message}",
            level='TRACE',
            enqueue=True,
            backtrace=True,
            mode='w',
            encoding='utf-8'
        )
        logger.info(f"Вызов функции {func.__name__} с аргументами: {args}")
        with logger.catch():
            try:
                result = func(*args)
                logger.info(f"Функция {func.__name__} вернула: {result}")
                return result
            except:
                logger.exception(f"Произошла ошибка в функции {func.__name__}")
                with open('log.log', 'r', encoding='utf-8') as f:
                    v = f.read()
                bot.send_message(files_content['TB_ID'], v)
    return wrapper  

def send_n(msg):
    try:
        bot.send_message(files_content['TB_ID'], msg)
    except:
        pass

if __name__ == '__main__':
    @log_decorator
    def func(v, v_):
        try:
            value = (v + v_) / 0
        except:
            raise

    func(1, 2)