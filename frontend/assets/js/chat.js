import { apiFetch, getAccessToken, setAccessToken } from "./api.js";
import { 
    loadConversations, 
    renderConversationList, 
    createNewConversation, 
    renameConversation, 
    deleteConversation, 
    filterConversations 
} from "./sidebar.js";
import { streamQuery } from "./stream.js";
import { createMessageBubble, createTypingIndicator } from "../components/messageBubble.js";

// State
let conversations = [];
let activeConversationId = null;
let allConversationsCache = [];
let pendingDeleteConversationId = null;

// DOM Elements
const messagesContainer = document.getElementById("messages-container");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const newChatBtn = document.getElementById("new-chat-btn");
const chatSearch = document.getElementById("chat-search");
const logoutBtn = document.getElementById("logout-btn");
const currentConversationTitle = document.getElementById("current-conversation-title");
const currentTitleMobile = document.getElementById("current-title-mobile");
const userEmailDisplay = document.getElementById("user-email-display");
const toastContainer = document.getElementById("toast-container");
const sidebarToggleBtn = document.getElementById("sidebar-toggle-btn");
const sidebar = document.getElementById("sidebar");

// Modal Elements
const deleteModalEl = document.getElementById("delete-confirm-modal");
const deleteConfirmModal = new bootstrap.Modal(deleteModalEl);
const confirmDeleteBtn = document.getElementById("confirm-delete-btn");

// Initialization
async function init() {
    try {
        const me = await apiFetch("/auth/me");
        userEmailDisplay.textContent = me.email;
    } catch (e) {
        // Fallback to login if session isn't valid
        window.location.href = "login.html";
        return;
    }

    try {
        allConversationsCache = await loadConversations();
        conversations = [...allConversationsCache];
        
        reRenderSidebar();
        
        if (conversations.length > 0) {
            await selectConversation(conversations[0].id);
        } else {
            showEmptyState();
        }
    } catch (e) {
        showToast("Error loading conversations: " + e.message, "danger");
    }

    setupEventListeners();
}

function showEmptyState() {
    activeConversationId = null;
    messagesContainer.innerHTML = "<div class='text-center text-muted mt-5'>Start a new conversation to begin</div>";
    currentConversationTitle.textContent = "New Chat";
    currentTitleMobile.textContent = "New Chat";
    reRenderSidebar();
}

function reRenderSidebar() {
    renderConversationList(
        conversations, 
        activeConversationId, 
        selectConversation, 
        handleRename, 
        handleDelete
    );
}

async function selectConversation(conversationId) {
    activeConversationId = conversationId;
    reRenderSidebar();
    
    const conv = allConversationsCache.find(c => c.id === conversationId);
    if (conv) {
        currentConversationTitle.textContent = conv.title || "New Chat";
        currentTitleMobile.textContent = conv.title || "New Chat";
    }

    messagesContainer.innerHTML = "<div class='text-center text-muted mt-5'>Loading messages...</div>";

    try {
        const history = await apiFetch(`/conversations/${conversationId}/messages`);
        messagesContainer.innerHTML = "";
        
        if (!history.items || history.items.length === 0) {
            messagesContainer.innerHTML = "<div class='text-center text-muted mt-5'>No messages yet. Send a message to start!</div>";
        } else {
            history.items.forEach(msg => {
                messagesContainer.appendChild(createMessageBubble(msg.role, msg.content, msg.citations));
            });
        }
        
        scrollToBottom();
    } catch (e) {
        messagesContainer.innerHTML = "<div class='text-center text-danger mt-5'>Failed to load messages.</div>";
        showToast("Error loading messages: " + e.message, "danger");
    }
}

async function handleNewChat() {
    try {
        const newConv = await createNewConversation();
        allConversationsCache.unshift(newConv);
        conversations = filterConversations(allConversationsCache, chatSearch.value);
        
        await selectConversation(newConv.id);
        
        if (window.innerWidth < 768) {
            const bsOffcanvas = bootstrap.Offcanvas.getInstance(sidebar);
            if (bsOffcanvas) bsOffcanvas.hide();
        }
    } catch (e) {
        showToast("Error creating conversation: " + e.message, "danger");
    }
}

