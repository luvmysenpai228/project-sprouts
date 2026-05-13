const API_BASE = "http://127.0.0.1:8000/api/v1";

// NAV
const homeBtn = document.getElementById("homeBtn");
const settingsBtn = document.getElementById("settingsBtn");

const mainContent = document.getElementById("mainContent");
const settingsPage = document.getElementById("settingsPage");

// MODAL UPLOAD
const modalOverlay = document.getElementById("modalOverlay");
const addLink = document.querySelector(".link");

// LOGIN
const loginBtn = document.getElementById("loginBtn");
const loginPage = document.getElementById("loginPage");
const closeLogin = document.getElementById("closeLogin");

// FILE UPLOAD
const fileInput = document.getElementById("fileInput");
const uploadBtn = document.querySelector(".modal__btn");

// IMAGE VIEWER
const imageViewer = document.getElementById("imageViewer");
const viewerImg = document.getElementById("viewerImg");
const closeViewer = document.getElementById("closeViewer");



// настройки
settingsBtn.addEventListener("click", () => {
    settingsBtn.classList.add("nav__btn--active");
    homeBtn.classList.remove("nav__btn--active");

    mainContent.classList.add("hidden");
    settingsPage.classList.remove("hidden");
});

// главная
homeBtn.addEventListener("click", () => {
    homeBtn.classList.add("nav__btn--active");
    settingsBtn.classList.remove("nav__btn--active");

    mainContent.classList.remove("hidden");
    settingsPage.classList.add("hidden");
});


loginBtn.addEventListener("click", () => {
    loginPage.classList.remove("hidden");
});

closeLogin.addEventListener("click", () => {
    loginPage.classList.add("hidden");
});


// открыть
addLink.addEventListener("click", (e) => {
    e.preventDefault();
    modalOverlay.classList.remove("hidden");
});

// закрыть по фону
modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) {
        modalOverlay.classList.add("hidden");
    }
});


// открыть выбор файла
uploadBtn.addEventListener("click", () => {
    fileInput.click();
});

// отправка
fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    if (!file) return;

    try {
        const formData = new FormData();
        formData.append("image", file);

        await fetch(`${API_BASE}/images/`, {
            method: "POST",
            body: formData
        });

        loadImages(); // обновить список
        modalOverlay.classList.add("hidden");

    } catch (e) {
        console.error("Ошибка загрузки файла", e);
    }
});



async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/stats/`);
        const data = await res.json();

        document.querySelector(".stats").innerHTML = `
            <h2 class="card__title">Статистика по росткам</h2>
            <p>Всего ростков: ${data.total}</p>
            <p>Новых ростков за сегодня: ${data.today_increment}</p>
        `;
    } catch (e) {
        console.error("Ошибка загрузки статистики", e);
    }
}



async function loadImages() {
    try {
        const res = await fetch(`${API_BASE}/images/`);
        const images = await res.json();

        const list = document.querySelector(".image-list");
        list.innerHTML = "";

        images.forEach(img => {
            const el = document.createElement("div");
            el.className = "image-item";

            el.innerHTML = `
                <div>
                    <strong>${img.segment_title}</strong>
                    <div>
                        ростков: ${img.detected_qty}
                        ${img.detected_qty_increment ? `(+${img.detected_qty_increment})` : ""}
                    </div>
                </div>
                <div class="image-item__right">
                    <span>${img.date_of_image}</span>
                    <button class="eye">👁</button>
                </div>
            `;

            // 👁 ОБРАБОТКА КНОПКИ
            const eyeBtn = el.querySelector(".eye");

            eyeBtn.addEventListener("click", () => {
                const imageUrl = `http://127.0.0.1:8000${img.original_image}`;
                viewerImg.src = imageUrl;
                imageViewer.classList.remove("hidden");
            });

            list.appendChild(el);
        });

    } catch (e) {
        console.error("Ошибка загрузки изображений", e);
    }
}



// закрыть крестиком
closeViewer.addEventListener("click", () => {
    imageViewer.classList.add("hidden");
});

// закрыть по фону
imageViewer.addEventListener("click", (e) => {
    if (e.target === imageViewer) {
        imageViewer.classList.add("hidden");
    }
});



loadStats();
loadImages();