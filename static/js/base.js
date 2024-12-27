function selectNavbarItem(item) {
    document.getElementById(`${item}-item`).classList.add("selected-navbar-item");
}

var menus;

function onLoad() {
    this.menus = document.querySelectorAll(".menu");
    document.addEventListener("click", (event) => {
        this.menus.forEach((element) => {
            element.querySelector(".menu-content").style.display = "none";
        });
    });
    this.menus.forEach((element) => {
        element.querySelector(".menu-trigger").addEventListener("click", (event) => {
            var content = element.querySelector(".menu-content");
            if (!content.style.display || content.style.display === "none") {
                content.style.display = "block";
            } else {
                content.style.display = "none";
            }
            event.stopPropagation();
        });
    });
}

window.addEventListener("load", onLoad);