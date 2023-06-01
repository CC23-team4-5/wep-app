function submit() {
    $("#result").text(""); // Clear the old message
    const review = $("#text-input").val();
    $.post("/submit", {review: review}, function (data) {
        console.log(data);
        $("#result").text(data.message);
    }).fail(function () {
        $("#result").text("Error");
    });
}

function unfog() {
    $("#additional-info").removeClass("foggy");
    $("#unfog-button").prop("disabled", true);
}

function nextTask() {
    $.get("/next_task", function (data) {
        $("#task-description").val(data.task_description);
    });
}

function nextInfo() {
    $.get("/next_info", function (data) {
        $("#additional-info").val(data.additional_info);
    });
}

$(document).ready(function () {
    $("#submit-button").on("click", submit);
    $("#unfog-button").on("click", unfog);
    $("#next-task").on("click", nextTask);
    $("#next-info").on("click", nextInfo);
});