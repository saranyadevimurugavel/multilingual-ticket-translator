const hamburger =
document.querySelector(".hamburger");

const sidebar =
document.querySelector(".sidebar");

if (hamburger) {

    hamburger.addEventListener(
        "click",
        function () {

            sidebar.classList.toggle(
                "active"
            );

        }
    );

}