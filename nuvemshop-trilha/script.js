// ===========================================
// TRILHA DE SUCESSO - NUVEMSHOP
// Interactive Learning Path with Video Player
// ===========================================

// ===========================================
// COURSE DATA - Configure your videos here
// ===========================================
// 
// COMO CONFIGURAR SEUS VÍDEOS:
// 
// 1. Para vídeos do YouTube:
//    - videoType: "youtube"
//    - videoId: "ID_DO_VIDEO" (a parte após v= na URL)
//    - Exemplo: youtube.com/watch?v=ABC123 → videoId: "ABC123"
//
// 2. Para vídeos do StreamYard (após transmissão):
//    - Os vídeos do StreamYard ficam no YouTube após a live
//    - Use o mesmo formato do YouTube com o ID do vídeo
//
// 3. Para vídeos MP4 hospedados:
//    - videoType: "mp4"
//    - videoId: "https://seu-servidor.com/video.mp4"
//
// ===========================================

const courseData = {
    modules: [
        {
            id: 1,
            title: "Primeiros Passos",
            lessons: [
                {
                    id: "1-1",
                    title: "Criando sua conta na Nuvemshop",
                    duration: "5 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL", // Substitua pelo ID do vídeo real
                    completed: true,
                    resources: [
                        { title: "Checklist de criação de conta", url: "#" }
                    ]
                },
                {
                    id: "1-2",
                    title: "Tour completo pelo painel administrativo",
                    duration: "8 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: true,
                    resources: []
                },
                {
                    id: "1-3",
                    title: "Configurações essenciais da sua loja",
                    duration: "10 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: true,
                    resources: [
                        { title: "Guia de configurações", url: "#" }
                    ]
                }
            ]
        },
        {
            id: 2,
            title: "Cadastro de Produtos",
            lessons: [
                {
                    id: "2-1",
                    title: "Estrutura de um produto que vende",
                    duration: "7 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: true,
                    resources: []
                },
                {
                    id: "2-2",
                    title: "Como cadastrar seus primeiros produtos",
                    duration: "12 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    watchedSeconds: 180,
                    resources: [
                        { title: "Checklist de cadastro de produtos", url: "#" },
                        { title: "Template de descrição persuasiva", url: "#" }
                    ]
                },
                {
                    id: "2-3",
                    title: "Fotos de produtos que convertem",
                    duration: "15 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: [
                        { title: "Guia de fotografia de produtos", url: "#" },
                        { title: "Checklist de fotos", url: "#" }
                    ]
                },
                {
                    id: "2-4",
                    title: "Variações, estoque e organização",
                    duration: "10 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: [
                        { title: "Planilha de controle de estoque", url: "#" }
                    ]
                }
            ]
        },
        {
            id: 3,
            title: "Pagamentos e Frete",
            lessons: [
                {
                    id: "3-1",
                    title: "Escolhendo os melhores meios de pagamento",
                    duration: "10 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: [
                        { title: "Comparativo de gateways", url: "#" }
                    ]
                },
                {
                    id: "3-2",
                    title: "Configurando Nuvem Pago (passo a passo)",
                    duration: "8 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: []
                },
                {
                    id: "3-3",
                    title: "Opções de frete que funcionam",
                    duration: "12 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: [
                        { title: "Guia de transportadoras", url: "#" }
                    ]
                },
                {
                    id: "3-4",
                    title: "Calculadora de frete e frete grátis",
                    duration: "6 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: [
                        { title: "Planilha de cálculo de frete", url: "#" }
                    ]
                }
            ]
        },
        {
            id: 4,
            title: "Visual e Identidade",
            lessons: [
                {
                    id: "4-1",
                    title: "Escolhendo o tema perfeito para sua loja",
                    duration: "8 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: []
                },
                {
                    id: "4-2",
                    title: "Design que converte: personalizando com Canva",
                    duration: "15 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL", // Webinar real da Nuvemshop
                    completed: false,
                    resources: [
                        { title: "Templates Canva exclusivos", url: "#" },
                        { title: "Guia de cores e fontes", url: "#" }
                    ]
                },
                {
                    id: "4-3",
                    title: "Banners e destaques que vendem",
                    duration: "12 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: [
                        { title: "Pack de banners editáveis", url: "#" }
                    ]
                },
                {
                    id: "4-4",
                    title: "Páginas institucionais essenciais",
                    duration: "7 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: [
                        { title: "Templates de páginas", url: "#" }
                    ]
                }
            ]
        },
        {
            id: 5,
            title: "Primeiras Vendas",
            lessons: [
                {
                    id: "5-1",
                    title: "Estratégias de divulgação orgânica",
                    duration: "15 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: [
                        { title: "Calendário de conteúdo", url: "#" }
                    ]
                },
                {
                    id: "5-2",
                    title: "Automação de marketing: venda no piloto automático",
                    duration: "18 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL", // Case Vegpet - Webinar real
                    completed: false,
                    resources: [
                        { title: "Templates de e-mail", url: "#" },
                        { title: "Fluxo de automação", url: "#" }
                    ]
                },
                {
                    id: "5-3",
                    title: "Seu primeiro anúncio no Meta Ads",
                    duration: "20 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: [
                        { title: "Guia de Meta Ads", url: "#" },
                        { title: "Checklist de campanha", url: "#" }
                    ]
                },
                {
                    id: "5-4",
                    title: "Cupons e promoções estratégicas",
                    duration: "8 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: []
                }
            ]
        },
        {
            id: 6,
            title: "Lançamento da Loja",
            lessons: [
                {
                    id: "6-1",
                    title: "Checklist completo pré-lançamento",
                    duration: "10 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: [
                        { title: "Checklist de lançamento (PDF)", url: "#" }
                    ]
                },
                {
                    id: "6-2",
                    title: "Testando sua loja como um cliente",
                    duration: "8 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: []
                },
                {
                    id: "6-3",
                    title: "Ativando sua loja e domínio",
                    duration: "5 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL",
                    completed: false,
                    resources: []
                },
                {
                    id: "6-4",
                    title: "NuvemCommerce: tendências e próximos passos",
                    duration: "15 min",
                    videoType: "youtube",
                    videoId: "SUBSTITUA_PELO_ID_REAL", // Webinar NuvemCommerce real
                    completed: false,
                    resources: [
                        { title: "Relatório NuvemCommerce 2026", url: "#" },
                        { title: "Roadmap de crescimento", url: "#" }
                    ]
                }
            ]
        }
    ]
};

