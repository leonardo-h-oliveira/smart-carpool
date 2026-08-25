# Telas: do UniCar ao Smart Carpool

## 1. Screen1 — acesso e cadastro

No protótipo antigo concentrava inicialização, TinyDB, autenticação Firebase, `localId` e cadastro de usuário/veículo. Na nova versão foi separada em login, criação de conta, perfil e veículo para reduzir complexidade.

## 2. Screen4 — menu principal

Era o ponto de decisão entre oferecer e solicitar carona. Agora é o dashboard inicial, com os dois atalhos e caronas próximas.

## 3. Screen3 — oferta

Motorista escolhe veículo, origem, destino, data, horário, vagas e observações. A oferta passa a ter estado (`open`, `completed` ou `cancelled`) e controle explícito de vagas.

## 4. Screen2 — solicitação

Passageiro pesquisa caronas por origem, destino e data, abre os detalhes e solicita uma vaga. A solicitação nasce como `pending`.

## 5. Screen5 — embarque e contato

No protótipo reunia embarque e contato por WhatsApp. Na nova experiência corresponde a **Minhas viagens**, onde motorista aceita/recusa pedidos e passageiro acompanha o status. O contato só deve ser liberado após o aceite.

## Telas complementares da nova versão

- Meu veículo
- Perfil
- Minhas viagens
- Estado vazio, carregamento, sucesso e erro em cada jornada

