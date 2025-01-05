function setupSubmissionWebSocket() {
    const dataTranslator = document.getElementById("data-translator");

    const submissionId = dataTranslator.dataset.submissionId;
    const isChecking = dataTranslator.dataset.isChecking === "True";

    if (isChecking) {
        const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        const wsPath = wsProtocol + window.location.host + "/ws/submission/" + submissionId + "/";

        const socket = new WebSocket(wsPath);

        socket.onopen = function(event) {
            console.log("WebSocket successfully opened");
        };

        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            const testRow = document.getElementById(`test-${data.test_id}`);
            if (testRow) {
                testRow.cells[1].textContent = data.test_status;
                testRow.cells[2].textContent = data.test_execution_time;
                testRow.cells[3].textContent = data.test_memory_used;
            }

            const submissionStatus = document.getElementById("submission-status");
            submissionStatus.textContent = data.test_status;
        };

        socket.onclose = function(event) {
            console.log("Socket closed", event);
        };

        socket.onerror = function(event) {
            console.error("Socket error: ", event.data);
        };
    } else {
        console.log("Submission is already checked. Data loaded from template.");
    }
}

document.addEventListener("DOMContentLoaded", setupSubmissionWebSocket);