// ===========================================
// WEBINARS GRAVADOS - Configure aqui
// ===========================================
// Substitua os videoIds pelos IDs reais dos vídeos do YouTube/StreamYard
const recordedWebinars = {
    "webinar-1": {
        id: "webinar-1",
        title: "NuvemCommerce 2025: o que os dados revelam",
        description: "Análise completa das tendências do e-commerce brasileiro com dados exclusivos da plataforma.",
        duration: "58 min",
        date: "15 Jan 2026",
        videoType: "youtube",
        videoId: "SUBSTITUA_PELO_ID_REAL", // ID do vídeo do YouTube
        resources: [
            { title: "Relatório NuvemCommerce 2025 (PDF)", url: "#" },
            { title: "Slides da apresentação", url: "#" }
        ]
    },
    "webinar-2": {
        id: "webinar-2",
        title: "Como a Vegpet aumentou vendas com automação",
        description: "Case real de sucesso: e-mails automatizados e recuperação de carrinho abandonado.",
        duration: "45 min",
        date: "08 Jan 2026",
        videoType: "youtube",
        videoId: "SUBSTITUA_PELO_ID_REAL",
        resources: [
            { title: "Templates de e-mail da Vegpet", url: "#" },
            { title: "Fluxo de automação", url: "#" }
        ]
    },
    "webinar-3": {
        id: "webinar-3",
        title: "D2C Fashion Talks: vendendo moda online",
        description: "Estratégias das maiores marcas de moda para vender direto ao consumidor.",
        duration: "52 min",
        date: "18 Dez 2025",
        videoType: "youtube",
        videoId: "SUBSTITUA_PELO_ID_REAL",
        resources: [
            { title: "Guia D2C para moda", url: "#" }
        ]
    },
    "webinar-4": {
        id: "webinar-4",
        title: "Design que converte: Canva + Nuvemshop",
        description: "Workshop prático de design para criar materiais que vendem.",
        duration: "41 min",
        date: "11 Dez 2025",
        videoType: "youtube",
        videoId: "SUBSTITUA_PELO_ID_REAL",
        resources: [
            { title: "Templates Canva exclusivos", url: "#" },
            { title: "Guia de design para e-commerce", url: "#" }
        ]
    },
    "webinar-5": {
        id: "webinar-5",
        title: "Meta Ads do zero: sua primeira campanha",
        description: "Passo a passo completo para criar anúncios que convertem no Instagram e Facebook.",
        duration: "55 min",
        date: "04 Dez 2025",
        videoType: "youtube",
        videoId: "SUBSTITUA_PELO_ID_REAL",
        resources: [
            { title: "Checklist de campanha", url: "#" },
            { title: "Guia de públicos", url: "#" }
        ]
    },
    "webinar-6": {
        id: "webinar-6",
        title: "Black Friday: preparando sua loja para vender",
        description: "Estratégias, promoções e checklist completo para a maior data do e-commerce.",
        duration: "48 min",
        date: "20 Nov 2025",
        videoType: "youtube",
        videoId: "SUBSTITUA_PELO_ID_REAL",
        resources: [
            { title: "Checklist Black Friday", url: "#" },
            { title: "Planilha de promoções", url: "#" }
        ]
    }
};

