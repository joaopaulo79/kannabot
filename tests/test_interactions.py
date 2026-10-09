import unittest
from unittest.mock import Mock
from types import SimpleNamespace as N
from pathlib import Path
from kannabot.interacoes import Interactions
from kannabot.handlers.emotes import Emotes
from kannabot._config.configuracao import Configuracao
class InteractionTests(unittest.TestCase):
 def test_identity_scope_expiry_capacity(self):
    now=[0];s=Interactions(ttl=10,capacity=2,clock=lambda:now[0])
    value=dict(owner=1,target=2,buttons={'x'},roles={'x':'target'})
    s.put((1,1),value);s.put((2,1),value)
    self.assertIsNone(s.claim((1,1),3,'x'))
    self.assertIsNone(s.claim((1,1),2,'spoof'))
    self.assertIsNotNone(s.claim((1,1),2,'x'))
    self.assertIsNone(s.claim((1,1),2,'x'))
    self.assertIsNotNone(s.claim((2,1),2,'x'))
    now[0]=11;self.assertIsNone(s.claim((2,1),1,'x'))
    for k in range(3):s.put(k,value)
    self.assertEqual(len(s.items),2)
 def test_commands_interleaved_keep_message(self):
    bot=Mock();bot.get_chat_member.return_value=N(status='administrator')
    bot.send_animation.side_effect=[N(message_id=10),N(message_id=11),N(message_id=12)]
    cfg=Configuracao('123:fake',Path('x'),(1,2),'@KannaTesteBot');e=Emotes(bot,cfg)
    def msg(chat,user,target):
        return N(chat=N(id=chat),message_id=1,text='/hug',sender_chat=None,from_user=N(id=user,username=None,is_bot=False),reply_to_message=N(from_user=N(id=target,username=None)))
    e.command('hug',msg(1,7,8));e.command('hug',msg(2,9,10))
    call=N(id='callback',data='Aceitar_Abraço',from_user=N(id=8,username=None),message=N(chat=N(id=1),message_id=10))
    e.callback(call)
    self.assertEqual(bot.send_animation.call_args.args[0],1)
    self.assertIn('8',bot.send_animation.call_args.kwargs['caption'])
    bot.answer_callback_query.assert_called_once()
 def test_unauthorized_callback_is_answered(self):
    bot=Mock();e=Emotes(bot,Configuracao('123:fake',Path('x'),(1,),'@TesteBot'))
    e.callback(N(id='x',message=None))
    bot.answer_callback_query.assert_called_once()
    bot.send_animation.assert_not_called()
