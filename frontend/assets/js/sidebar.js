import { apiFetch } from './api.js';

export async function loadConversations() {
    const response = await apiFetch("/conversations");
    return response.items;
}

export function renderConversationList(conversations, activeConversationId, onSelectCallback, onRenameCallback, onDeleteCallback) {
    const listEl = document.getElementById("conversation-list");
    if (!listEl) return;
    
    // Clear the existing list
    listEl.innerHTML = "";
    
    conversations.forEach(conversation => {
        const li = document.createElement("li");
        li.className = "conversation-item";
        
        if (conversation.id === activeConversationId) {
            li.classList.add("active");
        }
        
        // Clicking the item selects the conversation
        li.addEventListener("click", () => onSelectCallback(conversation.id));
        
        // Use textContent to prevent HTML injection from arbitrary titles
        const titleSpan = document.createElement("span");
        titleSpan.className = "conversation-title";
        titleSpan.textContent = conversation.title || "New Chat";
        li.appendChild(titleSpan);
        
        // Actions container
        const actionsDiv = document.createElement("div");
        actionsDiv.className = "conversation-actions";
        
        // Rename button
        const renameBtn = document.createElement("button");
        renameBtn.className = "btn btn-sm text-secondary border-0 py-0 px-1 me-1";
        renameBtn.innerHTML = "✏️";
        renameBtn.title = "Rename Chat";
        renameBtn.addEventListener("click", (e) => {
            e.stopPropagation(); // Don't trigger the li select click
            onRenameCallback(conversation.id, conversation.title);
        });
        
        // Delete button
        const deleteBtn = document.createElement("button");
        deleteBtn.className = "btn btn-sm text-secondary border-0 py-0 px-1";
        deleteBtn.innerHTML = "🗑️";
        deleteBtn.title = "Delete Chat";
        deleteBtn.addEventListener("click", (e) => {
            e.stopPropagation(); // Don't trigger the li select click
            onDeleteCallback(conversation.id);
        });
        
        actionsDiv.appendChild(renameBtn);
        actionsDiv.appendChild(deleteBtn);
        li.appendChild(actionsDiv);
        
        listEl.appendChild(li);
    });
}

export async function createNewConversation() {
    const response = await apiFetch("/conversations", {
        method: "POST"
    });
    return response;
}

export async function renameConversation(conversationId, newTitle) {
    const response = await apiFetch(`/conversations/${conversationId}`, {
        method: "PATCH",
        body: JSON.stringify({ title: newTitle })
    });
    return response;
}

export async function deleteConversation(conversationId) {
    await apiFetch(`/conversations/${conversationId}`, {
        method: "DELETE"
    });
}

export function filterConversations(conversations, searchTerm) {
    if (!searchTerm || !searchTerm.trim()) {
        return conversations;
    }
    
    const lowerTerm = searchTerm.toLowerCase();
    return conversations.filter(conv => 
        (conv.title || "").toLowerCase().includes(lowerTerm)
    );
}
