from kannabot.presentation import send_reply
"""Detection does not sanction; only an explicit authorized decision may do so."""
import re
from kannabot.presentation import context
from functools import partial
from html import escape
from types import SimpleNamespace
from kannabot.interacoes import Seen
from kannabot.moderation import Result
from kannabot.permissions import PermissionDenied

class Review:
    def __init__(self,moderation,store,audit):
        self.moderation,self.store,self.audit=moderation,store,audit
        self.notified=Seen(ttl=60)
    def observe(self,detections):
        for detection in detections:
            try:
                id,created=self.store.put(detection)
                if created and self.notified.claim((detection.chat_id,detection.user_id)):
                    self.audit.record(detection.chat_id,None,detection.user_id,"review_pending",f"Detecção {id}; {detection.rule}; use /detections para revisar","done")
            except Exception as error:
                self.audit.record(detection.chat_id,None,detection.user_id,"review_storage","Falha ao registrar detecção","failed",error)
    def guard(self,message):
        if getattr(self.moderation,"roles",None) is not None:
            return self.moderation.permissions.actor(message,"review")
        return self.moderation.permissions.actor(message)
    def handle(self,command,message):
        actor,context_data=context(message);target=None;reason="";error=None
        try:
            actor=self.guard(message)
            arguments=message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1))>1 else ""
            if command=="detections":
                rows=self.store.pending(message.chat.id)
                text="\n".join(f"ID {id} | mensagem {msg} | membro {user} | {rules}" for id,msg,user,rules in rows)
                result=Result("done","🔎 Detecções pendentes de revisão\n"+escape(text)+"\nNenhuma punição foi aplicada automaticamente." if text else "🔎 Nenhuma detecção pendente.")
            else:
                parts=arguments.split(maxsplit=1)
                if len(parts)!=2 or not parts[0].isdigit():raise ValueError("Informe ID e decisão/motivo.")
                id=int(parts[0]);row=self.store.get(message.chat.id,id)
                if not row or row["status"]!="pending":raise ValueError("Detecção inexistente ou já processada neste grupo.")
                target=row["user"]
                if command=="dismiss":
                    reason=self.audit.clean(parts[1])
                    if not reason.strip():raise ValueError("Motivo obrigatório.")
                    if not self.store.reserve(message.chat.id,id,actor):raise ValueError("Detecção já reservada.")
                    self.store.finish(message.chat.id,id,actor,"dismissed",reason,status="dismissed")
                    result=Result("done",f"✅ Detecção #{id} descartada.\nMotivo: {escape(reason)}\nNenhuma sanção foi aplicada.")
                else:
                    decision=parts[1].split(maxsplit=1)
                    if len(decision)!=2 or decision[0] not in ("warn","delete","mute","ban"):
                        raise ValueError("Use /review ID warn|delete|mute|ban argumentos.")
                    action,payload=decision
                    code_parts=payload.split()
                    code=code_parts[1] if action=="mute" and len(code_parts)>1 else code_parts[0]
                    if not re.fullmatch(r"R[0-9]{2,4}",code):raise ValueError("A revisão requer um código de regra.")
                    catalog=getattr(self.moderation,"governance",None)
                    if catalog is None:raise ValueError("Catálogo ainda indisponível; revisão não aplica sanção.")
                    rule=catalog.rule(message.chat.id,code)
                    if not rule or not rule["active"]:raise ValueError("Regra inexistente ou revogada.")
                    self.guard(message)
                    if not self.store.reserve(message.chat.id,id,actor):raise ValueError("Detecção já reservada.")
                    # Source identities come from the persisted event, never callback/user arguments.
                    synthetic=SimpleNamespace(chat=message.chat,from_user=message.from_user,sender_chat=getattr(message,"sender_chat",None),
                        message_id=message.message_id,text=f"/{action} {payload}",
                        reply_to_message=SimpleNamespace(chat=message.chat,message_id=row["message"],sender_chat=None,from_user=SimpleNamespace(id=target,is_bot=False)))
                    result=self.moderation.handle(action,synthetic)
                    reason=self.audit.clean(f"Revisão {id}: {action} {code}")
                    if not self.store.finish(message.chat.id,id,actor,result.outcome,reason):raise RuntimeError("Review completion not recorded")
        except (PermissionDenied,ValueError) as exc:
            result=Result("refused",str(exc))
        except Exception as exc:
            error=exc;result=Result("failed","Não foi possível concluir a revisão; não haverá repetição automática.")
        self.audit.record(message.chat.id,actor,target,command,reason,result.outcome,error,metadata=context_data)
        return result

def register(bot,service):
    def handle(command,message):
        result=service.handle(command,message)
        try:send_reply(bot,message.chat.id,result.message)
        except Exception:service.audit.record(message.chat.id,None,None,"review_feedback","Falha de retorno","failed")
    for command in ("detections","dismiss","review"):
        bot.message_handler(commands=[command])(partial(handle,command))
