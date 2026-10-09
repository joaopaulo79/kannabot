from collections import OrderedDict
from kannabot.identities import Identities
from functools import partial
from html import escape
from threading import RLock
from telebot.apihelper import ApiTelegramException
from kannabot._config.mensagem_usuario import Mensagem_Usuario
from kannabot.emotes.construcao_acoes import Construcao_Acoes
from kannabot.emotes.open_json import Abrir_Arquivos_Emotes
from kannabot.permissions import Permissions, PermissionDenied
from kannabot.interacoes import Interactions

COMMANDS = "punch slap kiss shy hug cuddle pat push stare highfive poke bite lick bonk tickle wave cry".split()
CALLBACKS = {
 'Pedir_Desculpa_Punch':('Case_Punch_Me_Desculpa','owner'),
 'Devolver_Soco':('Case_Revida_Punch','target'),
 'Devolver_Tapa':('Case_Revida_Slap','target'),
 'Pedir_Desculpa_Slap':('Case_Slap_Me_Desculpa','owner'),
 'Rejeitar_Beijo':('Case_Rejeita_Kiss','target'), 'Aceitar_Beijo':('Case_Choque_Kiss','target'),
 'Aceitar_Abraço':('Case_Choque_Hug','target'), 'Rejeitar_Abraço':('Case_Rejeita_Hug','target'),
 'Aceitar_Carinho':('Case_Choque_Cuddle','target'), 'Rejeitar_Carinho':('Case_Rejeita_Cuddle','target'),
 'Aceitar_Cafuné':('Case_Choque_Pat','target'), 'Rejeitar_Cafuné':('Case_Rejeita_Pat','target'),
 'Aceitar_Toca_Aqui':('Case_Aceita_Highfive','target'), 'Rejeitar_Toca_Aqui':('Case_Rejeita_Highfive','target'),
 'Aceitar_Lambida':('Case_Revida_Lick','target'), 'Rejeitar_Lambida':('Case_Rejeita_Lick','target'),
 'Acenar_de_Volta':('Case_Devolve_Wave','target'), 'Cumprimentar':('Case_Welcome_Wave','other')}

class UnresolvedTarget(ValueError):
    pass

class ConfirmedSendFailure(RuntimeError):
    pass

class Emotes:
    def __init__(self,bot,config):
        self.bot,self.config=bot,config
        self.identities=None
        self.permissions=Permissions(bot,config.grupos_id)
        self.interactions=Interactions()
        self.known=OrderedDict();self.lock=RLock()
    def observe(self,message):
        with self.lock:
            for user in (getattr(message,'from_user',None),getattr(getattr(message,'reply_to_message',None),'from_user',None)):
                if user and user.username:
                    key=(message.chat.id,user.username.casefold());self.known[key]=user.id;self.known.move_to_end(key)
            while len(self.known)>1000:self.known.popitem(last=False)
    def command(self,command,message):
        if not self.permissions.authorized(message.chat.id):return
        try:self.permissions.emote_actor(message)
        except PermissionDenied:return
        self.observe(message)
        msg=Mensagem_Usuario();msg.Arguments(message)
        target=msg.Target()
        reply=getattr(message,'reply_to_message',None)
        target_user=getattr(reply,'from_user',None)
        target_id = None
        if target_user:
            reply_target = '@' + escape(target_user.username or str(target_user.id))
            if target is not None and target.casefold() != reply_target.casefold():
                self.bot.send_message(message.chat.id, 'O argumento e a resposta indicam pessoas diferentes. Use apenas a resposta à mensagem do alvo.')
                return
            target, target_id = reply_target, target_user.id
        elif target:
            with self.lock:
                target_id = self.known.get((message.chat.id, target.lstrip('@').casefold()))
            if self.identities is not None and target.casefold()!=self.config.bot_username.casefold():
                try:
                    resolved=self.identities.resolve(message.chat.id,target)
                    target_id=resolved.id
                    target="@"+escape(resolved.username)
                except ValueError as error:
                    self.bot.send_message(message.chat.id,str(error));return
        actions=Construcao_Acoes(self.bot,msg,Abrir_Arquivos_Emotes())
        # Capture the message ID returned by send_animation for callback context.
        owner=message.from_user.id
        class Sender:
            def send_animation(inner,*args,**kwargs):
                markup=kwargs.get('reply_markup')
                buttons={b.callback_data for row in markup.keyboard for b in row} if markup else set()
                if target_id is None and any(CALLBACKS.get(button, ('', 'target'))[1] == 'target' for button in buttons):
                    raise UnresolvedTarget()
                try:
                    sent=self.bot.send_animation(*args,**kwargs)
                except ApiTelegramException as error:
                    if error.error_code in (400, 403, 429):
                        raise ConfirmedSendFailure() from None
                    raise
                if markup:
                    self.interactions.put((message.chat.id,sent.message_id),dict(actions=actions,owner=owner,target=target_id,buttons=buttons,roles={k:CALLBACKS[k][1] for k in buttons if k in CALLBACKS}))
                return sent
        actions.bot=Sender();actions.Arguments(target or 'Vazio')
        name=command.capitalize()
        is_self=target_id==owner or target==f'@{msg.Username()}'
        if target is None or is_self:
            if command in ('shy','stare','wave','cry') or (is_self and command in ('punch','slap','kiss')):
                method='Case_Auto_'+name
            else:
                self.bot.send_message(message.chat.id,'Responda à mensagem do alvo ou informe @username.');return
        elif target.casefold()==self.config.bot_username.casefold():method='Case_'+name+'_Me'
        else:method='Case_'+name
        try:getattr(actions,method)()
        except UnresolvedTarget:
            self.bot.send_message(message.chat.id, 'Não foi possível identificar o alvo. Responda à mensagem da pessoa para usar este emote.')
        except Exception:self.bot.send_message(message.chat.id,'Não foi possível executar o emote.')
    def callback(self,call):
        status='Interação indisponível, expirada ou não autorizada.'
        try:
            if not getattr(call,'message',None) or not self.permissions.authorized(call.message.chat.id):return
            key=(call.message.chat.id,call.message.message_id)
            value=self.interactions.claim(key,call.from_user.id,call.data)
            if value and call.data in CALLBACKS:
                method=getattr(value['actions'],CALLBACKS[call.data][0])
                if call.data=='Cumprimentar':method(escape(call.from_user.username or str(call.from_user.id)))
                else:method()
                self.interactions.finish(key, call.from_user.id, value, success=True)
                status=''
        except ConfirmedSendFailure:
            self.interactions.finish(key, call.from_user.id, value, success=False)
            status='O envio foi recusado. Você pode tentar novamente.'
        except Exception:status='Resultado do envio não confirmado. A interação permanece bloqueada para evitar duplicidade.'
        finally:
            try:self.bot.answer_callback_query(call.id,text=status)
            except Exception:pass

def register(bot,config,state_dir):
    service=Emotes(bot,config)
    identities=getattr(bot,"kanna_identities",None)
    if isinstance(identities,Identities):service.identities=identities
    for command in COMMANDS:
        bot.message_handler(commands=[command])(partial(service.command,command))
    bot.callback_query_handler(func=lambda call:True)(service.callback)
    return service
