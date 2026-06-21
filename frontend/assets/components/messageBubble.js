export function createMessageBubble(role, content, citations = []) {
    const bubble = document.createElement("div");
    // Add the base class and the role class ("user" or "assistant")
    bubble.className = `message-bubble ${role}`;

    // Note: We use textContent (NOT innerHTML) to avoid XSS from rendered message content.
    // This means we are not rendering markdown formatting in this version (no bold/lists/etc 
    // render specially), which is an acceptable simplification for the prototype; if markdown 
    // rendering is added later it must go through a sanitizing markdown renderer, never raw innerHTML.
    const contentDiv = document.createElement("div");
    contentDiv.style.whiteSpace = "pre-wrap"; // Preserve line breaks visually for plain text
    contentDiv.textContent = content;
    
    bubble.appendChild(contentDiv);

    // If citations are provided and it's an assistant message, append them
    if (role === "assistant" && citations && citations.length > 0) {
        const citationList = document.createElement("div");
        citationList.className = "mt-2 pt-2 border-top border-light";
        
        // Note: Phase 6.x follow-up: join citations to actual document titles for a nicer display
        citations.forEach(citation => {
            const badge = document.createElement("span");
            badge.className = "citation-badge";
            
            // Just show a shortened id since we don't have document titles wired into the citation data yet
            const docShort = citation.document_id ? citation.document_id.slice(0, 8) : "unknown";
            badge.textContent = `[${citation.rank}] Doc ${docShort} p.${citation.page_number}`;
            
            citationList.appendChild(badge);
        });
        
        bubble.appendChild(citationList);
    }

    return bubble;
}

export function createTypingIndicator() {
    const indicator = document.createElement("div");
    indicator.className = "typing-indicator";
    
    // Append the three animated dots as defined in chat.css
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement("span");
        dot.className = "typing-dot";
        indicator.appendChild(dot);
    }
    
    return indicator;
}
