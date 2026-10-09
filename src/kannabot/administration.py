from kannabot.presentation import send_reply
"""Explicit human commands for assignments, catalogs and cancellations."""
import json
from kannabot.presentation import context, mention, user_mention, rule_text, ROLE_NAMES
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
        actor,context_data=context(message);target=None;reason="";error=None
        try:
            action="roles" if command in ("role","role_remove","rule_set","rule_disable","rules_import") else "unwarn" if command=="unwarn" else "catalog"
            actor=self.moderation.permissions.actor(message,action)
            if command in ("role","role_remove","unwarn") and self.moderation.identities is not None:
                message=self.moderation.identities.prepare(message,command)
            argument=message.text.split(maxsplit=1)[1].strip() if len(message.text.split(maxsplit=1))>1 else ""
            if command in ("role","role_remove"):
                _,target=self.moderation.reply_target(message)
                previous=self.roles.role(message.chat.id,target)
                self.roles.assign(message.chat.id,actor,target,argument if command=="role" else "member")
                reason="Atribuição "+(argument if command=="role" else "member")
                result=Result("done",f"🛡️ Cargo interno de {user_mention(message.reply_to_message.from_user)} atualizado!\nCargo anterior: {ROLE_NAMES[previous]}\nCargo atual: {ROLE_NAMES[argument if command=='role' else 'member']}.")
            elif command=="rule_set":
                rule=json.loads(argument)
                if isinstance(rule,dict):
                    for key in ("name","description","summary"):
                        if isinstance(rule.get(key),str):rule[key]=self.audit.clean(rule[key],limit=4000)
                version=self.store.put_rule(message.chat.id,rule,actor)
                result=Result("done",f"📚 Regra {rule['code']} salva na versão {version}. Histórico anterior preservado.")
                reason="Cadastro/edição de regra"
            elif command=="rule_disable":
                rule=self.store.rule(message.chat.id,argument)
                if not rule:raise ValueError("Regra inexistente.")
                del rule["version"];rule["active"]=False
                self.store.put_rule(message.chat.id,rule,actor)
                result=Result("done",f"📚 Regra {argument} revogada para novas aplicações. Histórico preservado.")
            elif command=="rules_import":
                rules=json.loads((Path(__file__).parent/"resources/rules_initial.json").read_text(encoding="utf-8"))
                if argument not in ("","atualizar"):raise ValueError("Use /rules_import ou /rules_import atualizar.")
                created=updated=preserved=0
                for rule in rules:
                    existing=self.store.rule(message.chat.id,rule["code"])
                    if existing is None:
                        self.store.put_rule(message.chat.id,rule,actor);created+=1
                    elif argument=="atualizar" and existing["description"]==f"Referência ao livro de regras fornecido pelo Dono: {existing['name']}. Aplicação depende de avaliação humana; exceções exigem decisão explícita." and all(existing[key]==rule[key] for key in ("name","level","weight","active","actions")):
                        self.store.put_rule(message.chat.id,rule,actor);updated+=1
                    else:preserved+=1
                result=Result("done",f"📚 Catálogo atualizado!\nNovas regras: {created}.\nRedações genéricas atualizadas: {updated}.\nRegras existentes preservadas: {preserved}.\nCondições pendentes não foram presumidas.")
            elif command=="unwarn":
                parts=argument.split(maxsplit=1)
                if len(parts)!=2 or not parts[0].isdigit():raise ValueError("Use /unwarn ID motivo.")
                row=self.store.infraction(message.chat.id,int(parts[0]))
                if not row:raise ValueError("Infração inexistente neste grupo.")
                target=row[0]
                supplied=getattr(getattr(message,"reply_to_message",None),"from_user",None)
                if supplied is not None and supplied.id!=target:raise ValueError("A advertência não pertence ao alvo indicado.")
                self.roles.target(message.chat.id,actor,target)
                reason=self.audit.clean(parts[1])
                if not reason.strip():raise ValueError("Motivo obrigatório.")
                changed=self.store.cancel(message.chat.id,int(parts[0]),actor,reason)
                result=Result("done",f"✅ Advertência #{parts[0]} cancelada!\nAlvo: {mention(target)}\nMotivo: {escape(reason)}\nSituação atual: {self.store.history(message.chat.id,target)[0]} advertência(s) válida(s) · {self.store.points(message.chat.id,target)} pontos.\nHistórico preservado.") if changed else Result("refused","Advertência já cancelada.")
            else:
                rules=[self.store.rule(message.chat.id,argument)] if argument else self.store.catalog(message.chat.id)
                if not rules or any(rule is None for rule in rules):raise ValueError("Catálogo vazio ou regra inexistente.")
                text="\n".join(f"{rule['code']} v{rule['version']} | {rule['name'][:80]} | {rule['level']} | peso {rule['weight']} | {'ativa' if rule['active'] else 'revogada'}" for rule in rules[:20])
                result=Result("done",rule_text(rules[0]) if argument else "📚 Catálogo de regras\n"+escape(text)+"\nUse /catalog R10 para consultar os detalhes.")
        except (PermissionDenied,ValueError,TypeError) as exc:
            result=Result("refused",self.audit.clean(str(exc)))
        except Exception as exc:
            error=exc;result=Result("failed","Não foi possível concluir a administração.")
        self.audit.record(message.chat.id,actor,target,command,reason,result.outcome,error,metadata={**context_data,**self.roles.metadata(message.chat.id,actor,target)})
        return result

def register(bot,service):
    def handle(command,message):
        result=service.handle(command,message)
        try:send_reply(bot,message.chat.id,result.message)
        except Exception:service.audit.record(message.chat.id,None,None,"admin_feedback","Falha de retorno","failed")
    for command in COMMANDS:bot.message_handler(commands=[command])(partial(handle,command))
