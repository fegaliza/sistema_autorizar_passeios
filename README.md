# Central de Autorizações

Aplicação Streamlit para gestão de eventos, autorizações, assinaturas e PDFs.

## Configuração local

1. Instale Python 3.11 e execute `pip install -r requirements.txt`.
2. Execute `python gerar_hash.py` e guarde o hash gerado. **Não é necessário gerar novamente a cada deploy.**
3. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`, preenchendo o hash e as demais configurações. Nunca publique `secrets.toml`.
4. Execute `streamlit run app.py`.

## Publicação no Streamlit Community Cloud

1. Crie um repositório **privado** no GitHub e envie `app.py`, `requirements.txt`, `gerar_hash.py`, `README.md` e `.streamlit/config.toml`. Não envie arquivos `.db` ou `secrets.toml`.
2. Provisione um PostgreSQL **persistente**, com backup e SSL, em provedor confiável (confirme limites e política de retenção do plano). Não use SQLite local na hospedagem: o disco pode ser descartado.
3. No Streamlit Community Cloud, crie o app apontando para `app.py`. Em **Advanced settings → Secrets**, insira os valores de `.streamlit/secrets.toml.example` com os dados reais.
4. Configure `APP_BASE_URL` com a URL pública exata, sem barra final. Teste link público, assinatura, salvamento, CSV e PDF após reiniciar a aplicação.
5. Para atualizações futuras, mantenha o mesmo `ADMIN_PASSWORD_HASH` nos Secrets. Alterar o código ou reiniciar o app não deve exigir novo hash.

## Segurança e privacidade

- Os registros contêm dados pessoais de menores e podem incluir informações de saúde. Antes de disponibilizar publicamente, defina controlador, aviso de privacidade, base legal, acesso, retenção, backups e política de incidentes conforme a LGPD.
- `st.session_state` fornece autenticação por sessão de navegador, **não** é um sistema de identidade corporativo. Bloqueio de tentativas também é por sessão, não global. Para maior escala, use autenticação gerenciada e controles adicionais.
- O componente de assinatura `streamlit-drawable-canvas` deve ser validado no ambiente publicado; sua manutenção/compatibilidade pode variar conforme a versão do Streamlit.
- Tema claro/escuro usa `prefers-color-scheme` do dispositivo. O canvas de assinatura permanece branco intencionalmente.
- Não existe hospedagem gratuita com acessos, disponibilidade e armazenamento ilimitados garantidos. Confira quotas e termos atuais do provedor.
- Não há migração automática de registros do SQLite existente para PostgreSQL. Faça exportação/migração segura antes de trocar o banco de produção.
