import json, os

# Caminho do arquivo de log
log_path = None

# Classe para gerenciar os cliques em botões
class Verificar_Button:
    def __init__(self, Msg, caminho):
        self.Msg = Msg
        self.caminho = caminho
        self._Carregar_Log()

    def _Carregar_Log(self):
        if os.path.exists(self.caminho):
            with open(self.caminho, "r", encoding="utf-8") as f:
                self.log = json.load(f)
        else:
            self.log = {}

    def _Salvar_Log(self):
        os.makedirs(os.path.dirname(self.caminho), exist_ok=True)
        with open(self.caminho, "w", encoding="utf-8") as f:
            json.dump(self.log, f, ensure_ascii=False, indent=2)

    def Ja_Clicou(self, user_id: str) -> bool:
        return self.log.get(user_id, False)

    def Registrar_Clique(self, user_id: str):
        self.log[user_id] = True
        self._Salvar_Log()

    def Limpar_Log(self):
        self.log = {}
        self._Salvar_Log()

    def Case_Username_Username(self, username: str, user_id: str):
        if username == self.Msg.Username():
            self.Registrar_Clique(user_id)
            return True
        else:
            return False

    def Case_Username_Not_Username(self, username: str, user_id: str):
        if username != self.Msg.Username():
            self.Registrar_Clique(user_id)
            return True
        else:
            return False

    def Case_Username_TargetUsername(self, username: str, user_id: str):
        if username == self.Msg.TargetUsername():
            self.Registrar_Clique(user_id)
            return True
        else:
            return False
