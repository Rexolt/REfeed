document.addEventListener("DOMContentLoaded", function () {
    const rssContainer = document.getElementById('rss-container');
    const rssForm = document.getElementById('rss-form');
    const rssUrlInput = document.getElementById('rss-url');
    const cityInput = document.getElementById('city-input');
    const saveCityBtn = document.getElementById('save-city-btn');
    const notificationBox = document.getElementById('notification-box');

    const defaultLogo = "static/logo.png";  // Az alapértelmezett logó, ha nincs kép

    // Értesítés megjelenítése
    function showNotification(message, type) {
        notificationBox.innerText = message;
        notificationBox.className = `notification ${type}`;
        notificationBox.style.display = 'block';
        setTimeout(() => {
            notificationBox.style.display = 'none';
        }, 3000); // Az értesítés 3 másodpercig látszik
    }

    // Város beállítása
    saveCityBtn.addEventListener('click', function () {
        const city = cityInput.value.trim();
        if (city) {
            fetch('/set_city', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ city: city }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showNotification(data.message, 'success'); // Zöld értesítés
                } else {
                    showNotification(data.message, 'error'); // Piros értesítés
                }
            })
            .catch(error => {
                showNotification('Hiba történt a város beállítása közben!', 'error');
            });
        }
    });

    // RSS feed betöltése
    function loadRSS(feedUrl) {
        fetch(`/rss?feed_url=${encodeURIComponent(feedUrl)}`)
            .then(response => response.json())
            .then(data => {
                rssContainer.innerHTML = '';
                if (data.length === 0) {
                    rssContainer.innerHTML = '<p>Nincsenek hírek elérhetőek.</p>';
                } else {
                    data.forEach(article => {
                        const articleElement = document.createElement('div');
                        articleElement.classList.add('article');

                        const imageHtml = article.image
                            ? `<img src="${article.image}" alt="Borítókép" class="article-image">`
                            : `<img src="${defaultLogo}" alt="Hírportál logó" class="article-image">`;

                        const isLiked = article.is_liked ? 'liked' : '';
                        const redirectLink = `/redirect?url=${encodeURIComponent(article.link)}`;

                        articleElement.innerHTML = `
                            ${imageHtml}
                            <div class="article-title">${article.title}</div>
                            <div class="article-date">${article.published}</div>
                            <a href="${redirectLink}" class="article-link">Tovább olvasom</a>
                            <div class="heart ${isLiked}" data-title="${article.title}" data-link="${article.link}" data-published="${article.published}"></div>
                        `;

                        rssContainer.appendChild(articleElement);
                    });

                    // Szív ikon eseménykezelés
                    document.querySelectorAll('.heart').forEach(heart => {
                        heart.addEventListener('click', function () {
                            const title = this.getAttribute('data-title');
                            const link = this.getAttribute('data-link');
                            const published = this.getAttribute('data-published');

                            fetch('/favorites/toggle', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({ title, link, published }),
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.status === 'added') {
                                    this.classList.add('liked');
                                } else if (data.status === 'removed') {
                                    this.classList.remove('liked');
                                }
                            });
                        });
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                rssContainer.innerHTML = '<p>Hiba történt az RSS feed betöltésekor.</p>';
            });
    }

    rssForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const feedUrl = rssUrlInput.value.trim();
        if (feedUrl) {
            loadRSS(feedUrl);
            rssUrlInput.value = '';
        }
    });

    // Alapértelmezett RSS feed betöltése
    loadRSS('https://index.hu/24ora/rss/');
});
