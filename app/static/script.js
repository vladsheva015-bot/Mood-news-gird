let currentMood = 'neutral';

const moodButtons = document.querySelectorAll('.mood-btn');
const newsGrid = document.getElementById('news-grid');
const refreshBtn = document.getElementById('refresh-btn');
const refreshStatus = document.getElementById('refresh-status');

moodButtons.forEach(btn => {
    btn.addEventListener('click', function() {
        moodButtons.forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        currentMood = this.dataset.mood;
        updateAllCards();
    });
});

async function updateAllCards() {
    const cards = document.querySelectorAll('.news-card');
    for (const card of cards) {
        const id = card.dataset.id;
        const rewrittenSpan = card.querySelector('.rewritten-text');
        if (rewrittenSpan) {
            rewrittenSpan.textContent = '⏳ Загрузка...';
        }
        try {
            const response = await fetch(`/api/news/${id}/${currentMood}`);
            const data = await response.json();
            if (data.rewritten && rewrittenSpan) {
                rewrittenSpan.textContent = data.rewritten;
            }
        } catch (error) {
            if (rewrittenSpan) {
                rewrittenSpan.textContent = 'Ошибка загрузки';
            }
        }
    }
}

newsGrid.addEventListener('click', async function(e) {
    const card = e.target.closest('.news-card');
    if (!card) return;
    const front = card.querySelector('.news-card-front');
    const back = card.querySelector('.news-card-back');
    if (e.target.closest('.read-more-btn') || e.target.closest('.news-card-front')) {
        if (front) front.style.display = 'none';
        if (back) back.style.display = 'flex';
        const rewrittenSpan = card.querySelector('.rewritten-text');
        if (rewrittenSpan && rewrittenSpan.textContent === 'Загрузка...') {
            const id = card.dataset.id;
            try {
                const response = await fetch(`/api/news/${id}/${currentMood}`);
                const data = await response.json();
                if (data.rewritten) {
                    rewrittenSpan.textContent = data.rewritten;
                }
            } catch (error) {
                rewrittenSpan.textContent = 'Ошибка загрузки';
            }
        }
    }
    if (e.target.closest('.close-btn')) {
        if (front) front.style.display = 'flex';
        if (back) back.style.display = 'none';
    }
});

refreshBtn.addEventListener('click', async function() {
    this.disabled = true;
    refreshStatus.textContent = 'Загрузка новостей...';
    try {
        const response = await fetch('/api/refresh');
        const result = await response.json();
        if (result.status === 'ok') {
            refreshStatus.textContent = `Загружено ${result.saved} новых новостей. Обновляем страницу...`;
            setTimeout(() => window.location.reload(), 1500);
        } else {
            refreshStatus.textContent = ` Ошибка: ${result.message}`;
        }
    } catch (error) {
        refreshStatus.textContent = ' Ошибка при обновлении';
    } finally {
        this.disabled = false;
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const activeBtn = document.querySelector('.mood-btn.active');
    if (activeBtn) {
        currentMood = activeBtn.dataset.mood;
    }
    setTimeout(updateAllCards, 500);
});