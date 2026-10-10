from kannabot.presentation import send_reply
from functools import partial

COMMANDS = ("warn", "warnings", "delete", "mute", "kick", "ban", "unban", "delwarn")

def register(bot, service):
    def handle(command, message):
        result = service.handle(command, message)
        try:
            send_reply(bot,message.chat.id,result.message)
        except Exception:
            service.audit.record(message.chat.id, None, None, "command_feedback", "Falha no retorno", "failed")
    for command in COMMANDS:
        bot.message_handler(commands=[command])(partial(handle, command))
