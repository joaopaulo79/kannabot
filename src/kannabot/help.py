"""Bounded, role-aware help navigation. No moderation effects."""
from collections import OrderedDict
from dataclasses import dataclass, field
from html import escape
from secrets import token_urlsafe
from threading import RLock
from time import monotonic
from types import SimpleNamespace
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from kannabot.governance import CAPABILITIES
from kannabot.moderation import Result
from kannabot.permissions import PermissionDenied
from kannabot.presentation import ROLE_NAMES, context

# capability, category, title, example, purpose, expected, constraints
PAGES = {
 'warn':('warn','warnings','⚠️ Aplicar advertência','/warn R10 envio repetido de figurinhas',
    'Registra uma advertência no histórico do alvo. Não apaga a mensagem.',
    'Com regra, aplica o peso do catálogo. /warn motivo registra advertência manual sem peso definido, sem acrescentar pontos. Mostra registro e saldo atual.',
    'Responda à mensagem do alvo ou use /warn @usuario R10 motivo. A hierarquia é respeitada; o limite de pontos exige revisão humana, sem ban automático.'),
 'warnings':('warnings','warnings','📋 Consultar histórico','/warnings @usuario',
    'Consulta advertências do alvo, incluindo cancelamentos.',
    'Mostra advertências válidas, pontos, motivos, regras e números de registro.',
    'Também funciona em resposta à mensagem do alvo. Use o registro para identificar uma advertência.'),
 'unwarn':('unwarn','warnings','↩️ Cancelar advertência','/unwarn 2 advertência aplicada por engano',
    'Cancela uma advertência pelo número do registro.',
    'Ela deixa de contar no saldo e nos pontos. Histórico e motivo do cancelamento permanecem.',
    'Admin/Dono, respeitando a hierarquia. Alvo opcional por resposta ou @username para conferir o registro.'),
 'delete':('delete','messages','🧹 Apagar mensagem','/delete conteúdo fora do assunto',
    'Apaga uma mensagem específica, sem adicionar advertência.',
    'Exclusão confirmada, ação no log e evidência disponível preservada.',
    'Responda à mensagem que deseja apagar. @username não identifica qual mensagem excluir. Motivo obrigatório.'),
 'delwarn':(('warn','delete'),'messages','🧹⚠️ Apagar e advertir','/delwarn R10 envio repetido de figurinhas',
    'Apaga a mensagem respondida e registra advertência no alvo.',
    'Mostra exclusão, registro e saldo. /delwarn motivo usa advertência manual sem peso; não acrescenta pontos.',
    'Sempre responda à mensagem. Falha de armazenamento impede o efeito. Uma advertência pode ser registrada mesmo se a exclusão falhar: confira resultado parcial/incerto antes de repetir.'),
 'mute':('mute','silence','🔇 Silenciar temporariamente','/mute @usuario 10m insistência após orientação',
    'Impede o alvo de enviar mensagens pelo prazo informado.',
    'Silenciamento temporário. Não apaga a mensagem nem acrescenta advertência.',
    'Pode usar resposta. 10m = 10 minutos, 2h = 2 horas, 1d = 1 dia; mínimo 1 minuto e máximo 365 dias. Requer supergrupo, hierarquia e direitos do bot. Administradores nativos não são rebaixados automaticamente.'),
 'kick':('kick','bans','🚪 Expulsar','/kick @usuario motivo da expulsão',
    'Remove o alvo do grupo, permitindo retorno voluntário.',
    'O alvo é removido; pode voltar se tiver acesso ao grupo.',
    'Admin/Dono, hierarquia e supergrupo. Pode usar resposta. Não confundir expulsão com banimento.'),
 'ban':('ban','bans','⛔ Banir','/ban @usuario motivo do banimento',
    'Bane o alvo sem prazo definido.',
    'Ban confirmado revoga o cargo interno do alvo. Ação registrada no log.',
    'Admin pode banir Mod/Membro, nunca Admin/Dono. Dono respeita limites nativos do Telegram. Pode usar resposta; nenhum administrador nativo é rebaixado automaticamente.'),
 'unban':('unban','bans','✅ Remover banimento','/unban @usuario motivo da liberação',
    'Libera o retorno voluntário de um alvo banido.',
    'Não adiciona a pessoa ao grupo nem restaura cargo interno.',
    'Admin/Dono e supergrupo. Pode usar resposta; username requer identidade conhecida e confirmada.'),
 'role':('roles','roles','🛡️ Atribuir cargo','/role @usuario mod',
    'Atribui um cargo interno da Kanna ao alvo.',
    'Permissões passam a seguir o novo cargo. Não muda título cosmético ou poderes nativos do Telegram.',
    'Admin gere apenas Mod. Dono também pode atribuir Admin com /role @usuario admin. Pode usar resposta; Dono real não é atribuído por comando.'),
 'role_remove':('roles','roles','🛡️ Remover cargo','/role_remove @usuario',
    'Remove o cargo interno do alvo, tornando-o Membro.',
    'Acesso administrativo interno é revogado, sem alterar cargo nativo.',
    'Admin remove Mod; Dono pode remover Admin/Mod. Pode usar resposta.'),
 'catalog':('catalog','rules','📚 Consultar regras','/catalog R10',
    'Consulta a regra completa, peso, versão, estado e condições.',
    'Apenas consulta. /catalog lista as regras; não aplica punições.',
    'Mod/Admin/Dono. Regra revogada ou condição pendente não autoriza aplicação automática.'),
 'rules_import':('rules','rules','📚 Importar catálogo','/rules_import atualizar',
    'Importa regras ausentes e, com atualizar, substitui redações reconhecidas como genéricas.',
    'Preserva regras personalizadas e versões históricas. /rules_import sem argumento importa apenas ausentes.',
    'Somente Dono. Não presume condições ainda não definidas nem aplica punições.'),
 'rule_set':('rules','rules','📚 Criar versão de regra','/rule_set JSON',
    'Cria uma nova versão de uma regra.',
    'Novas aplicações usam a versão atual; advertências anteriores mantêm a versão aplicada.',
    'Somente Dono. JSON requer code, name, description, level, weight, active e actions; summary é opcional. Use o catálogo para conferir os dados antes de alterar.'),
 'rule_disable':('rules','rules','📚 Revogar regra','/rule_disable R10',
    'Revoga uma regra para novas aplicações.',
    'Histórico preservado; advertências já registradas não são canceladas por este comando.',
    'Somente Dono. Revogar não é apagar registros.'),
 'detections':('review','review','🔎 Consultar detecções','/detections',
    'Lista detecções pendentes de revisão humana.',
    'Mostra IDs, alvos e mensagens relacionadas. Não aplica punição.',
    'Use o ID da detecção em /dismiss ou /review; não é o registro de advertência.'),
 'dismiss':('review','review','🔎 Descartar detecção','/dismiss 2 falso positivo',
    'Descarta a detecção pelo ID com motivo explícito.',
    'A detecção sai das pendentes, sem sancionar o alvo.',
    'ID e motivo obrigatórios; somente detecção pendente deste grupo.'),
 'review':('review','review','🔎 Decidir sobre detecção','/review 2 warn R10 motivo',
    'Aplica uma decisão explícita ao alvo da detecção registrada.',
    'Respeita regra, hierarquia e permissões da ação. /review 2 mute 1d R10 motivo para silenciar.',
    'Exige ID, ação, regra e argumentos; não aceita @username como substituto do ID. Ações disponíveis dependem do seu cargo.'),
}
CATEGORIES={'warnings':'⚠️ Advertências','messages':'🧹 Mensagens','silence':'🔇 Silenciamento','bans':'⛔ Banimentos','roles':'🛡️ Cargos','rules':'📚 Regras','review':'🔎 Revisão'}