// ===========================================
// WEBINARS AO VIVO - Configure aqui
// ===========================================
const liveWebinars = [
    {
        id: 1,
        date: "2026-01-23",
        time: "15:00",
        title: "Design que converte: como personalizar sua loja com Canva",
        description: "Aprenda técnicas práticas de design para criar banners, logos e materiais que aumentam suas vendas.",
        speaker: {
            name: "Marina Costa",
            role: "Designer @ Nuvemshop",
            avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=40&h=40&fit=crop&crop=face"
        },
        streamyardUrl: "https://streamyard.com/watch/SEU_LINK_AQUI",
        spotsLeft: 127
    },
    {
        id: 2,
        date: "2026-01-30",
        time: "15:00",
        title: "Automação de Marketing: venda mais no piloto automático",
        description: "Case Vegpet: como aumentar vendas com e-mails automatizados e recuperação de carrinho.",
        speaker: {
            name: "Ricardo Almeida",
            role: "Growth @ Nuvemshop",
            avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face"
        },
        streamyardUrl: "https://streamyard.com/watch/SEU_LINK_AQUI",
        spotsLeft: 284
    },
    {
        id: 3,
        date: "2026-02-06",
        time: "15:00",
        title: "D2C ou Marketplace? Estratégias para vender em múltiplos canais",
        description: "O que as grandes marcas ensinam sobre construir equilíbrio entre canais de venda.",
        speaker: {
            name: "Juliana Ferreira",
            role: "Head of Commerce @ Nuvemshop",
            avatar: "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=40&h=40&fit=crop&crop=face"
        },
        streamyardUrl: "https://streamyard.com/watch/SEU_LINK_AQUI",
        spotsLeft: 342
    },
    {
        id: 4,
        date: "2026-02-13",
        time: "15:00",
        title: "NuvemCommerce 2026: tendências e dados do e-commerce",
        description: "Análise exclusiva dos dados da plataforma e o que esperar para o mercado este ano.",
        speaker: {
            name: "Felipe Santos",
            role: "CEO @ Nuvemshop Brasil",
            avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=40&h=40&fit=crop&crop=face"
        },
        streamyardUrl: "https://streamyard.com/watch/SEU_LINK_AQUI",
        spotsLeft: 456
    }
];

// Current state
let currentLesson = null;
let youtubePlayer = null;
let isYouTubeAPIReady = false;

// ===========================================
// INITIALIZATION
// ===========================================
document.addEventListener('DOMContentLoaded', () => {
    loadYouTubeAPI();
    initProgressRing();
    initModuleCards();
    initSmoothScroll();
    initVideoThumbnails();
    initPlaylistItems();
});

// ===========================================
// YouTube API Integration
// ===========================================
function loadYouTubeAPI() {
    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    const firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
}

// Called automatically by YouTube API when ready
window.onYouTubeIframeAPIReady = function() {
    isYouTubeAPIReady = true;
    console.log('YouTube API Ready');
};

