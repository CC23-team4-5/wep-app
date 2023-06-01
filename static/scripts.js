function analyze() {
    $("#result").text(""); // Clear the old message
    const review = $("#text-input").val();
    $.post("/analyze", {review: review}, function (data) {
        console.log(data);
        $("#result").text(data.prediction > "0" ? "😊" : "☹️");
    }).fail(function () {
        $("#result").text("Error");
    });
}

function unfog() {
    $("#additional-info").removeClass("foggy");
    $("#unfog-button").prop("disabled", true);
}

$(document).ready(function () {
    $("#submit-button").on("click", analyze);
    $("#unfog-button").on("click", unfog);
});
