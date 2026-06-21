import { getAccessToken } from './api.js';

/**
 * Note: This does not handle the 401-refresh-retry logic that api.js's apiFetch handles 
 * for regular requests. If the access token expires mid-conversation, the stream will 
 * fail with a 401 and the user will need to refresh the page to get a new token via a regular 
 * apiFetch call elsewhere, which would trigger the silent refresh. This is acceptable 
 * for the prototype given access tokens last 15 minutes.
 */
export async function streamQuery(conversationId, question, onToken, onDone, onError) {
    try {
        const response = await fetch("http://localhost:8000/api/v1/chat/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${getAccessToken()}`
            },
            credentials: "include",
            body: JSON.stringify({
                conversation_id: conversationId,
                question: question
            })
        });

        if (!response.ok) {
            onError(`Server error: ${response.status} ${response.statusText}`);
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            let eventEndIndex;
            while ((eventEndIndex = buffer.indexOf('\n\n')) >= 0) {
                const eventChunk = buffer.substring(0, eventEndIndex).trim();
                buffer = buffer.substring(eventEndIndex + 2);

                if (!eventChunk.startsWith('data: ')) {
                    continue;
                }

                const jsonStr = eventChunk.substring(6); // Strip 'data: '
                let event;
                try {
                    event = JSON.parse(jsonStr);
                } catch (e) {
                    console.error("Failed to parse stream JSON:", jsonStr);
                    continue;
                }

                if (event.type === "token") {
                    onToken(event.content);
                } else if (event.type === "done") {
                    onDone(event.citations, event.message_id);
                    return; // Break the loop and stop reading
                } else if (event.type === "error") {
                    onError(event.message || "Stream returned an error event");
                    return; // Break the loop and stop reading
                }
            }
        }
    } catch (err) {
        onError(err.message || "An error occurred during the stream connection");
    }
}
