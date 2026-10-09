from collections import OrderedDict
from functools import partial
from html import escape
from threading import RLock
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

class Emotes:
    def __init__(self,bot,config):
        self.bot,self.config=bot,config
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
        if target is None and target_user:
            target='@'+escape(target_user.username or str(target_user.id))
        target_id=target_user.id if target_user else None
        if target_id is None and target:
            with self.lock:target_id=self.known.get((message.chat.id,target.lstrip('@').casefold()))
        actions=Construcao_Acoes(self.bot,msg,Abrir_Arquivos_Emotes())
        # Capture the message ID returned by send_animation for callback context.
        owner=message.from_user.id
        class Sender:
            def send_animation(inner,*args,**kwargs):
                sent=self.bot.send_animation(*args,**kwargs)
                markup=kwargs.get('reply_markup')
                if markup:
                    buttons={b.callback_data for row in markup.keyboard for b in row}
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
                status=''
        except Exception:status='Não foi possível concluir a interação.'
        finally:
            try:self.bot.answer_callback_query(call.id,text=status)
            except Exception:pass

def register(bot,config,state_dir):
    service=Emotes(bot,config)
    for command in COMMANDS:
        bot.message_handler(commands=[command])(partial(service.command,command))
    bot.callback_query_handler(func=lambda call:True)(service.callback)
    return service