@dataclass
class Session:
    owner: int
    chat: int
    message: int
    expires: float
    page: str = 'home'
    role: str = ''
    lock: RLock = field(default_factory=RLock)

class Help:
    def __init__(self,moderation,ttl=600,capacity=1000,clock=monotonic):
        self.moderation=moderation;self.ttl=ttl;self.capacity=capacity;self.clock=clock
        self.sessions=OrderedDict();self.lock=RLock()

    def role(self,message):
        actor=self.moderation.permissions.emote_actor(message)
        roles=self.moderation.roles
        if roles is None:raise PermissionDenied('Não foi possível confirmar seu cargo interno.')
        role=roles.role(message.chat.id,actor)
        if role not in ('owner','admin','mod'):raise PermissionDenied('🛡️ Esta ajuda é destinada ao Dono, Admin e Mod da Kanna.')
        return role

    def allowed(self,role):
        caps=CAPABILITIES[role]
        return {name:page for name,page in PAGES.items() if set(page[0] if isinstance(page[0],tuple) else (page[0],))<=caps}

    def render(self,role,page='home'):
        allowed=self.allowed(role)
        if page=='home':return (f'📖 <b>Ajuda da Kanna</b>\nSeu cargo neste grupo: <b>{ROLE_NAMES[role]}</b>\n\n'
            'Escolha o que deseja fazer. Vou mostrar como usar e o que esperar. 🐉\n\n'
            '🎯 Responda à mensagem do alvo ou use @username conhecido e confirmado.\n'
            '🧹 /delete e /delwarn exigem resposta à mensagem específica.\n\n'
            'Seu cargo na Kanna é independente do título/cargo no Telegram. Emotes continuam disponíveis para Membros.\n'
            'Se necessário, use /help@username_do_bot. Esta ajuda expira em 10 minutos; envie /help novamente.')
        if page.startswith('cat_'):
            category=page[4:]
            if not any(item[1]==category for item in allowed.values()):raise PermissionDenied('Essa categoria não está disponível para seu cargo.')
            return '<b>'+CATEGORIES[category]+'</b>\n\nEscolha um comando para ver exemplos e o resultado esperado.'
        if page not in allowed:raise PermissionDenied('Esse comando não está disponível para seu cargo.')
        item=allowed[page];notes=item[6]
        if page=='review':notes+=' Permitidas: '+', '.join(action for action in ('warn','delete','mute','ban') if action in CAPABILITIES[role])+'.'
        return f'<b>{escape(item[2])}</b>\n\n{escape(item[4])}\n\n<b>Como usar</b>\n<code>{escape(item[3])}</code>\n\n<b>O que esperar</b>\n{escape(item[5])}\n\n<b>Antes de usar</b>\n{escape(notes)}'

    def keyboard(self,role,page,token):
        allowed=self.allowed(role);keyboard=InlineKeyboardMarkup(row_width=2)
        def button(label,dest):return InlineKeyboardButton(label,callback_data=f'h:{token}:{dest}')
        if page=='home':
            for category,label in CATEGORIES.items():
                if any(item[1]==category for item in allowed.values()):keyboard.add(button(label,'cat_'+category))
        elif page.startswith('cat_'):
            for name,item in allowed.items():
                if item[1]==page[4:]:keyboard.add(button(item[2],name))
            keyboard.add(button('🏠 Início','home'))
        else:
            item=allowed[page];siblings=[name for name,p in allowed.items() if p[1]==item[1]];position=siblings.index(page)
            navigation=[]
            if position: navigation.append(button('⬅️ Anterior',siblings[position-1]))
            if position+1<len(siblings):navigation.append(button('Próximo ➡️',siblings[position+1]))
            if navigation:keyboard.add(*navigation)
            keyboard.add(button('⬅️ '+CATEGORIES[item[1]],'cat_'+item[1]),button('🏠 Início','home'))
        return keyboard

    def handle(self,message):
        actor,metadata=context(message);error=None
        try:
            role=self.role(message);metadata['actor_role']=role;result=Result('done',self.render(role))
        except (PermissionDenied,ValueError) as exc:result=Result('refused',escape(self.moderation.audit.clean(str(exc))))
        except Exception as exc:error=exc;result=Result('failed','Não foi possível consultar a ajuda agora.')
        self.moderation.audit.record(message.chat.id,actor,None,'help','Consulta de comandos',result.outcome,error,metadata=metadata)
        return result

    def expire(self):
        for token in list(self.sessions):
            if self.sessions[token].expires<=self.clock():del self.sessions[token]

    def open(self,message):
        bot=self.moderation.bot
        result=self.handle(message)
        if result.outcome!='done':bot.send_message(message.chat.id,result.message,parse_mode='HTML');return
        role=self.role(message);token=token_urlsafe(9)
        sent=bot.send_message(message.chat.id,self.render(role),parse_mode='HTML',reply_markup=self.keyboard(role,'home',token))
        if type(getattr(sent,'message_id',None)) is not int:raise ValueError('Mensagem da ajuda não confirmada.')
        with self.lock:
            self.expire();self.sessions[token]=Session(message.from_user.id,message.chat.id,sent.message_id,self.clock()+self.ttl,role=role)
            while len(self.sessions)>self.capacity:self.sessions.popitem(last=False)

    def callback(self,call):
        bot=self.moderation.bot;answer='';error=None
        try:
            data=getattr(call,'data','');parts=data.split(':')
            if len(parts)!=3 or parts[0]!='h':raise ValueError('Navegação inválida.')
            token,page=parts[1:]
            with self.lock:self.expire();session=self.sessions.get(token)
            if session is None:raise ValueError('Esta ajuda expirou. Envie /help novamente.')
            message=getattr(call,'message',None);user=getattr(call,'from_user',None)
            if message is None or user is None or (message.chat.id,message.message_id,user.id)!=(session.chat,session.message,session.owner):
                raise PermissionDenied('Abra sua própria ajuda com /help para navegar.')
            with session.lock:
                with self.lock:
                    self.expire()
                    if self.sessions.get(token) is not session:raise ValueError('Esta ajuda expirou. Envie /help novamente.')
                synthetic=SimpleNamespace(chat=message.chat,from_user=user,sender_chat=None)
                role=self.role(synthetic);text=self.render(role,page)
                if session.page!=page or session.role!=role:
                    bot.edit_message_text(text,chat_id=session.chat,message_id=session.message,parse_mode='HTML',reply_markup=self.keyboard(role,page,token))
                    session.page,session.role=page,role
        except (PermissionDenied,ValueError) as exc:answer=self.moderation.audit.clean(str(exc))
        except Exception as exc:error=exc;answer='Não consegui atualizar a ajuda. Tente novamente.'
        finally:
            try:bot.answer_callback_query(call.id,text=answer,show_alert=bool(answer))
            except Exception:pass
        if error:
            message=getattr(call,'message',None);user=getattr(call,'from_user',None)
            if message:self.moderation.audit.record(message.chat.id,getattr(user,'id',None),None,'help_feedback','Falha na navegação','failed',error)

def register(bot,service):
    @bot.message_handler(commands=['help'])
    def handle(message):
        try:service.open(message)
        except Exception as error:
            actor,metadata=context(message)
            service.moderation.audit.record(message.chat.id,actor,None,'help_feedback','Falha no retorno','failed',error,metadata=metadata)
    @bot.callback_query_handler(func=lambda call:isinstance(getattr(call,'data',None),str) and call.data.startswith('h:'))
    def navigate(call):service.callback(call)
