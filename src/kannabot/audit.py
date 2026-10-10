"""Moderation audit with sanitized local fallback and no action retries."""
import json
import logging
import re
from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path
from kannabot.presentation import mention, ROLE_NAMES, NATIVE_NAMES, ACTION_NAMES, OUTCOME_NAMES
from threading import RLock

class Audit:
    def __init__(self, bot, chat_id=None, path=None, secrets=(), clock=None):
        self.bot, self.chat_id = bot, chat_id
        self.path = Path(path) if path else None
        self.secrets = tuple(value for value in secrets if value)
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.lock = RLock()

    def clean(self, text, limit=300):
        text = str(text)
        for secret in self.secrets:
            text = text.replace(secret, "[redacted]")
        return re.sub(r"[0-9]+:[A-Za-z0-9_-]+", "[redacted]", text)[:limit]

    def record(self, chat_id, actor_id, target_id, action, reason, outcome, error=None, metadata=None):
        if outcome not in ("done", "refused", "failed", "partial", "uncertain"):
            raise ValueError("Unknown audit outcome")
        if type(chat_id) is not int or any(value is not None and type(value) is not int for value in (actor_id, target_id)):
            raise ValueError("Audit identities must be numeric")
        event = dict(time=self.clock().isoformat(), chat_id=chat_id,
                     actor=actor_id if actor_id is not None else "automation", target=target_id,
                     action=self.clean(action), reason=self.clean(reason), outcome=outcome)
        for key,value in (metadata or {}).items():
            if key in ("actor_role","target_role","actor_title","target_title","actor_native","target_native","actor_username","target_username","rule_code","rule_version","detail","origin","command","command_message","chat_title","warning_id","weight","valid_count","points","stage","evidence_id","evidence_status") and value is not None:
                event[key] = self.clean(value)
        if error is not None:
            event["error"] = type(error).__name__
            code=getattr(error,"error_code",None)
            if type(code) is int:event["error_code"]=code
            description=getattr(error,"description",None)
            result=getattr(error,"result_json",None)
            if not isinstance(description,str) and isinstance(result,dict):description=result.get("description")
            if isinstance(description,str):event["error_description"]=self.clean(description)
        if self.chat_id is not None:
            try:
                chat = self.bot.get_chat(self.chat_id)
                if chat.type not in ("group", "supergroup") or getattr(chat, "username", None):
                    raise ValueError("Private log group required")
                text = self.render(event)
                self.bot.send_message(self.chat_id, text, parse_mode="HTML")
                return True
            except Exception:
                pass
        try:
            if self.path is None:
                raise OSError("No fallback path")
            with self.lock:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as output:
                    output.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError:
            logging.getLogger(__name__).error("Audit destination unavailable; outcome=%s", outcome)
        return False


    def render(self,event):
        safe=lambda value: escape(str(value))
        lines=["AÇÃO — "+safe(ACTION_NAMES.get(event["action"],event["action"])),
               "Resultado: "+OUTCOME_NAMES[event["outcome"]],"Data/hora: "+safe(self.display_time(event["time"])),
               "", "Origem", "Grupo: "+safe(event.get("chat_title","nome não disponível")),
               "ID do grupo: "+str(event["chat_id"])]
        for key,label in (("command","Comando"),("command_message","Mensagem do comando")):
            if event.get(key):lines.append(label+": "+safe(event[key]))
        for prefix,label in (("actor","Autor"),("target","Alvo")):
            value=event[prefix]
            if value is None and prefix=="target":continue
            lines+=["",label]
            if type(value) is int:
                username=event.get(prefix+"_username")
                # ID appears once; a mention without username already includes it.
                lines.append("Usuário: "+mention(value,username)+(f" | ID: {value}" if username else ""))
            else:
                lines.append("Identificação: "+("Autor não identificável" if event.get("origin")=="human" else "Automação"))
            for key,field,mapping in (("_role","Cargo na Kanna",ROLE_NAMES),("_native","Cargo no Telegram",NATIVE_NAMES),("_title","Título no Telegram",{})):
                item=event.get(prefix+key)
                if item:lines.append(field+": "+safe(mapping.get(item,item)))
        lines+=["","Ação"]
        for key,label in (("reason","Motivo"),("warning_id","Advertência"),("rule_code","Regra"),("rule_version","Versão da regra"),("weight","Peso aplicado"),("valid_count","Advertências válidas"),("points","Pontos acumulados"),("detail","Detalhes"),("stage","Etapa"),("evidence_id","Registro da evidência"),("evidence_status","Disponibilidade da evidência"),("error","Erro"),("error_code","Código Telegram"),("error_description","Descrição Telegram")):
            if key in event and event[key]!="":lines.append(label+": "+safe(event[key]))
        return "\n".join(lines)

    @staticmethod
    def display_time(value):
        try:
            instant=datetime.fromisoformat(str(value).replace("Z","+00:00"))
            if instant.tzinfo is None:return str(value)
            local=instant.astimezone(timezone(timedelta(hours=-3)))
            return local.strftime("%d/%m/%Y às %H:%M:%S")+" — horário de Brasília (UTC−3)"
        except (TypeError,ValueError):return str(value)
