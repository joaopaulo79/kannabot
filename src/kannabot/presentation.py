"""Human-facing output; IDs remain the authority."""
from html import escape

ROLE_NAMES = {"owner":"Dono","admin":"Admin","mod":"Mod","member":"Membro"}
NATIVE_NAMES = {"creator":"Proprietário","administrator":"Administrador","member":"Membro","restricted":"Restrito","left":"Ausente","kicked":"Banido"}
ACTION_NAMES = {"warn":"Advertência","warnings":"Consulta de advertências","unwarn":"Cancelamento de advertência","delete":"Exclusão de mensagem","delwarn":"Exclusão com advertência","mute":"Silenciamento","kick":"Expulsão","ban":"Banimento","unban":"Remoção de banimento","role":"Atribuição de cargo","role_remove":"Remoção de cargo","rules_import":"Importação de regras","rule_set":"Edição de regra","rule_disable":"Desativação de regra","catalog":"Consulta de regras","detections":"Consulta de detecções","review":"Revisão de detecção","dismiss":"Descarte de detecção","review_pending":"Detecção aguardando revisão","spam_observe":"Observação de antispam"}
OUTCOME_NAMES = {"done":"Concluída","refused":"Recusada","failed":"Falha confirmada","partial":"Parcial","uncertain":"Resultado incerto"}
def mention(user_id, username=None):
    if isinstance(username,str) and username.strip():
        return escape("@"+username.lstrip("@"))
    if type(user_id) is int:
        return f'<a href="tg://user?id={user_id}">Usuário {user_id}</a>'
    return "Identidade não confirmada"
def user_mention(user):
    return mention(getattr(user,"id",None),getattr(user,"username",None))
def context(message):
    user=getattr(message,"from_user",None)
    actor=getattr(user,"id",None)
    if getattr(message,"sender_chat",None) is not None or type(actor) is not int: actor=None
    metadata={"origin":"human","command":getattr(message,"text","") or "","command_message":getattr(message,"message_id",None)}
    title=getattr(message.chat,"title",None)
    if isinstance(title,str):metadata["chat_title"]=title
    username=getattr(user,"username",None)
    if actor is not None and isinstance(username,str):metadata["actor_username"]=username
    reply=getattr(message,"reply_to_message",None)
    target=getattr(reply,"from_user",None)
    username=getattr(target,"username",None)
    if isinstance(username,str):metadata["target_username"]=username
    return actor,metadata
def brief(rule):
    return escape(rule.get("summary") or rule["description"])
def rule_text(rule):
    weight=rule["weight"] if rule["weight"] is not None else "não definido"
    actions={"warn":"Advertência","delete":"Exclusão","mute":"Silenciamento","ban":"Banimento"}
    conditions=[]
    bounds={"N1":"5 a 59 minutos","N2":"1 a 24 horas","N3":"1 dia a 1 semana"}
    if "mute" in rule["actions"] and rule["level"] in bounds:
        conditions.append("Faixa de silenciamento: "+bounds[rule["level"]]+".")
    if rule["weight"] is None:
        conditions.append("Peso de advertência não definido; não presumir valor.")
    if rule["level"]=="N1":
        conditions.append("Advertência por reincidência depende de critérios e peso definidos pela administração.")
    return (f"📖 {escape(rule['code'])} — {escape(rule['name'])}\n"
            f"Nível: {rule['level']} · Peso: {weight} · Versão: {rule['version']}\n"
            f"Estado: {'ativa' if rule['active'] else 'revogada'}\n\n"
            f"{escape(rule['description'])}\n\n"
            "Ações cadastradas: "+", ".join(actions[a] for a in rule["actions"])+
            ("\n"+"\n".join(conditions) if conditions else "")+
            "\nA aplicação depende da moderação. Esta consulta não executa punições.")


def send_reply(bot,chat,text):
    """Keep replies within Telegram limits without truncating history or rule text."""
    from html import unescape
    pages=[];current=""
    for line in text.splitlines():
        if len(line)>3000:
            # Long rule descriptions contain escaped plain text, not generated mention tags.
            raw=unescape(line)
            pieces=[escape(raw[i:i+1500]) for i in range(0,len(raw),1500)]
        else:pieces=[line]
        for piece in pieces:
            if current and len(current)+len(piece)+1>3500:pages.append(current);current=""
            current+=("\n" if current else "")+piece
    if current:pages.append(current)
    for page in pages:bot.send_message(chat,page,parse_mode="HTML")
