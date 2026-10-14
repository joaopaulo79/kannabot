from dataclasses import replace
from kannabot.group_registry import GroupRegistry, GroupAccess
from kannabot.registration import Registration, register as register_registration
from kannabot.help import Help, register as register_help
from kannabot.evidence import Evidence
import os
from kannabot.identities import Identities, register as register_identities
from pathlib import Path
from telebot import TeleBot
from kannabot.audit import Audit
from kannabot.review_store import ReviewStore
from kannabot.review import Review, register as register_review
from kannabot.antispam import Antispam, register as register_antispam
from kannabot.policy import Policy
from kannabot.welcome import Welcome, register as register_welcome
from kannabot.governance import Governance
from kannabot.roles import Roles
from kannabot.administration import Administration, register as register_administration
from kannabot.moderation import Moderation
from kannabot.handlers.moderation import register as register_moderation
from kannabot._config.configuracao import carregar_configuracao, RAIZ_PROJETO
from kannabot.handlers.emotes import register
from kannabot import database
from kannabot._config.configuracao import ErroConfiguracao

def create_app(configuracao=None, client=None, home=None):
    root = Path(home or os.getenv("KANNA_HOME") or RAIZ_PROJETO).resolve()
    settings = configuracao or carregar_configuracao(root)
    policy = Policy.load(settings.policy_path)
    bot = client if client is not None else TeleBot(settings.token)
    try:
        store = Governance(settings.database_url or root / "var/moderation.sqlite3")
        registry = GroupRegistry(store.path)
    except database.Error:
        raise ErroConfiguracao("Banco indisponível; inicialização interrompida.") from None
    access = GroupAccess(registry, settings.grupos_id)
    legacy_groups = settings.grupos_id
    legacy_log = settings.log_chat_id
    settings = replace(settings, grupos_id=access)
    bot.kanna_audit = Audit(bot, None, root / "var/audit.jsonl",
        secrets=tuple(value for value in (settings.token, settings.database_url) if value),
        destination=lambda chat: access.destination(chat, legacy_log))
    bot.kanna_registration = Registration(bot, registry, bot.kanna_audit, settings.registrar_ids, legacy_groups, legacy_log=legacy_log, operators=settings.operator_ids)
    register_registration(bot, bot.kanna_registration)
    bot.kanna_identities = Identities(bot, settings.grupos_id, store.path)
    register_identities(bot, bot.kanna_identities)
    bot.kanna_roles = Roles(bot, settings.grupos_id, store, operators=settings.operator_ids)
    bot.kanna_moderation = Moderation(bot, settings, store, bot.kanna_audit, roles=bot.kanna_roles)
    bot.kanna_moderation.identities = bot.kanna_identities
    bot.kanna_evidence = Evidence(store.path,bot.kanna_audit.clean)
    bot.kanna_moderation.evidence = bot.kanna_evidence
    bot.kanna_administration = Administration(bot.kanna_moderation, store, bot.kanna_roles, bot.kanna_audit)
    bot.kanna_antispam = Antispam(bot, settings, policy, bot.kanna_audit, roles=bot.kanna_roles)
    bot.kanna_review = Review(bot.kanna_moderation, ReviewStore(store.path), bot.kanna_audit)
    register_antispam(bot, bot.kanna_antispam, bot.kanna_review.observe)
    register_review(bot, bot.kanna_review)
    bot.kanna_help = Help(bot.kanna_moderation)
    register_help(bot,bot.kanna_help)
    register_moderation(bot, bot.kanna_moderation)
    register_administration(bot, bot.kanna_administration)
    register_welcome(bot, Welcome(bot, settings, policy, bot.kanna_audit))
    register(bot, settings, root / "var")
    return bot
