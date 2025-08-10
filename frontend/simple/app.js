// GitHub PR Metrics Analyzer - Frontend JavaScript

const API_BASE = 'http://localhost:8000';
let currentTaskId = null;
let wsConnection = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Set up event listeners
    document.getElementById('analysisForm').addEventListener('submit', handleFormSubmit);
    document.getElementById('toggleToken').addEventListener('click', toggleTokenVisibility);
    document.getElementById('exportBtn').addEventListener('click', exportCSV);
    
    // Check backend health
    checkBackendHealth();
}

async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        if (response.ok) {
            console.log('✅ Backend is running');
        } else {
            showAlert('Backend is not responding. Please make sure the FastAPI server is running on port 8000.', 'warning');
        }
    } catch (error) {
        showAlert('Cannot connect to backend. Please start the FastAPI server first.', 'danger');
    }
}

function toggleTokenVisibility() {
    const tokenInput = document.getElementById('githubToken');
    const toggleBtn = document.getElementById('toggleToken');
    const icon = toggleBtn.querySelector('i');
    
    if (tokenInput.type === 'password') {
        tokenInput.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        tokenInput.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

async function handleFormSubmit(event) {
    event.preventDefault();
    
    const formData = {
        github_url: document.getElementById('githubUrl').value,
        github_token: document.getElementById('githubToken').value,
        since: document.getElementById('sinceDate').value || null,
        until: document.getElementById('untilDate').value || null
    };
    
    // Validate GitHub URL
    if (!isValidGitHubUrl(formData.github_url)) {
        showAlert('Please enter a valid GitHub repository URL', 'danger');
        return;
    }
    
    // Start analysis
    await startAnalysis(formData);
}

function isValidGitHubUrl(url) {
    const githubRegex = /^https:\/\/github\.com\/[a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+\/?$/;
    return githubRegex.test(url);
}

async function startAnalysis(formData) {
    try {
        // Show loading state
        showLoadingState(true);
        
        // Start analysis
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }
        
        const result = await response.json();
        currentTaskId = result.task_id;
        
        // Show progress section
        showProgressSection();
        
        // Connect to WebSocket for real-time updates
        connectWebSocket(currentTaskId);
        
        // Poll for results
        pollForResults(currentTaskId);
        
    } catch (error) {
        showLoadingState(false);
        showAlert(`Error starting analysis: ${error.message}`, 'danger');
    }
}

function connectWebSocket(taskId) {
    const wsUrl = `ws://localhost:8000/ws/${taskId}`;
    wsConnection = new WebSocket(wsUrl);
    
    wsConnection.onopen = () => {
        console.log('🔗 WebSocket connected');
    };
    
    wsConnection.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    wsConnection.onclose = () => {
        console.log('🔌 WebSocket disconnected');
    };
}

function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'progress':
            updateProgress(message.data.progress, message.data.message);
            break;
        case 'completed':
            updateProgress(100, 'Analysis completed!');
            setTimeout(() => {
                displayResults(message.data.results);
            }, 1000);
            break;
        case 'error':
            showAlert(`Analysis error: ${message.data.error}`, 'danger');
            hideProgressSection();
            showLoadingState(false);
            break;
    }
}

