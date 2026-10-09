"""Explicit human commands for assignments, catalogs and cancellations."""
import json
from functools import partial
from html import escape
from pathlib import Path
from kannabot.moderation import Result
from kannabot.permissions import PermissionDenied

COMMANDS=("role","role_remove","rules_import","rule_set","rule_disable","catalog","unwarn")

class Administration:
    def __init__(self,moderation,store,roles,audit):
        self.moderation,self.store,self.roles,self.audit=moderation,store,roles,audit
    def handle(self,command,message):
        actor=target=None;reason="";error=None
        try:
            action="roles" if command in ("role","role_remove","rule_set","rule_disable","rules_import") else "unwarn" if command=="unwarn" else "catalog"
            actor=self.moderation.permissions.actor(message,action)
            argument=message.text.split(maxsplit=1)[1].strip() if len(message.text.split(maxsplit=1))>1 else ""
            if command in ("role","role_remove"):
                _,target=self.moderation.reply_target(message)
                self.roles.assign(message.chat.id,actor,target,argument if command=="role" else "member")
                reason="Atribuição "+(argument if command=="role" else "member")
                result=Result("done","Cargo interno atualizado.")
            elif command=="rule_set":
                rule=json.loads(argument)
                if isinstance(rule,dict):
                    for key in ("name","description"):
                        if isinstance(rule.get(key),str):rule[key]=self.audit.clean(rule[key])
                version=self.store.put_rule(message.chat.id,rule,actor)
                result=Result("done",f"Regra salva na versão {version}.")
                reason="Cadastro/edição de regra"
            elif command=="rule_disable":
                rule=self.store.rule(message.chat.id,argument)
                if not rule:raise ValueError("Regra inexistente.")
                del rule["version"];rule["active"]=False
                self.store.put_rule(message.chat.id,rule,actor)
                result=Result("done","Regra revogada; histórico preservado.")
            elif command=="rules_import":
                rules=json.loads((Path(__file__).parent/"resources/rules_initial.json").read_text(encoding="utf-8"))
                for rule in rules:
                    if self.store.rule(message.chat.id,rule["code"]) is None:self.store.put_rule(message.chat.id,rule,actor)
                result=Result("done","Catálogo inicial importado; regras existentes preservadas. Condições pendentes não foram presumidas.")
            elif command=="unwarn":
                parts=argument.split(maxsplit=1)
                if len(parts)!=2 or not parts[0].isdigit():raise ValueError("Use /unwarn ID motivo.")
                row=self.store.infraction(message.chat.id,int(parts[0]))
                if not row:raise ValueError("Infração inexistente neste grupo.")
                target=row[0];self.roles.target(message.chat.id,actor,target)
                reason=self.audit.clean(parts[1])
                if not reason.strip():raise ValueError("Motivo obrigatório.")
                changed=self.store.cancel(message.chat.id,int(parts[0]),actor,reason)
                result=Result("done","Advertência cancelada; histórico preservado.") if changed else Result("refused","Advertência já cancelada.")
            else:
                rules=[self.store.rule(message.chat.id,argument)] if argument else self.store.catalog(message.chat.id)
                if not rules or any(rule is None for rule in rules):raise ValueError("Catálogo vazio ou regra inexistente.")
                text="\n".join(f"{rule['code']} v{rule['version']} | {rule['name'][:80]} | {rule['level']} | peso {rule['weight']} | {'ativa' if rule['active'] else 'revogada'}" for rule in rules[:20])
                result=Result("done",escape(text))
        except (PermissionDenied,ValueError,TypeError) as exc:
            result=Result("refused",self.audit.clean(str(exc)))
        except Exception as exc:
            error=exc;result=Result("failed","Não foi possível concluir a administração.")
        self.audit.record(message.chat.id,actor,target,command,reason,result.outcome,error,metadata=self.roles.metadata(message.chat.id,actor,target))
        return result

def register(bot,service):
    def handle(command,message):
        result=service.handle(command,message)
        try:bot.send_message(message.chat.id,result.message,parse_mode="HTML")
        except Exception:service.audit.record(message.chat.id,None,None,"admin_feedback","Falha de retorno","failed")
    for command in COMMANDS:bot.message_handler(commands=[command])(partial(handle,command))
