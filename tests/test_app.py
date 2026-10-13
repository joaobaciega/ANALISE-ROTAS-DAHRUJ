from streamlit.testing.v1 import AppTest
from rotas.dados import ROOT


def test_interface_filtros_e_ceasa(monkeypatch):
    # O app deve operar sem consultar serviços externos.
    import requests
    def sem_rede(*args, **kwargs):
        raise AssertionError('O app tentou acessar a rede')
    monkeypatch.setattr(requests.sessions.Session, 'request', sem_rede)
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
    assert not app.exception
    assert app.metric[0].value == '4'
    assert app.metric[1].value == '14'
    app.checkbox[0].check()
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == '5'
    assert app.metric[1].value == '19'
    app.multiselect[0].set_value(['DEALER'])
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == '1'
    assert app.metric[1].value == '2'
    app.multiselect[1].set_value([])
    app.button[0].click().run()
    assert not app.exception
    assert 'Nenhuma loja selecionada' in app.info[0].value
