// Frontend JavaScript para Agente de Predicción de Demanda

// Elementos DOM
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const chatForm = document.getElementById('chatForm');
const sendButton = document.getElementById('sendButton');
const sendIcon = document.getElementById('sendIcon');
const loadingIcon = document.getElementById('loadingIcon');
const statsContent = document.getElementById('stats-content');

// Cargar estadísticas al iniciar
loadStats();

// Enviar mensaje
async function sendMessage(event) {
    event.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Agregar mensaje del usuario al chat
    addMessage(message, 'user');
    
    // Limpiar input
    messageInput.value = '';
    
    // Mostrar indicador de carga
    setLoading(true);
    
    try {
        // Enviar al backend
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Agregar respuesta del bot
        addMessage(data.response, 'bot');
        
    } catch (error) {
        console.error('Error:', error);
        addMessage('Lo siento, ocurrió un error al procesar tu consulta. Por favor intenta nuevamente.', 'bot', true);
    } finally {
        setLoading(false);
    }
}

// Agregar mensaje al chat
function addMessage(text, sender, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (isError) {
        contentDiv.style.backgroundColor = '#fee2e2';
        contentDiv.style.color = '#991b1b';
    }
    
    // Convertir saltos de línea a <br> y formatear listas
    const formattedText = formatMessageText(text);
    contentDiv.innerHTML = formattedText;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll al final
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Formatear texto del mensaje
function formatMessageText(text) {
    // Convertir saltos de línea a <br>
    let formatted = text.replace(/\n/g, '<br>');
    
    // Detectar y formatear listas (líneas que empiezan con -)
    formatted = formatted.replace(/- (.+?)<br>/g, '<li>$1</li>');
    
    // Envolver listas en <ul>
    if (formatted.includes('<li>')) {
        formatted = formatted.replace(/(<li>.*<\/li>)+/g, '<ul>$&</ul>');
    }
    
    // Formatear negritas (**texto**)
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Formatear párrafos
    if (!formatted.includes('<ul>')) {
        formatted = formatted.split('<br><br>').map(p => `<p>${p}</p>`).join('');
    }
    
    return formatted;
}

// Enviar pregunta rápida
function sendQuickQuestion(question) {
    messageInput.value = question;
    chatForm.dispatchEvent(new Event('submit'));
}

// Controlar estado de carga
function setLoading(loading) {
    sendButton.disabled = loading;
    messageInput.disabled = loading;
    
    if (loading) {
        sendIcon.style.display = 'none';
        loadingIcon.style.display = 'inline';
    } else {
        sendIcon.style.display = 'inline';
        loadingIcon.style.display = 'none';
    }
}

// Cargar estadísticas
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) return;
        
        const stats = await response.json();
        
        statsContent.innerHTML = `
            <p>📊 <strong>${stats.total_predicciones || 0}</strong> predicciones</p>
            <p>🏥 <strong>${stats.total_hospitales || 0}</strong> hospitales</p>
            <p>💊 <strong>${stats.total_productos || 0}</strong> productos</p>
            <p>💬 <strong>${stats.total_consultas || 0}</strong> consultas</p>
        `;
    } catch (error) {
        statsContent.innerHTML = '<p>Error cargando stats</p>';
    }
}

// Recargar stats cada 30 segundos
setInterval(loadStats, 30000);

// Autocompletar con Enter
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});
