from functools import partial

COMMANDS = ("warn", "warnings", "delete", "mute", "kick", "ban", "unban")

def register(bot, service):
    def handle(command, message):
        result = service.handle(command, message)
        try:
            bot.send_message(message.chat.id, result.message, parse_mode="HTML")
        except Exception:
            service.audit.record(message.chat.id, None, None, "command_feedback", "Falha no retorno", "failed")
    for command in COMMANDS:
        bot.message_handler(commands=[command])(partial(handle, command))
