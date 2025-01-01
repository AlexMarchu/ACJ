let menus;

function hideAllMenus() {
    menus.forEach((element) => {
        element.querySelector(".menu-content").style.display = "none";
    });
}

function setupMenus() {
    menus = document.querySelectorAll(".menu");
    document.addEventListener("click", hideAllMenus);

    menus.forEach((element) => {
        element.querySelector(".menu-trigger").addEventListener("click", (event) => {
            let content = element.querySelector(".menu-content");
            let display = content.style.display;
            hideAllMenus();
            if (!display || display === "none") {
                content.style.display = "block";
            } else {
                content.style.display = "none";
            }
            event.stopPropagation();
        });
    });
}

window.addEventListener("load", setupMenus);