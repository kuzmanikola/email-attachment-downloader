const form = document.getElementById('emailForm');
const submitBtn = document.getElementById('submitBtn');
const btnText = document.querySelector('.btn-text');
const btnLoader = document.querySelector('.btn-loader');
const progressCard = document.getElementById('progressCard');
const filesCard = document.getElementById('filesCard');
const statusMessage = document.getElementById('statusMessage');
const progressText = document.getElementById('progressText');
const downloadText = document.getElementById('downloadText');
const progressFill = document.getElementById('progressFill');
const filesList = document.getElementById('filesList');

let progressInterval = null;

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        email_address: document.getElementById('email_address').value,
        app_password: document.getElementById('app_password').value,
        sender_mail: document.getElementById('sender_mail').value,
        start_date: document.getElementById('start_date').value,
        end_date: document.getElementById('end_date').value
    };
    
    // Disable form
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'block';
    
    // Show progress card
    progressCard.style.display = 'block';
    filesCard.style.display = 'none';
    filesList.innerHTML = '';
    
    try {
        const response = await fetch('/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to start processing');
        }
        
        // Start polling for progress
        startProgressPolling();
        
    } catch (error) {
        alert('Error: ' + error.message);
        resetForm();
    }
});

function startProgressPolling() {
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch('/progress');
            const data = await response.json();
            
            updateProgress(data);
            
            if (data.status === 'completed' || data.status === 'error') {
                stopProgressPolling();
                resetForm();
                
                if (data.status === 'completed' && data.files.length > 0) {
                    displayFiles(data.files);
                }
            }
        } catch (error) {
            console.error('Error fetching progress:', error);
        }
    }, 500);
}

function stopProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

function updateProgress(data) {
    statusMessage.textContent = data.message;
    
    // Update status class
    statusMessage.className = '';
    if (data.status === 'connecting') {
        statusMessage.classList.add('status-connecting');
    } else if (data.status === 'completed') {
        statusMessage.classList.add('status-completed');
    } else if (data.status === 'error') {
        statusMessage.classList.add('status-error');
    }
    
    // Update progress text
    if (data.total > 0) {
        progressText.textContent = `${data.progress} / ${data.total} emails`;
        downloadText.textContent = `${data.downloads} PDF${data.downloads !== 1 ? 's' : ''} downloaded`;
        
        const percentage = (data.progress / data.total) * 100;
        progressFill.style.width = `${percentage}%`;
    } else {
        progressText.textContent = 'Processing...';
        downloadText.textContent = '';
        progressFill.style.width = '0%';
    }
}

function displayFiles(files) {
    filesCard.style.display = 'block';
    filesList.innerHTML = '';
    
    if (files.length === 0) {
        filesList.innerHTML = '<div class="empty-state">No files downloaded</div>';
        return;
    }
    
    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        
        fileItem.innerHTML = `
            <div class="file-name">📄 ${file.name}</div>
            <div class="file-meta">
                <div><strong>From:</strong> ${file.from}</div>
                <div><strong>Subject:</strong> ${file.subject || 'No subject'}</div>
                <div><strong>Date:</strong> ${file.date}</div>
            </div>
            <div class="file-actions">
                <a href="/downloads/${encodeURIComponent(file.name)}" class="btn btn-small btn-download" download>
                    Download
                </a>
            </div>
        `;
        
        filesList.appendChild(fileItem);
    });
}

function resetForm() {
    submitBtn.disabled = false;
    btnText.style.display = 'block';
    btnLoader.style.display = 'none';
}

// Set default dates (last 30 days)
const today = new Date();
const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

document.getElementById('end_date').valueAsDate = today;
document.getElementById('start_date').valueAsDate = thirtyDaysAgo;

