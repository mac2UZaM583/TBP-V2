from settings__ import files_content

import telebot

def s_send_n(msg):
    try:
        telebot.TeleBot(
            files_content['TB_API']
        ).send_message(
            files_content['TB_ID'], 
            msg
        )
    except:
        pass