function createYouTubePlayer(videoId) {
    // Clear existing player
    const playerContainer = document.getElementById('videoPlayer');
    playerContainer.innerHTML = '';

    youtubePlayer = new YT.Player('videoPlayer', {
        height: '100%',
        width: '100%',
        videoId: videoId,
        playerVars: {
            'autoplay': 1,
            'modestbranding': 1,
            'rel': 0,
            'showinfo': 0,
            'controls': 1,
            'fs': 1
        },
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange
        }
    });
}

function onPlayerReady(event) {
    console.log('Player ready');
    // Resume from saved position if available
    if (currentLesson && currentLesson.watchedSeconds) {
        event.target.seekTo(currentLesson.watchedSeconds);
    }
}

function onPlayerStateChange(event) {
    if (event.data === YT.PlayerState.ENDED) {
        // Video ended - mark as complete
        markLessonComplete(currentLesson.id);
    }

    // Save progress periodically
    if (event.data === YT.PlayerState.PLAYING) {
        startProgressTracking();
    } else {
        stopProgressTracking();
    }
}

let progressInterval = null;

function startProgressTracking() {
    if (progressInterval) return;

    progressInterval = setInterval(() => {
        if (youtubePlayer && typeof youtubePlayer.getCurrentTime === 'function') {
            const currentTime = youtubePlayer.getCurrentTime();
            saveProgress(currentLesson.id, currentTime);
        }
    }, 5000); // Save every 5 seconds
}

function stopProgressTracking() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

// ===========================================
// Video Modal Functions
// ===========================================
function openVideoModal(lessonId) {
    const lesson = findLessonById(lessonId);
    if (!lesson) return;

    currentLesson = lesson;
    const modal = document.getElementById('videoModal');
    const moduleInfo = findModuleByLessonId(lessonId);

    // Update modal content
    document.querySelector('.video-modal-title').textContent = lesson.title;
    document.querySelector('.video-module-tag').textContent = `Módulo ${moduleInfo.id}`;

    // Update playlist
    updatePlaylist(moduleInfo);

    // Update resources
    updateResources(lesson.resources);

    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Load video
    if (isYouTubeAPIReady && lesson.videoType === 'youtube') {
        createYouTubePlayer(lesson.videoId);
    } else if (lesson.videoType === 'mp4') {
        loadMP4Video(lesson.videoId);
    } else {
        // Wait for API and retry
        setTimeout(() => openVideoModal(lessonId), 500);
    }
}

function closeVideoModal() {
    const modal = document.getElementById('videoModal');
    modal.classList.remove('active');
    document.body.style.overflow = '';

    // Stop and destroy player
    if (youtubePlayer) {
        stopProgressTracking();
        if (typeof youtubePlayer.stopVideo === 'function') {
            youtubePlayer.stopVideo();
        }
        youtubePlayer = null;
    }

    // Clear player container
    const playerContainer = document.getElementById('videoPlayer');
    if (playerContainer) {
        playerContainer.innerHTML = '';
    }
}

function loadMP4Video(videoUrl) {
    const playerContainer = document.getElementById('videoPlayer');
    playerContainer.innerHTML = `
        <video controls autoplay style="width: 100%; height: 100%;">
            <source src="${videoUrl}" type="video/mp4">
            Seu navegador não suporta o elemento de vídeo.
        </video>
    `;

    const video = playerContainer.querySelector('video');
    video.addEventListener('ended', () => {
        markLessonComplete(currentLesson.id);
    });
}