async function pollForResults(taskId) {
    const maxAttempts = 60; // 5 minutes maximum
    let attempts = 0;
    
    const poll = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/analysis/${taskId}`);
            const result = await response.json();
            
            if (result.status === 'completed') {
                displayResults(result.results);
                return;
            }
            
            if (result.status === 'failed') {
                throw new Error(result.error || 'Analysis failed');
            }
            
            // Continue polling
            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(poll, 5000); // Poll every 5 seconds
            } else {
                throw new Error('Analysis timeout');
            }
            
        } catch (error) {
            showAlert(`Error: ${error.message}`, 'danger');
            hideProgressSection();
            showLoadingState(false);
        }
    };
    
    setTimeout(poll, 2000); // Start polling after 2 seconds
}

function updateProgress(percentage, message, details = '') {
    const progressBar = document.getElementById('progressBar');
    const progressStatus = document.getElementById('progressStatus');
    const progressDetails = document.getElementById('progressDetails');
    
    progressBar.style.width = `${percentage}%`;
    progressBar.textContent = `${percentage}%`;
    progressStatus.textContent = message;
    progressDetails.textContent = details;
}

function displayResults(results) {
    // Hide progress, show results
    hideProgressSection();
    showResultsSection();
    showLoadingState(false);
    
    // Create summary cards
    createSummaryCards(results.summary);
    
    // Create charts
    createCharts(results);
    
    // Populate data table
    populateDataTable(results.developers);
    
    // Scroll to results
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

function createSummaryCards(summary) {
    const container = document.getElementById('summaryCards');
    
    const cards = [
        {
            title: 'Total PRs',
            value: summary.total_prs || 0,
            icon: 'fas fa-code-branch',
            color: 'primary'
        },
        {
            title: 'Merged PRs',
            value: summary.merged_prs || 0,
            icon: 'fas fa-check-circle',
            color: 'success'
        },
        {
            title: 'Developers',
            value: summary.total_developers || 0,
            icon: 'fas fa-users',
            color: 'info'
        },
        {
            title: 'Avg Time to Merge',
            value: summary.avg_time_to_merge || 'N/A',
            icon: 'fas fa-clock',
            color: 'warning'
        }
    ];
    
    container.innerHTML = cards.map(card => `
        <div class="col-lg-3 col-md-6 mb-4">
            <div class="card metric-card text-center p-4">
                <div class="card-body">
                    <i class="${card.icon} fa-3x mb-3"></i>
                    <h3 class="card-title">${card.value}</h3>
                    <p class="card-text">${card.title}</p>
                </div>
            </div>
        </div>
    `).join('');
}

function createCharts(results) {
    createContributorsChart(results.developers);
    createStatusChart(results.summary);
}

function createContributorsChart(developers) {
    const ctx = document.getElementById('contributorsChart').getContext('2d');
    
    // Get top 10 contributors
    const topDevelopers = developers
        .sort((a, b) => b.total_prs - a.total_prs)
        .slice(0, 10);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topDevelopers.map(dev => dev.developer),
            datasets: [{
                label: 'Total PRs',
                data: topDevelopers.map(dev => dev.total_prs),
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                    '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
                    '#4BC0C0', '#FF6384'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function createStatusChart(summary) {
    const ctx = document.getElementById('statusChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Merged', 'Open', 'Closed'],
            datasets: [{
                data: [
                    summary.merged_prs || 0,
                    summary.open_prs || 0,
                    summary.closed_prs || 0
                ],
                backgroundColor: ['#28a745', '#ffc107', '#dc3545']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function populateDataTable(developers) {
    const tbody = document.getElementById('resultsTableBody');
    
    tbody.innerHTML = developers.map(dev => `
        <tr>
            <td><strong>${dev.developer}</strong></td>
            <td>${dev.total_prs}</td>
            <td><span class="badge bg-success">${dev.merged_prs}</span></td>
            <td><span class="badge bg-warning">${dev.open_prs}</span></td>
            <td><span class="badge bg-danger">${dev.closed_prs}</span></td>
            <td>${dev.merge_rate_percent.toFixed(1)}%</td>
            <td>${dev.avg_time_to_merge_hours ? dev.avg_time_to_merge_hours.toFixed(1) + 'h' : 'N/A'}</td>
        </tr>
    `).join('');
}

async function exportCSV() {
    if (!currentTaskId) {
        showAlert('No data available to export', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/analysis/${currentTaskId}/export`);
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'github-pr-metrics.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showAlert('CSV file downloaded successfully!', 'success');
        
    } catch (error) {
        showAlert(`Export failed: ${error.message}`, 'danger');
    }
}

function showLoadingState(loading) {
    const btn = document.getElementById('analyzeBtn');
    const spinner = btn.querySelector('.loading-spinner');
    const icon = btn.querySelector('.fas');
    
    if (loading) {
        btn.disabled = true;
        spinner.style.display = 'inline-block';
        icon.style.display = 'none';
        btn.innerHTML = btn.innerHTML.replace('Start Analysis', 'Analyzing...');
    } else {
        btn.disabled = false;
        spinner.style.display = 'none';
        icon.style.display = 'inline';
        btn.innerHTML = btn.innerHTML.replace('Analyzing...', 'Start Analysis');
    }
}

function showProgressSection() {
    document.querySelector('.progress-container').style.display = 'block';
    document.getElementById('progress-section').scrollIntoView({ behavior: 'smooth' });
}

function hideProgressSection() {
    document.querySelector('.progress-container').style.display = 'none';
}

function showResultsSection() {
    document.querySelector('.results-container').style.display = 'block';
}

function hideResultsSection() {
    document.querySelector('.results-container').style.display = 'none';
}

function startNewAnalysis() {
    // Reset form and UI
    document.getElementById('analysisForm').reset();
    hideProgressSection();
    hideResultsSection();
    currentTaskId = null;
    
    // Close WebSocket
    if (wsConnection) {
        wsConnection.close();
        wsConnection = null;
    }
    
    // Scroll to form
    document.getElementById('form-section').scrollIntoView({ behavior: 'smooth' });
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(alert);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alert && alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}