"""Human-facing output; IDs remain the authority."""
from html import escape

ROLE_NAMES = {"owner":"Dono","admin":"Admin","mod":"Mod","member":"Membro"}
NATIVE_NAMES = {"creator":"Proprietário","administrator":"Administrador","member":"Membro","restricted":"Restrito","left":"Ausente","kicked":"Banido"}
ACTION_NAMES = {"help":"Consulta de ajuda","help_feedback":"Retorno da ajuda","warn":"Advertência","warnings":"Consulta de advertências","unwarn":"Cancelamento de advertência","delete":"Exclusão de mensagem","delwarn":"Exclusão com advertência","mute":"Silenciamento","kick":"Expulsão","ban":"Banimento","unban":"Remoção de banimento","role":"Atribuição de cargo","role_remove":"Remoção de cargo","rules_import":"Importação de regras","rule_set":"Edição de regra","rule_disable":"Desativação de regra","catalog":"Consulta de regras","detections":"Consulta de detecções","review":"Revisão de detecção","dismiss":"Descarte de detecção","review_pending":"Detecção aguardando revisão","spam_observe":"Observação de antispam"}
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
    """Show the actual policy as readable prose, without implying an action ran."""
    lines=[f"📖 <b>{escape(rule['code'])} — {escape(rule['name'].removesuffix(' — revogada'))}</b>",
           f"Nível {escape(rule['level'][1:])}"]
    if not rule['active']:lines.extend(["","🚫 <b>Regra revogada</b>","Não se aplica a novas ocorrências. O histórico permanece preservado."])
    lines.extend(["","<b>Descrição</b>",escape(rule['description']),"","<b>Aplicação prevista</b>"])
    bounds={"N1":"5 a 59 minutos","N2":"1 a 24 horas","N3":"1 dia a 1 semana"}
    for action in rule['actions']:
        if action=='warn':
            weight=rule['weight']
            lines.append("• Advertência: 0 pontos; conta no histórico sem acrescentar pontos." if weight == 0 else f"• Advertência: +{weight} {'ponto' if weight==1 else 'pontos'}." if weight is not None else "• Advertência: peso não definido.")
        elif action=='delete':lines.append("• Exclusão da mensagem.")
        elif action=='mute':lines.append("• Silenciamento: de "+bounds[rule['level']]+"." if rule['level'] in bounds else "• Silenciamento, conforme condições definidas pela administração.")
        elif action=='ban':lines.append("• Banimento.")
    if not rule['actions']:lines.append("Nenhuma ação definida para esta regra.")
    if rule['level']=='N1' and rule['weight'] is None:lines.extend(["","⚠️ <b>Condição para advertência</b>","Advertência por reincidência depende de critérios definidos pela administração; peso não definido."])
    elif 'warn' in rule['actions'] and rule['weight'] is None:
        lines.extend(["","⚠️ O peso ainda precisa ser definido pela administração; não presumir pontuação."])
    lines.extend(["","🛡️ A aplicação exige decisão da moderação, respeitando permissões e condições da regra.",
                  "Esta consulta não aplica nenhuma punição.","",f"Revisão da regra: {escape(str(rule['version']))}."])
    return "\n".join(lines)


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


def catalog_text(rules):
    """Readable index; full policy data remains in the per-rule view."""
    active=[rule for rule in rules if rule["active"]]
    revoked=[rule for rule in rules if not rule["active"]]
    active_label="ativa" if len(active)==1 else "ativas"
    revoked_label="revogada" if len(revoked)==1 else "revogadas"
    lines=["📚 <b>Regras do grupo</b>",f"{len(active)} {active_label} · {len(revoked)} {revoked_label}"]
    for level in ("N1","N2","N3","N4"):
        entries=sorted((rule for rule in active if rule["level"]==level),key=lambda rule:rule["code"])
        if entries:
            lines.extend(["",f"<b>Nível {level[1:]}</b>"])
            lines.extend(f"{escape(rule['code'])} — {escape(rule['name'])}" for rule in entries)
    if revoked:
        lines.extend(["","🗂️ <b>Regras revogadas</b>"])
        lines.extend(f"{escape(rule['code'])} — {escape(rule['name'].removesuffix(' — revogada'))}" for rule in sorted(revoked,key=lambda rule:rule["code"]))
        lines.append("Não se aplicam a novas ocorrências.")
    lines.extend(["","🔎 Para ler uma regra, use <code>/catalog R10</code>.",
                  "A consulta detalhada mostra descrição, pontuação, condições e versão."])
    return "\n".join(lines)
