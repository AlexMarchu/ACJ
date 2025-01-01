function setupFavoriteButtons() {
    function handleFavoriteButtonClick(event) {
        event.preventDefault();
        const button = event.currentTarget;
        const contestId = button.dataset.contestId;

        axios.post(button.href, {}, {
            headers: {
                "Content-Type": "application/json",
                "X-CSRFTOKEN": button.dataset.csrfToken,
            },
        })
        .then(response => {
            if (response.data.status === "created") {
                button.querySelector("i").classList.add("favorite");
            } else {
                button.querySelector("i").classList.remove("favorite");
            }
        })
        .catch(error => {
            console.log("Error", error);
        });
    }

    const favoriteButtons = document.querySelectorAll(".favorite-btn");
    favoriteButtons.forEach(button => {
        button.addEventListener("click", handleFavoriteButtonClick);
    });
}

document.addEventListener("DOMContentLoaded", setupFavoriteButtons);