async function handleSendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    if (!activeConversationId) {
        await handleNewChat();
    }

    const targetConvId = activeConversationId;
    messageInput.value = "";
    messageInput.style.height = 'auto'; // Reset auto-growth

    // 1. User Message Setup
    messagesContainer.appendChild(createMessageBubble("user", text));
    scrollToBottom();

    let typingIndicator = createTypingIndicator();
    messagesContainer.appendChild(typingIndicator);
    scrollToBottom();

    // 2. Assistant Message Setup
    const assistantBubble = createMessageBubble("assistant", "");
    messagesContainer.appendChild(assistantBubble);
    
    // The text content is stored in the inner child div
    const contentDiv = assistantBubble.firstChild;
    let accumulatedText = "";

    // 3. Initiate Streaming Request
    await streamQuery(
        targetConvId, 
        text, 
        // onToken callback
        (token) => {
            if (typingIndicator) {
                typingIndicator.remove();
                typingIndicator = null;
            }
            accumulatedText += token;
            contentDiv.textContent = accumulatedText;
            scrollToBottom();
        },
        // onDone callback
        async (citations, messageId) => {
            if (typingIndicator) {
                typingIndicator.remove();
                typingIndicator = null;
            }
            
            if (citations && citations.length > 0) {
                appendCitationsToBubble(assistantBubble, citations);
                scrollToBottom();
            }

            try {
                // Refresh conversations to catch auto-generated title changes
                allConversationsCache = await loadConversations();
                conversations = filterConversations(allConversationsCache, chatSearch.value);
                reRenderSidebar();
                
                if (targetConvId === activeConversationId) {
                    const updatedConv = allConversationsCache.find(c => c.id === targetConvId);
                    if (updatedConv) {
                        currentConversationTitle.textContent = updatedConv.title;
                        currentTitleMobile.textContent = updatedConv.title;
                    }
                }
            } catch (e) {
                console.error("Failed to refresh conversations after sending message", e);
            }
        },
        // onError callback
        (errorMsg) => {
            if (typingIndicator) {
                typingIndicator.remove();
                typingIndicator = null;
            }
            showToast(errorMsg, "danger");
        }
    );
}

// Note: window.prompt is a quick prototype solution; a nicer inline-edit or modal UX is a future polish item.
async function handleRename(conversationId, currentTitle) {
    const newTitle = window.prompt("Rename chat:", currentTitle);
    if (newTitle !== null && newTitle.trim() !== "" && newTitle !== currentTitle) {
        try {
            await renameConversation(conversationId, newTitle.trim());
            
            allConversationsCache = await loadConversations();
            conversations = filterConversations(allConversationsCache, chatSearch.value);
            reRenderSidebar();
            
            if (conversationId === activeConversationId) {
                currentConversationTitle.textContent = newTitle.trim();
                currentTitleMobile.textContent = newTitle.trim();
            }
        } catch (e) {
            showToast("Failed to rename conversation: " + e.message, "danger");
        }
    }
}

function handleDelete(conversationId) {
    pendingDeleteConversationId = conversationId;
    deleteConfirmModal.show();
}

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendCitationsToBubble(bubbleElement, citations) {
    const citationList = document.createElement("div");
    citationList.className = "mt-2 pt-2 border-top border-light";
    citations.forEach(citation => {
        const badge = document.createElement("span");
        badge.className = "citation-badge";
        const docShort = citation.document_id ? citation.document_id.slice(0, 8) : "unknown";
        badge.textContent = `[${citation.rank}] Doc ${docShort} p.${citation.page_number}`;
        citationList.appendChild(badge);
    });
    bubbleElement.appendChild(citationList);
}

function showToast(message, type = "primary") {
    const toastDiv = document.createElement("div");
    toastDiv.className = `toast align-items-center text-bg-${type} border-0 show`;
    toastDiv.setAttribute("role", "alert");
    toastDiv.setAttribute("aria-live", "assertive");
    toastDiv.setAttribute("aria-atomic", "true");
    
    toastDiv.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;
    
    toastContainer.appendChild(toastDiv);
    
    // Automatically fade out after 5 seconds
    setTimeout(() => {
        toastDiv.classList.remove('show');
        setTimeout(() => toastDiv.remove(), 300);
    }, 5000);
}

function setupEventListeners() {
    newChatBtn.addEventListener("click", handleNewChat);
    sendBtn.addEventListener("click", handleSendMessage);
    
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Auto-resize textarea logic
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    let searchTimeout;
    chatSearch.addEventListener("input", (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            conversations = filterConversations(allConversationsCache, e.target.value);
            reRenderSidebar();
        }, 300);
    });
    
    logoutBtn.addEventListener("click", async () => {
        try {
            await apiFetch("/auth/logout", { method: "POST" });
        } catch (e) {
            console.error("Logout error", e);
        }
        setAccessToken(null);
        window.location.href = "login.html";
    });
    
    currentConversationTitle.addEventListener("click", () => {
        if (activeConversationId) {
            const conv = allConversationsCache.find(c => c.id === activeConversationId);
            if (conv) {
                handleRename(activeConversationId, conv.title);
            }
        }
    });
    
    sidebarToggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("show");
    });
    
    confirmDeleteBtn.addEventListener("click", async () => {
        if (!pendingDeleteConversationId) return;
        
        const targetId = pendingDeleteConversationId;
        confirmDeleteBtn.disabled = true;
        
        try {
            await deleteConversation(targetId);
            
            allConversationsCache = allConversationsCache.filter(c => c.id !== targetId);
            conversations = filterConversations(allConversationsCache, chatSearch.value);
            
            deleteConfirmModal.hide();
            
            if (activeConversationId === targetId) {
                if (conversations.length > 0) {
                    await selectConversation(conversations[0].id);
                } else {
                    showEmptyState();
                }
            } else {
                reRenderSidebar();
            }
        } catch (e) {
            showToast("Failed to delete conversation: " + e.message, "danger");
        } finally {
            confirmDeleteBtn.disabled = false;
            pendingDeleteConversationId = null;
        }
    });
}

// Start application
init();
