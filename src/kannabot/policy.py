"""Validated local policies, disabled when no file is configured."""
import json
from pathlib import Path
from kannabot.links import normalize_host
from kannabot._config.configuracao import ErroConfiguracao

class Policy:
    def __init__(self, data=None):
        data = {"groups":{}} if data is None else data
        if not isinstance(data,dict) or set(data)!={"groups"} or not isinstance(data["groups"],dict):
            raise ErroConfiguracao("Políticas requerem objeto groups.")
        self.groups = data["groups"]
        for group, options in self.groups.items():
            try:
                valid = str(int(group))==group
            except (TypeError,ValueError):
                valid=False
            if not valid or not isinstance(options,dict) or set(options)-{"welcome", "spam", "links"}:
                raise ErroConfiguracao("Grupo ou opção de política inválido.")
            links=options.get("links")
            if links is not None:
                if not isinstance(links,dict) or set(links)!={"allow","deny","include_subdomains"} or type(links["include_subdomains"]) is not bool:
                    raise ErroConfiguracao("Links requerem allow, deny e include_subdomains booleano.")
                try:
                    for name in ("allow","deny"):
                        if not isinstance(links[name],list) or len(links[name])>100:
                            raise ValueError()
                        links[name]=[normalize_host(host) for host in links[name]]
                except (ValueError,UnicodeError):
                    raise ErroConfiguracao("Domínios de política inválidos.") from None
            spam=options.get("spam")
            if spam is not None:
                keys={"flood_limit","flood_window","repeat_limit","repeat_window"}
                if not isinstance(spam,dict) or set(spam)!=keys:
                    raise ErroConfiguracao("Spam requer limites e janelas de flood e repetição.")
                for key,value in spam.items():
                    maximum=100 if key.endswith("limit") else 3600
                    if type(value) is not int or not 1<=value<=maximum:
                        raise ErroConfiguracao("Limites e janelas de spam fora do intervalo.")
            welcome=options.get("welcome")
            if welcome is not None:
                if not isinstance(welcome,dict) or set(welcome)!={"text","rules"} or any(not isinstance(value,str) or not value.strip() or len(value)>250 for value in welcome.values()):
                    raise ErroConfiguracao("Boas-vindas requerem text e rules não vazios até 250 caracteres.")
    @classmethod
    def load(cls, path):
        if path is None:
            return cls()
        try:
            return cls(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError,ValueError):
            raise ErroConfiguracao("Arquivo de políticas inválido ou ilegível.") from None
    def get(self, chat_id, name):
        return self.groups.get(str(chat_id),{}).get(name)
