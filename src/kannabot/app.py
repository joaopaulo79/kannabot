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

def create_app(configuracao=None, client=None, home=None):
    root = Path(home or os.getenv("KANNA_HOME") or RAIZ_PROJETO).resolve()
    settings = configuracao or carregar_configuracao(root)
    policy = Policy.load(settings.policy_path)
    bot = client if client is not None else TeleBot(settings.token)
    bot.kanna_audit = Audit(bot, settings.log_chat_id, root / "var/audit.jsonl", secrets=(settings.token,))
    store = Governance(root / "var/moderation.sqlite3")
    bot.kanna_identities = Identities(bot, settings.grupos_id, store.path)
    register_identities(bot, bot.kanna_identities)
    bot.kanna_roles = Roles(bot, settings.grupos_id, store)
    bot.kanna_moderation = Moderation(bot, settings, store, bot.kanna_audit, roles=bot.kanna_roles)
    bot.kanna_moderation.identities = bot.kanna_identities
    bot.kanna_evidence = Evidence(store.path,bot.kanna_audit.clean)
    bot.kanna_moderation.evidence = bot.kanna_evidence
    bot.kanna_administration = Administration(bot.kanna_moderation, store, bot.kanna_roles, bot.kanna_audit)
    bot.kanna_antispam = Antispam(bot, settings, policy, bot.kanna_audit, roles=bot.kanna_roles)
    bot.kanna_review = Review(bot.kanna_moderation, ReviewStore(root / "var/moderation.sqlite3"), bot.kanna_audit)
    register_antispam(bot, bot.kanna_antispam, bot.kanna_review.observe)
    register_review(bot, bot.kanna_review)
    bot.kanna_help = Help(bot.kanna_moderation)
    register_help(bot,bot.kanna_help)
    register_moderation(bot, bot.kanna_moderation)
    register_administration(bot, bot.kanna_administration)
    register_welcome(bot, Welcome(bot, settings, policy, bot.kanna_audit))
    register(bot, settings, root / "var")
    return bot