function updatePlaylist(module) {
    const playlistContainer = document.querySelector('.video-playlist');
    const completedCount = module.lessons.filter(l => l.completed).length;

    // Update progress
    document.querySelector('.module-progress-mini span').textContent = 
        `${completedCount}/${module.lessons.length} aulas`;
    document.querySelector('.progress-fill-mini').style.width = 
        `${(completedCount / module.lessons.length) * 100}%`;

    // Build playlist HTML
    playlistContainer.innerHTML = module.lessons.map(lesson => {
        const isActive = currentLesson && currentLesson.id === lesson.id;
        const statusClass = lesson.completed ? 'completed' : (isActive ? 'active' : '');
        const lessonIndex = module.lessons.indexOf(lesson) + 1;

        let statusIcon = '';
        if (lesson.completed) {
            statusIcon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>`;
        } else if (isActive) {
            statusIcon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
        } else {
            statusIcon = `<span class="playlist-number">${lessonIndex}</span>`;
        }

        return `
            <div class="playlist-item ${statusClass}" 
                 data-lesson-id="${lesson.id}" 
                 data-video-id="${lesson.videoId}" 
                 data-video-type="${lesson.videoType}"
                 onclick="switchLesson('${lesson.id}')">
                <div class="playlist-item-status ${isActive ? 'playing' : ''}">
                    ${statusIcon}
                </div>
                <div class="playlist-item-info">
                    <span class="playlist-item-title">${lesson.title}</span>
                    <span class="playlist-item-duration">${lesson.duration}</span>
                </div>
            </div>
        `;
    }).join('');
}

function updateResources(resources) {
    const resourcesContainer = document.querySelector('.video-resources');

    if (!resources || resources.length === 0) {
        resourcesContainer.style.display = 'none';
        return;
    }

    resourcesContainer.style.display = 'block';
    const resourcesHTML = resources.map(resource => `
        <a href="${resource.url}" class="resource-download" target="_blank">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
            </svg>
            <span>${resource.title}</span>
        </a>
    `).join('');

    resourcesContainer.innerHTML = `
        <h4>Materiais desta aula</h4>
        ${resourcesHTML}
    `;
}

function switchLesson(lessonId) {
    if (currentLesson && currentLesson.id === lessonId) return;

    const lesson = findLessonById(lessonId);
    if (!lesson) return;

    // Stop current video
    if (youtubePlayer && typeof youtubePlayer.stopVideo === 'function') {
        youtubePlayer.stopVideo();
    }

    currentLesson = lesson;

    // Update UI
    document.querySelector('.video-modal-title').textContent = lesson.title;
    updateResources(lesson.resources);

    // Update playlist active state
    const playlistItems = document.querySelectorAll('.playlist-item');
    playlistItems.forEach(item => {
        const itemLessonId = item.dataset.lessonId;
        item.classList.remove('active');
        if (itemLessonId === lessonId) {
            item.classList.add('active');
        }
    });

    // Load new video
    if (isYouTubeAPIReady && lesson.videoType === 'youtube') {
        youtubePlayer.loadVideoById(lesson.videoId);
    } else if (lesson.videoType === 'mp4') {
        loadMP4Video(lesson.videoId);
    }
}

function previousLesson() {
    const module = findModuleByLessonId(currentLesson.id);
    const currentIndex = module.lessons.findIndex(l => l.id === currentLesson.id);

    if (currentIndex > 0) {
        switchLesson(module.lessons[currentIndex - 1].id);
    }
}

function markAsCompleteAndNext() {
    markLessonComplete(currentLesson.id);

    const module = findModuleByLessonId(currentLesson.id);
    const currentIndex = module.lessons.findIndex(l => l.id === currentLesson.id);

    if (currentIndex < module.lessons.length - 1) {
        // Go to next lesson
        switchLesson(module.lessons[currentIndex + 1].id);
        updatePlaylist(module);
    } else {
        // Module complete - close modal and show celebration
        closeVideoModal();
        showModuleCompleteMessage(module);
    }
}

function markLessonComplete(lessonId) {
    const lesson = findLessonById(lessonId);
    if (lesson) {
        lesson.completed = true;
        updateProgressUI();

        // Update playlist if modal is open
        const module = findModuleByLessonId(lessonId);
        if (module && document.getElementById('videoModal').classList.contains('active')) {
            updatePlaylist(module);
        }

        // Save to localStorage
        saveUserProgress();
    }
}

function saveProgress(lessonId, seconds) {
    const lesson = findLessonById(lessonId);
    if (lesson) {
        lesson.watchedSeconds = seconds;
        localStorage.setItem('nuvemshop-trilha-progress', JSON.stringify(courseData));
    }
}

function showModuleCompleteMessage(module) {
    // Simple alert for now - could be replaced with a nice modal
    setTimeout(() => {
        alert(`Parabéns! Você completou o módulo "${module.title}"!`);
    }, 300);
}

// ===========================================
// Helper Functions
// ===========================================
function findLessonById(lessonId) {
    for (const module of courseData.modules) {
        const lesson = module.lessons.find(l => l.id === lessonId);
        if (lesson) return lesson;
    }
    return null;
}

function findModuleByLessonId(lessonId) {
    for (const module of courseData.modules) {
        if (module.lessons.find(l => l.id === lessonId)) {
            return module;
        }
    }
    return null;
}

// ===========================================
// Initialize Video Thumbnails
// ===========================================
function initVideoThumbnails() {
    const thumbnails = document.querySelectorAll('.lesson-thumbnail[data-video-id]');

    thumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', () => {
            const lessonId = thumbnail.dataset.lessonId;
            if (lessonId) {
                openVideoModal(lessonId);
            }
        });
    });
}

function initPlaylistItems() {
    // This is now handled in updatePlaylist with onclick
}

// ===========================================
// Progress Ring Animation
// ===========================================
function initProgressRing() {
    const progressRing = document.querySelector('.progress-ring-fill');
    if (!progressRing) return;

    const radius = 90;
    const circumference = 2 * Math.PI * radius;
    const progress = calculateTotalProgress();

    progressRing.style.strokeDasharray = `${circumference}`;

    // Animate on load
    setTimeout(() => {
        const offset = circumference - (progress / 100) * circumference;
        progressRing.style.strokeDashoffset = offset;
    }, 500);
}

function calculateTotalProgress() {
    let totalLessons = 0;
    let completedLessons = 0;

    courseData.modules.forEach(module => {
        totalLessons += module.lessons.length;
        completedLessons += module.lessons.filter(l => l.completed).length;
    });

    return Math.round((completedLessons / totalLessons) * 100);
}

// ===========================================
// Module Cards Interaction
// ===========================================
function initModuleCards() {
    const moduleCards = document.querySelectorAll('.module-card');

    moduleCards.forEach((card) => {
        const content = card.querySelector('.module-content');

        // Add hover effect for unlocked cards
        if (!card.classList.contains('locked')) {
            content.addEventListener('mouseenter', () => {
                content.style.transform = 'translateX(4px)';
            });

            content.addEventListener('mouseleave', () => {
                content.style.transform = 'translateX(0)';
            });
        }
    });

    // Make lesson items clickable
    const lessonItems = document.querySelectorAll('.lessons-preview .lesson-item');
    lessonItems.forEach((item, index) => {
        const moduleCard = item.closest('.module-card');
        if (moduleCard && !moduleCard.classList.contains('locked')) {
            item.style.cursor = 'pointer';
            item.addEventListener('click', () => {
                // Determine lesson ID based on module and position
                const moduleIndex = Array.from(document.querySelectorAll('.module-card')).indexOf(moduleCard);
                const lessonIndex = Array.from(item.parentElement.children).indexOf(item);
                const lessonId = `${moduleIndex + 1}-${lessonIndex + 1}`;
                openVideoModal(lessonId);
            });
        }
    });
}

// ===========================================
// Smooth Scroll Navigation
// ===========================================
function initSmoothScroll() {
    const navLinks = document.querySelectorAll('a[href^="#"]');

    navLinks.forEach((link) => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href && href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    const headerOffset = 80;
                    const elementPosition = target.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });

                    navLinks.forEach((l) => l.classList.remove('active'));
                    link.classList.add('active');
                }
            }
        });
    });
}

// ===========================================
// Progress Tracking
// ===========================================
function updateProgressUI() {
    const progress = calculateTotalProgress();

    // Update progress badge
    const progressBadge = document.querySelector('.progress-badge span:last-child');
    if (progressBadge) {
        progressBadge.textContent = `${progress}% concluído`;
    }

    // Update progress ring
    const progressPercentage = document.querySelector('.progress-percentage');
    if (progressPercentage) {
        progressPercentage.textContent = `${progress}%`;
    }

    // Animate progress ring
    const progressRing = document.querySelector('.progress-ring-fill');
    if (progressRing) {
        const radius = 90;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (progress / 100) * circumference;
        progressRing.style.strokeDashoffset = offset;
    }
}

function saveUserProgress() {
    localStorage.setItem('nuvemshop-trilha-progress', JSON.stringify(courseData));
}

function loadUserProgress() {
    const saved = localStorage.getItem('nuvemshop-trilha-progress');
    if (saved) {
        const savedData = JSON.parse(saved);
        // Merge saved progress with current course data
        savedData.modules.forEach((savedModule, mIndex) => {
            if (courseData.modules[mIndex]) {
                savedModule.lessons.forEach((savedLesson, lIndex) => {
                    if (courseData.modules[mIndex].lessons[lIndex]) {
                        courseData.modules[mIndex].lessons[lIndex].completed = savedLesson.completed;
                        courseData.modules[mIndex].lessons[lIndex].watchedSeconds = savedLesson.watchedSeconds;
                    }
                });
            }
        });
    }
}

// Load saved progress on init
loadUserProgress();

// ===========================================
// Keyboard Shortcuts
// ===========================================
document.addEventListener('keydown', (e) => {
    const modal = document.getElementById('videoModal');

    if (modal.classList.contains('active')) {
        // Escape to close
        if (e.key === 'Escape') {
            closeVideoModal();
        }

        // Arrow keys for navigation
        if (e.key === 'ArrowRight' && e.ctrlKey) {
            markAsCompleteAndNext();
        }

        if (e.key === 'ArrowLeft' && e.ctrlKey) {
            previousLesson();
        }
    }
});

// ===========================================
// Webinar Modal Functions
// ===========================================
function openWebinarModal(webinarId) {
    const webinar = recordedWebinars[webinarId];
    if (!webinar) {
        console.error('Webinar not found:', webinarId);
        return;
    }

    // Use the same video modal but with webinar data
    currentLesson = {
        id: webinar.id,
        title: webinar.title,
        videoType: webinar.videoType,
        videoId: webinar.videoId,
        resources: webinar.resources || []
    };

    const modal = document.getElementById('videoModal');

    // Update modal content for webinar
    document.querySelector('.video-modal-title').textContent = webinar.title;
    document.querySelector('.video-module-tag').textContent = 'Webinar Gravado';

    // Hide playlist sidebar for webinars (single video)
    const sidebar = document.querySelector('.video-sidebar');
    if (sidebar) {
        sidebar.innerHTML = `
            <div class="video-sidebar-header">
                <h3>Sobre este webinar</h3>
            </div>
            <div class="webinar-details" style="padding: var(--space-5); flex: 1;">
                <p style="color: var(--neutral-300); font-size: var(--font-size-sm); line-height: 1.6; margin-bottom: var(--space-4);">
                    ${webinar.description}
                </p>
                <div style="display: flex; gap: var(--space-4); margin-bottom: var(--space-4);">
                    <span style="font-size: var(--font-size-xs); color: var(--neutral-500);">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="vertical-align: middle; margin-right: 4px;">
                            <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.4 0-8-3.6-8-8s3.6-8 8-8 8 3.6 8 8-3.6 8-8 8zm.5-13H11v6l5.2 3.2.8-1.3-4.5-2.7V7z"/>
                        </svg>
                        ${webinar.duration}
                    </span>
                    <span style="font-size: var(--font-size-xs); color: var(--neutral-500);">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="vertical-align: middle; margin-right: 4px;">
                            <path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11z"/>
                        </svg>
                        ${webinar.date}
                    </span>
                </div>
            </div>
            ${webinar.resources && webinar.resources.length > 0 ? `
                <div class="video-resources">
                    <h4>Materiais do webinar</h4>
                    ${webinar.resources.map(r => `
                        <a href="${r.url}" class="resource-download" target="_blank">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
                            </svg>
                            <span>${r.title}</span>
                        </a>
                    `).join('')}
                </div>
            ` : ''}
        `;
    }

    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Update footer buttons for webinar
    const footer = document.querySelector('.video-modal-footer');
    footer.innerHTML = `
        <a href="https://www.nuvemshop.com.br/webinars" target="_blank" class="btn btn-ghost">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H8V4h12v12z"/></svg>
            Ver mais webinars
        </a>
        <button class="btn btn-primary" onclick="closeVideoModal()">
            Fechar
        </button>
    `;

    // Load video
    if (isYouTubeAPIReady && webinar.videoType === 'youtube') {
        createYouTubePlayer(webinar.videoId);
    } else if (webinar.videoType === 'mp4') {
        loadMP4Video(webinar.videoId);
    } else {
        setTimeout(() => openWebinarModal(webinarId), 500);
    }
}
