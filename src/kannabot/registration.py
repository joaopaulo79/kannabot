"""Owner-confirmed pairing of a moderated group and its private log group."""
from datetime import datetime, timezone
from secrets import token_urlsafe
from time import time
import re
from kannabot import database
from kannabot.group_registry import RegistrationError


class Registration:
    def __init__(self, bot, registry, audit, registrars=(), legacy=(), clock=time, legacy_log=None, operators=()):
        self.bot,self.registry,self.audit=bot,registry,audit
        self.operators=frozenset(operators)
        self.registrars=frozenset(registrars) | self.operators
        self.legacy=frozenset(legacy)
        self.clock=clock
        self.legacy_log=legacy_log

    def actor(self, message):
        user=getattr(message,"from_user",None)
        if (getattr(message,"sender_chat",None) is not None or user is None
                or getattr(user,"is_bot",False) or type(getattr(user,"id",None)) is not int):
            raise RegistrationError("🛡️ Use sua conta pessoal, sem enviar em nome do grupo.")
        if user.id not in self.registrars:
            raise RegistrationError("🛡️ Sua conta não está autorizada a cadastrar grupos nesta instalação. Consulte o responsável pela Kanna.")
        if getattr(message.chat,"type",None) not in ("group","supergroup"):
            raise RegistrationError("Use este comando no grupo que deseja configurar, não em conversa privada ou canal.")
        return user.id

    def member(self, chat, user):
        try:return self.bot.get_chat_member(chat,user)
        except Exception:
            raise RegistrationError("Não consegui confirmar os cargos no Telegram. Nenhum cadastro foi alterado; tente novamente.") from None

    def check_source(self, chat, actor):
        actor_member=self.member(chat,actor)
        present=actor_member.status in ("creator","administrator","member") or (actor_member.status=="restricted" and getattr(actor_member,"is_member",False) is True)
        if not present:
            raise RegistrationError("🛡️ O responsável pelo cadastro precisa ser membro identificado deste grupo.")
        if actor_member.status!="creator" and actor not in self.operators:
            raise RegistrationError("🛡️ Somente o Dono real do grupo ou um Operador configurado na instalação pode concluir o cadastro.")
        try:bot_id=self.bot.get_me().id
        except Exception:raise RegistrationError("Não consegui confirmar a identidade da Kanna. Tente novamente.") from None
        member=self.member(chat,bot_id)
        if (member.status!="administrator" or getattr(member,"can_delete_messages",False) is not True
                or getattr(member,"can_restrict_members",False) is not True):
            raise RegistrationError("🛡️ Torne a Kanna administradora com permissões para apagar mensagens e restringir membros antes de cadastrar.")

    def check_destination(self, destination, actor):
        try:
            chat=self.bot.get_chat(destination)
            bot_id=self.bot.get_me().id
        except Exception:raise RegistrationError("Não consegui verificar o grupo de logs. Confira se a Kanna está nele e tente novamente.") from None
        if (chat.type not in ("group","supergroup") or getattr(chat,"username",None)
                or getattr(chat,"active_usernames",None)):
            raise RegistrationError("🔒 O destino de logs precisa ser um grupo privado, sem username público.")
        if self.member(destination,actor).status not in ("creator","administrator"):
            raise RegistrationError("🛡️ Você precisa ser administrador do grupo privado de logs.")
        if self.member(destination,bot_id).status!="administrator":
            raise RegistrationError("🛡️ Adicione a Kanna como administradora do grupo privado de logs para permitir a entrega dos registros.")

    def handle(self, command, message):
        user=getattr(message,"from_user",None)
        actor=getattr(user,"id",None) if getattr(message,"sender_chat",None) is None else None
        if type(actor) is not int:actor=None
        outcome="refused"
        try:
            actor=self.actor(message)
            args=(getattr(message,"text","") or "").split()[1:]
            if command=="cadastrar_logs":
                if args:raise RegistrationError("Use /cadastrar_logs sem argumentos no grupo privado de logs.")
                self.check_destination(message.chat.id,actor)
                if message.chat.id in self.legacy:
                    raise RegistrationError("Este chat já é um grupo moderado. Escolha um grupo privado separado para os logs.")
                token=token_urlsafe(24)
                self.registry.issue(token,actor,message.chat.id,self.clock())
                outcome="done"
                text=("🔒 Grupo de logs preparado.\n\nNo grupo principal, envie com esta mesma conta:\n"
                      +"/cadastrar_grupo "+token+"\n\nO código vale por 10 minutos e só você pode usá-lo. "
                      "Você precisa ser o Dono do grupo principal ou Operador autorizado da Kanna. Não há IDs para copiar.")
            elif command=="cadastrar_grupo":
                self.check_source(message.chat.id,actor)
                if message.chat.id==self.legacy_log and self.legacy:
                    raise RegistrationError("Este chat recebe logs de um grupo legado. Use o comando no grupo principal.")
                if self.registry.get(message.chat.id):
                    text="✅ Este grupo já está cadastrado e vinculado ao seu chat de logs. Nenhuma configuração foi alterada."
                    outcome="done"
                else:
                    if len(args)!=1 or not re.fullmatch(r"[A-Za-z0-9_-]{32}",args[0]):
                        raise RegistrationError("Primeiro use /cadastrar_logs no grupo privado de logs. Depois use /cadastrar_grupo CODIGO aqui, com a mesma conta.")
                    destination=self.registry.ticket(args[0],actor,self.clock())
                    if destination==message.chat.id or destination in self.legacy:
                        raise RegistrationError("O grupo principal e o grupo privado de logs precisam ser distintos.")
                    if destination==self.legacy_log and any(chat!=message.chat.id for chat in self.legacy):
                        raise RegistrationError("Este destino já atende outro grupo legado. Prepare um grupo privado de logs exclusivo.")
                    self.check_destination(destination,actor)
                    self.check_source(message.chat.id,actor)
                    created=self.registry.activate(message.chat.id,destination,actor,args[0],self.clock(),datetime.now(timezone.utc).isoformat())
                    outcome="done"
                    text=("✅ Grupo cadastrado e chat de logs vinculado. 🐉\nO Dono ou Operador já pode importar as regras com /rules_import e configurar os cargos internos."
                          if created else "✅ Este grupo já está cadastrado. Nenhuma configuração foi alterada.")
            else:raise RegistrationError("Comando de cadastro desconhecido.")
        except RegistrationError as error:
            text=str(error)
        except database.Error:
            outcome="uncertain"
            text="⚠️ Não consegui confirmar o cadastro no banco. Tente novamente para conferir o estado; um vínculo já concluído não será duplicado."
        except Exception:
            outcome="failed"
            text="⚠️ Não consegui confirmar o cadastro. Nenhuma nova ativação foi confirmada; tente novamente."
        user=getattr(message,"from_user",None)
        metadata={"origin":"human","actor_username":getattr(user,"username",None),
                  "chat_title":getattr(message.chat,"title",None),"detail":text if command!="cadastrar_logs" or outcome!="done" else "Código de vinculação emitido; argumento omitido por segurança."}
        # Never include the ticket or raw command in audit, including failure paths.
        self.audit.record(message.chat.id,actor,None,command,"Cadastro de grupo e logs",outcome,metadata=metadata)
        return text


def register(bot, service):
    for command in ("cadastrar_logs","cadastrar_grupo"):
        def handle(message, command=command):
            text=service.handle(command,message)
            bot.send_message(message.chat.id,text)
        bot.message_handler(commands=[command])(handle)
