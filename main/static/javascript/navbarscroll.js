const navbar = document.getElementById("navbar-home");

window.addEventListener("scroll", function() {
    let scrollTop = window.pageYOffset || document.documentElement.scrollTop;

    if (scrollTop > 80) {
        // Scorrendo verso il basso
        navbar.classList.add("hidden");
    } else {
        // Scorrendo verso l'alto
        navbar.classList.remove("hidden");
    }
});