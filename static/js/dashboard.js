// Dashboard JavaScript

let currentPage = 1;
let postsChart = null;
let keywordsChart = null;

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadPosts();
    loadKeywords();
});

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        // Update stat cards
        document.getElementById('totalPosts').textContent = data.total_posts;
        
        // Update platform-specific counts
        const platformStats = data.platform_stats.reduce((acc, stat) => {
            acc[stat.platform] = stat.count;
            return acc;
        }, {});
        
        document.getElementById('linkedinPosts').textContent = platformStats.linkedin || 0;
        document.getElementById('glassdoorPosts').textContent = platformStats.glassdoor || 0;
        document.getElementById('keywordsTracked').textContent = data.top_keywords.length;
        
        // Update charts
        updatePostsChart(data.posts_over_time);
        updateKeywordsChart(data.top_keywords);
        
    } catch (error) {
        console.error('Error loading stats:', error);
        showToast('Error loading statistics', 'danger');
    }
}

// Load posts
async function loadPosts(page = 1) {
    currentPage = page;
    
    const platform = document.getElementById('platformFilter').value;
    const keyword = document.getElementById('keywordFilter').value;
    const postType = document.getElementById('postTypeFilter').value;
    
    const params = new URLSearchParams({
        page: page,
        per_page: 20
    });
    
    if (platform) params.append('platform', platform);
    if (keyword) params.append('keyword', keyword);
    if (postType) params.append('post_type', postType);
    
    try {
        const response = await fetch(`/api/posts?${params}`);
        const data = await response.json();
        
        displayPosts(data.posts);
        updatePagination(data.page, data.total_pages);
        
    } catch (error) {
        console.error('Error loading posts:', error);
        showToast('Error loading posts', 'danger');
    }
}

// Display posts in table
function displayPosts(posts) {
    const tbody = document.getElementById('postsTable');
    
    if (posts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">No posts found</td></tr>';
        return;
    }
    
    tbody.innerHTML = posts.map(post => `
        <tr class="fade-in">
            <td>
                <span class="badge platform-badge platform-${post.platform}">
                    ${post.platform}
                </span>
            </td>
            <td>
                ${post.author || 'Unknown'}
                ${post.author_title ? `<br><small class="text-muted">${post.author_title}</small>` : ''}
            </td>
            <td>
                <div class="content-preview" title="${escapeHtml(post.content)}">
                    ${escapeHtml(post.content)}
                </div>
            </td>
            <td>
                ${post.keywords_found.map(kw => 
                    `<span class="keyword-badge keyword-${getKeywordCategory(kw)}">${kw}</span>`
                ).join('')}
            </td>
            <td>
                <small>${formatDate(post.timestamp || post.scraped_at)}</small>
            </td>
            <td>
                <a href="${post.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                    <i class="bi bi-box-arrow-up-right"></i>
                </a>
            </td>
        </tr>
    `).join('');
}

// Load keywords for filter
async function loadKeywords() {
    try {
        const response = await fetch('/api/keywords');
        const data = await response.json();
        
        const select = document.getElementById('keywordFilter');
        select.innerHTML = '<option value="">All Keywords</option>' +
            data.keywords.map(kw => 
                `<option value="${kw.keyword}">${kw.keyword} (${kw.total_mentions})</option>`
            ).join('');
            
    } catch (error) {
        console.error('Error loading keywords:', error);
    }
}

// Update posts chart
function updatePostsChart(data) {
    const ctx = document.getElementById('postsChart').getContext('2d');
    
    if (postsChart) {
        postsChart.destroy();
    }
    
    postsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => formatDate(d.date)),
            datasets: [{
                label: 'Posts',
                data: data.map(d => d.count),
                borderColor: '#4e73df',
                backgroundColor: 'rgba(78, 115, 223, 0.1)',
                tension: 0.3
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
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Update keywords chart
function updateKeywordsChart(keywords) {
    const ctx = document.getElementById('keywordsChart').getContext('2d');
    
    if (keywordsChart) {
        keywordsChart.destroy();
    }
    
    const topKeywords = keywords.slice(0, 5);
    
    keywordsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topKeywords.map(k => k.keyword),
            datasets: [{
                label: 'Mentions',
                data: topKeywords.map(k => k.mentions),
                backgroundColor: [
                    '#4e73df',
                    '#1cc88a',
                    '#36b9cc',
                    '#f6c23e',
                    '#e74a3b'
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
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Update pagination
function updatePagination(currentPage, totalPages) {
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadPosts(${currentPage - 1}); return false;">Previous</a>
    </li>`;
    
    // Page numbers
    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
        html += `<li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="#" onclick="loadPosts(${i}); return false;">${i}</a>
        </li>`;
    }
    
    // Next button
    html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadPosts(${currentPage + 1}); return false;">Next</a>
    </li>`;
    
    pagination.innerHTML = html;
}

// Trigger manual scrape
async function triggerScrape() {
    const platform = document.getElementById('platformFilter').value;
    
    showToast('Starting scraper...', 'info');
    
    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ platform })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Scraping completed! Found ${data.results.total_posts} new posts`, 'success');
            refreshData();
        } else {
            showToast('Scraping failed: ' + data.error, 'danger');
        }
        
    } catch (error) {
        console.error('Error triggering scrape:', error);
        showToast('Error triggering scrape', 'danger');
    }
}

// Refresh all data
function refreshData() {
    loadStats();
    loadPosts(currentPage);
}

// Export data
async function exportData() {
    try {
        const response = await fetch('/api/export?days=7');
        const data = await response.json();
        
        // Create blob and download
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `social-media-export-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast('Data exported successfully', 'success');
        
    } catch (error) {
        console.error('Error exporting data:', error);
        showToast('Error exporting data', 'danger');
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function getKeywordCategory(keyword) {
    // This should match the categories from the backend
    const categories = {
        'Marc Benioff': 'person',
        'Bret Taylor': 'person',
        'Agentforce': 'product',
        'Sierra.AI': 'product',
        'Sierra AI': 'product',
        'Salesforce': 'company'
    };
    
    return categories[keyword] || 'general';
}

function showToast(message, type = 'info') {
    const toastEl = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    toastMessage.textContent = message;
    toastEl.classList.remove('text-bg-success', 'text-bg-danger', 'text-bg-info');
    toastEl.classList.add(`text-bg-${type}`);
    
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// Auto-refresh every 5 minutes
setInterval(refreshData, 5 * 60 * 1000);