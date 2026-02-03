# 🚀 Setup - Deploy no Vercel

## Passo 1: Inicializar Git

Abra o Terminal e execute:

```bash
cd /Users/renatovieira/Downloads/dashboard-webinar-insights
git init
git add .
git commit -m "Initial commit: Dashboard de Impacto - Webinars"
```

## Passo 2: Criar repositório no GitHub

1. Acesse [github.com/new](https://github.com/new)
2. Nome do repositório: `dashboard-webinar-insights`
3. Deixe como **Privado** (dados sensíveis)
4. NÃO marque "Add a README file"
5. Clique em **Create repository**

## Passo 3: Conectar e enviar

Após criar, execute no Terminal:

```bash
cd /Users/renatovieira/Downloads/dashboard-webinar-insights
git remote add origin https://github.com/SEU-USUARIO/dashboard-webinar-insights.git
git branch -M main
git push -u origin main
```

## Passo 4: Deploy no Vercel

1. Acesse [vercel.com](https://vercel.com) e faça login com GitHub
2. Clique em **"Add New..."** → **"Project"**
3. Selecione o repositório `dashboard-webinar-insights`
4. Clique em **"Deploy"**
5. Aguarde o deploy (cerca de 30 segundos)

## ✅ Pronto!

Você receberá uma URL tipo: `https://dashboard-webinar-insights.vercel.app`

---

## 🔄 Para atualizar os dados futuramente

1. Execute o script Python com as novas bases
2. Copie o HTML gerado para `index.html`
3. Faça commit e push:

```bash
cd /Users/renatovieira/Downloads/dashboard-webinar-insights
git add .
git commit -m "Atualização dos dados"
git push
```

O Vercel fará o redeploy automaticamente!
