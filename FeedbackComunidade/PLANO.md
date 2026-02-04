# Plano do Projeto - Feedback da Comunidade Nuvemshop

## Objetivo
Criar uma página onde lojistas da comunidade Nuvemshop possam compartilhar seus e-commerces e receber feedback de outros lojistas, similar ao Padlet.

## Funcionalidades Implementadas

### 1. Cadastro de Lojas
- Nome da loja
- URL do site (aceita com ou sem http/https)
- Instagram
- Descrição/pedido de feedback
- Dados do proprietário (nome, email, WhatsApp) - **privados**

### 2. Cards de Lojas
- Preview da imagem do site (via og:image)
- Nome e descrição
- Links para site e Instagram
- Contador de curtidas e feedbacks
- Botão de curtir (coração)
- Botão para dar feedback
- Botão discreto para excluir (apenas dono)

### 3. Sistema de Feedback
- Nome do autor
- Email (privado)
- Telefone (opcional, privado)
- Texto do feedback
- Curtidas nos comentários

### 4. Busca
- Campo de busca na navbar
- Filtra por nome da loja

### 5. Painel de Gestão (Admin)
- Acesso via footer ("Gestão interna")
- Senha: `nuvemshop2024`
- Visualiza dados privados (email, WhatsApp)
- Pode excluir qualquer loja
- Estatísticas de lojas e feedbacks

## Design
- Inspirado no Nimbus Design System da Nuvemshop
- Hero estilo página de webinars (fundo azul escuro)
- Imagem do hero: `https://d4avy5zjiurvu.cloudfront.net/content/2024/08/hero_geral_BR-1.webp`
- Logo oficial da Nuvemshop
- Cores principais: Azul (#0066FF), Azul escuro (#0B1A33)

## Tecnologias
- HTML5 + CSS3 + JavaScript Vanilla
- LocalStorage para persistência
- API Microlink para preview de sites

## Arquivos
```
FeedbackComunidade/
├── feedback-comunidade.html    # Página principal (tudo em um arquivo)
├── assets/
│   └── logo-nuvemshop.png      # Logo oficial
├── README.md                   # Documentação para GitHub
├── PLANO.md                    # Este arquivo
└── .gitignore                  # Arquivos ignorados pelo Git
```

## Melhorias Futuras (Backlog)

### Prioridade Alta
- [ ] Backend com banco de dados real
- [ ] Autenticação de usuários
- [ ] Upload de imagens próprias
- [ ] Notificações por email

### Prioridade Média
- [ ] Categorias de lojas (moda, pet, alimentos, etc.)
- [ ] Filtros avançados
- [ ] Ordenação (mais curtidas, mais recentes)
- [ ] Paginação

### Prioridade Baixa
- [ ] Modo escuro
- [ ] Compartilhamento em redes sociais
- [ ] Badges/conquistas para participantes ativos
- [ ] Integração com API da Nuvemshop

## Configurações

### Acesso Admin
- Link: Footer > "Gestão interna"
- Senha: `nuvemshop2024`
- **Importante**: Em produção, trocar para autenticação real

### LocalStorage Keys
- `nuvemshop_feedback_stores` - Dados das lojas
- `device_id` - ID único do dispositivo (para controle de likes)

## Referências de Design
- Nimbus Design System: https://nimbus.nuvemshop.com.br/
- Página LCY: https://lcy-teste.vercel.app/
- Página Webinars: https://www.nuvemshop.com.br/newsletter/webinars

## Histórico de Alterações

### Versão 1.0 (Fevereiro 2026)
- Página inicial com cards de lojas
- Sistema de cadastro e feedback
- Curtidas em lojas e comentários
- Busca por nome
- Painel administrativo
- Design alinhado com Nuvemshop
- Hero estilo webinars com imagem
- Botão de excluir discreto com tooltip
- Termos "feedback" em vez de "sugestões"
