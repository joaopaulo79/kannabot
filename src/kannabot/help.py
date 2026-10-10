"""Role-aware command help; querying help never applies a moderation action."""
from html import escape
from kannabot.governance import CAPABILITIES
from kannabot.moderation import Result
from kannabot.permissions import PermissionDenied
from kannabot.presentation import ROLE_NAMES, context, send_reply

COMMANDS = (
    ('warn', 'warn R10 motivo', 'Registra advertência com o peso da regra. /warn motivo registra advertência manual sem peso definido.'),
    ('warnings', 'warnings', 'Consulta o histórico de advertências do alvo, incluindo cancelamentos.'),
    ('delete', 'delete motivo', 'Apaga a mensagem respondida, sem adicionar advertência.'),
    ('mute', 'mute 10m motivo', 'Silencia o alvo temporariamente. Durações: s, m, h ou d; mínimo 1 minuto.'),
    ('kick', 'kick motivo', 'Remove o alvo e permite retorno voluntário.'),
    ('ban', 'ban motivo', 'Bane o alvo. Ban confirmado revoga cargo interno; respeita a hierarquia.'),
    ('unban', 'unban motivo', 'Remove o banimento, sem adicionar o alvo ao grupo nem restaurar cargo.'),
    ('unwarn', 'unwarn 2 motivo', 'Cancela a advertência pelo registro, preservando histórico. Alvo opcional para conferência.'),
    ('catalog', 'catalog R10', 'Mostra a regra completa. /catalog lista o catálogo.'),
)

class Help:
    def __init__(self,moderation):
        self.moderation=moderation

    def render(self,role):
        capabilities=CAPABILITIES[role]
        lines=[f"📖 Ajuda da Kanna — {ROLE_NAMES[role]}",
               "Aqui estão os comandos disponíveis para seu cargo neste grupo:", ""]
        for capability,syntax,description in COMMANDS:
            if capability in capabilities:
                lines.extend(["<code>/"+escape(syntax)+"</code>",escape(description),""])
        if {'warn','delete'} <= capabilities:
            lines.extend(["<code>/delwarn R10 motivo</code>",
                "Apaga a mensagem respondida e registra advertência com a regra.",
                "<code>/delwarn motivo</code> — advertência manual sem peso; não acrescenta pontos.",""])
        if 'review' in capabilities:
            actions=[action for action in ('warn','delete','mute','ban') if action in capabilities]
            lines.extend(["🔎 Revisão humana", "<code>/detections</code> — lista detecções pendentes.",
                "<code>/dismiss 2 motivo</code> — descarta a detecção pelo ID.",
                "<code>/review 2 warn R10 motivo</code> — aplica uma decisão à detecção.",
                "Ações permitidas: "+", ".join(actions)+". Para mute: /review 2 mute 1d R10 motivo.",
                "A revisão exige regra. Detecção e limite de pontos não aplicam ban automaticamente.",""])
        if 'roles' in capabilities:
            lines.extend(["🛡️ Cargos internos", "<code>/role mod</code> — atribui Mod ao alvo.",
                "<code>/role_remove</code> — remove o cargo interno do alvo."])
            if role=='owner':lines.append("<code>/role admin</code> — atribui Admin. Somente o Dono pode gerir Admins.")
            else:lines.append("Admin pode gerir Mod; não pode alterar Admin ou Dono.")
            lines.append("")
        if 'rules' in capabilities:
            lines.extend(["📚 Administração de regras", "<code>/rules_import</code> — importa regras ausentes.",
                "<code>/rules_import atualizar</code> — atualiza redações genéricas, preservando personalizações e histórico.",
                "<code>/rule_set JSON</code> — cria uma versão da regra com code, name, description, level, weight, active e actions.",
                "<code>/rule_disable R10</code> — revoga a regra para novas aplicações.",""])
        lines.extend(["🎯 Como indicar o alvo", "Responda à mensagem da pessoa ou informe @username antes dos argumentos:",
            "<code>/warn @usuario R10 motivo</code>",
            "O username precisa ser conhecido e confirmado; se não for, use uma resposta.",
            "/delete e /delwarn sempre exigem resposta à mensagem que será apagada.",
            "/review e /dismiss usam o ID da detecção; /unwarn usa o registro da advertência.","",
            "Seu cargo na Kanna é independente do título e do cargo no Telegram.",
            "Administradores nativos do Telegram não são rebaixados automaticamente para receber mute/ban.",
            "Se necessário, acrescente @username_do_bot ao comando, como /help@username_do_bot.",
            "Emotes continuam disponíveis para Membros. Use /help para consultar esta lista novamente."])
        return "\n".join(lines)

    def handle(self,message):
        actor,metadata=context(message);error=None
        try:
            actor=self.moderation.permissions.emote_actor(message)
            roles=self.moderation.roles
            if roles is None:raise PermissionDenied("Não foi possível confirmar seu cargo interno.")
            role=roles.role(message.chat.id,actor)
            if role not in ('owner','admin','mod'):
                raise PermissionDenied("🛡️ Esta ajuda é destinada ao Dono, Admin e Mod da Kanna.")
            metadata['actor_role']=role
            result=Result('done',self.render(role))
        except (PermissionDenied,ValueError) as exc:result=Result('refused',escape(self.moderation.audit.clean(str(exc))))
        except Exception as exc:error=exc;result=Result('failed','Não foi possível consultar a ajuda agora.')
        self.moderation.audit.record(message.chat.id,actor,None,'help','Consulta de comandos',result.outcome,error,metadata=metadata)
        return result

def register(bot,service):
    @bot.message_handler(commands=['help'])
    def handle(message):
        result=service.handle(message)
        try:send_reply(bot,message.chat.id,result.message)
        except Exception:
            actor,metadata=context(message)
            service.moderation.audit.record(message.chat.id,actor,None,'help_feedback','Falha no retorno','failed',metadata=metadata)
