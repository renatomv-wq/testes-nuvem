# Trilha de Sucesso - Nuvemshop

Uma página de trilha de conteúdos (LMS) para ajudar lojistas da Nuvemshop a criar suas lojas e começar a vender rapidamente.

## Como Visualizar

Abra o arquivo `index.html` no navegador ou use um servidor local:

```bash
# Com Python
python -m http.server 8000

# Com Node.js (npx)
npx serve .

# Com PHP
php -S localhost:8000
```

Depois acesse: http://localhost:8000

---

## Configuração dos Vídeos

### 1. Vídeos das Aulas (Trilha)

Os vídeos das aulas são configurados no arquivo `script.js` na variável `courseData`.

**Para vídeos do YouTube/StreamYard:**

Após a transmissão no StreamYard, o vídeo fica disponível no YouTube. Pegue o ID do vídeo:

- URL: `https://www.youtube.com/watch?v=ABC123xyz`
- ID: `ABC123xyz`

```javascript
{
    id: "2-2",
    title: "Como cadastrar seus primeiros produtos",
    duration: "12 min",
    videoType: "youtube",
    videoId: "ABC123xyz",  // Substitua pelo ID real
    resources: [
        { title: "Checklist de cadastro", url: "link-do-pdf.pdf" }
    ]
}
```

### 2. Webinars Gravados

Configure os webinars gravados na variável `recordedWebinars` em `script.js`:

```javascript
const recordedWebinars = {
    "webinar-1": {
        id: "webinar-1",
        title: "NuvemCommerce 2025: o que os dados revelam",
        description: "Análise completa das tendências...",
        duration: "58 min",
        date: "15 Jan 2026",
        videoType: "youtube",
        videoId: "ID_DO_VIDEO_YOUTUBE",
        resources: [
            { title: "Relatório PDF", url: "#" }
        ]
    }
};
```

### 3. Webinars Ao Vivo (Calendário)

Edite diretamente no `index.html` a seção `live-webinars-section`:

1. Atualize as datas dos eventos
2. Substitua os links do StreamYard:
   ```html
   <a href="https://streamyard.com/watch/SEU_LINK_AQUI" target="_blank" class="btn btn-primary">
       Inscrever-se
   </a>
   ```
3. Atualize títulos, descrições e speakers

### 4. Vídeos MP4 (auto-hospedados)

Se você tem vídeos em servidor próprio:

```javascript
{
    videoType: "mp4",
    videoId: "https://seu-servidor.com/video.mp4"
}
```

---

## Estrutura do Curso

A trilha está organizada em 6 módulos:

| Módulo | Título | Foco |
|--------|--------|------|
| 1 | Primeiros Passos | Configuração inicial da conta |
| 2 | Cadastro de Produtos | Criar produtos que vendem |
| 3 | Pagamentos e Frete | Meios de pagamento e entrega |
| 4 | Visual e Identidade | Personalização da loja |
| 5 | Primeiras Vendas | Marketing e divulgação |
| 6 | Lançamento da Loja | Checklist final e go-live |

---

## Funcionalidades

### Player de Vídeo
- Suporte a YouTube e MP4
- Retoma do ponto onde parou
- Playlist lateral com navegação
- Materiais para download

### Calendário de Webinars Ao Vivo
- 4 slots mensais (1 por semana)
- Contador de vagas
- Link direto para inscrição no StreamYard
- Destaque visual para o próximo evento

### Webinars Gravados
- Grid de vídeos anteriores
- Modal com player integrado
- Materiais complementares

### Progresso
- Salvo automaticamente (localStorage)
- Indicador visual de progresso geral
- Status por módulo e aula

### Atalhos de Teclado
- `Esc` - Fechar modal
- `Ctrl + →` - Próxima aula
- `Ctrl + ←` - Aula anterior

---

## Personalização

### Cores (Nimbus Design System)

Edite as variáveis CSS no início de `styles.css`:

```css
:root {
    --primary-500: #5C4FD1;  /* Cor principal Nuvemshop */
    --success-500: #00A650;   /* Verde de sucesso */
    --danger-500: #E53935;    /* Vermelho para alertas */
}
```

### Adicionar Módulos

1. Adicione em `courseData` no `script.js`
2. Adicione o card HTML em `index.html` seguindo o padrão

### Adicionar Webinars Gravados

1. Adicione em `recordedWebinars` no `script.js`
2. Adicione o card na seção `recorded-grid` do `index.html`

---

## Tecnologias

- HTML5 semântico
- CSS3 (Custom Properties, Grid, Flexbox)
- JavaScript ES6+ (vanilla)
- YouTube IFrame API
- Design System: Nimbus (Nuvemshop)

---

## Checklist de Deploy

- [ ] Substituir todos os `SUBSTITUA_PELO_ID_REAL` pelos IDs dos vídeos
- [ ] Atualizar links do StreamYard para os webinars ao vivo
- [ ] Atualizar datas do calendário de webinars
- [ ] Verificar links de download dos materiais
- [ ] Testar em mobile
- [ ] Configurar domínio (se aplicável)

---

## Próximos Passos (Sugestões)

- [ ] Backend para persistir progresso do usuário
- [ ] Sistema de certificados ao completar a trilha
- [ ] Quiz/avaliação ao final de cada módulo
- [ ] Área de comentários/dúvidas
- [ ] Integração com Nuvemshop API para métricas
- [ ] Notificações de novos webinars
- [ ] Sistema de gamificação (badges, pontos)
