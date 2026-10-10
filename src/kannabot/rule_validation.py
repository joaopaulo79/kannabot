"""Explain catalog refusals before moderation effects are started."""

class RuleRefusal(ValueError):
    """An expected business refusal, rather than an execution error."""


def validate_rule_action(rule, code, action):
    effect = ("Nenhuma advertência foi registrada e nenhuma mensagem foi apagada."
              if action == "delwarn" else "Nenhuma ação foi aplicada.")
    catalog_action = "warn" if action == "delwarn" else action
    label = {"warn": "advertência", "delete": "exclusão de mensagem",
             "mute": "silenciamento", "ban": "banimento",
             "kick": "expulsão", "unban": "remoção de banimento"}.get(catalog_action, catalog_action)
    if rule is None:
        explanation = f"A regra {code} não foi encontrada no catálogo deste grupo.\nUse /rules para consultar os códigos disponíveis."
    elif not rule["active"]:
        explanation = f"A regra {code} — {rule['name']} foi revogada e não pode fundamentar novas ações.\nConsulte /rule {code} para ver os detalhes."
    elif catalog_action not in rule["actions"]:
        explanation = f"A regra {code} — {rule['name']} não permite {label} pelo catálogo."
        if catalog_action == "warn" and rule["level"] == "N1" and rule["weight"] is None:
            explanation += "\nPara advertências por reincidência, a administração precisa definir os critérios e o peso antes de habilitar essa ação."
        explanation += f"\nConsulte /rule {code} para ver as ações previstas."
    elif catalog_action == "warn" and rule["weight"] is None:
        explanation = f"A regra {code} — {rule['name']} prevê advertência, mas seu peso ainda não foi definido.\nA administração precisa configurar o peso antes de usar essa regra.\nConsulte /rule {code} para ver os detalhes."
    else:
        return
    raise RuleRefusal("⚠️ Ação recusada\n" + explanation + "\n\n" + effect)


def normalize_rule_code(code):
    """Accept r1/R1 as R01 while retaining existing longer canonical codes."""
    code=code.upper()
    if len(code)==2 and code[0]=="R" and code[1] in "0123456789":
        return "R0"+code[1]
    return code
