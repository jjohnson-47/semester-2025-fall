/**
 * Deploy button functionality for dashboard
 * Handles the deployment pipeline with progress tracking
 */

class DeploymentManager {
    constructor() {
        this.isDeploying = false;
        this.deployButton = null;
        this.statusElement = null;
        this.logContainer = null;
        this.init();
    }

    init() {
        // Wait for DOM to load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupUI());
        } else {
            this.setupUI();
        }
    }

    setupUI() {
        // Find or create deploy button
        this.deployButton = document.getElementById('deployButton');
        if (!this.deployButton) {
            // Add deploy button to existing dropdown
            const deployDropdown = document.querySelector('[data-bs-toggle="dropdown"]:has(.bi-cloud-upload)');
            if (deployDropdown) {
                // Add actual deploy action to dropdown
                const dropdownMenu = deployDropdown.nextElementSibling;
                if (dropdownMenu) {
                    const deployItem = document.createElement('li');
                    deployItem.innerHTML = `
                        <a class="dropdown-item" href="#" id="deployButton">
                            <i class="bi bi-rocket-takeoff"></i> Deploy to Production
                        </a>
                    `;
                    dropdownMenu.insertBefore(deployItem, dropdownMenu.firstChild);
                    
                    // Add divider after deploy button
                    const divider = document.createElement('li');
                    divider.innerHTML = '<hr class="dropdown-divider">';
                    dropdownMenu.insertBefore(divider, deployItem.nextSibling);
                    
                    this.deployButton = document.getElementById('deployButton');
                }
            }
        }

        // Create status display area
        this.createStatusDisplay();

        // Attach event listeners
        if (this.deployButton) {
            this.deployButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.startDeployment();
            });
        }

        // Check deployment status on load
        this.checkStatus();
    }

    createStatusDisplay() {
        // Check if status display already exists
        if (document.getElementById('deploymentStatus')) {
            this.statusElement = document.getElementById('deploymentStatus');
            this.logContainer = document.getElementById('deploymentLog');
            return;
        }

        // Create deployment status modal
        const modal = document.createElement('div');
        modal.innerHTML = `
            <div class="modal fade" id="deploymentModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-rocket-takeoff"></i> Deployment Status
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div id="deploymentStatus"></div>
                            <div id="deploymentProgress" class="my-3" style="display:none;">
                                <div class="progress">
                                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                         role="progressbar" style="width: 0%"></div>
                                </div>
                            </div>
                            <div id="deploymentSteps" class="list-group mb-3" style="display:none;">
                                <div class="list-group-item" data-step="build">
                                    <i class="bi bi-circle"></i> Building site with v2 templates
                                </div>
                                <div class="list-group-item" data-step="sync">
                                    <i class="bi bi-circle"></i> Syncing content to worker
                                </div>
                                <div class="list-group-item" data-step="deploy">
                                    <i class="bi bi-circle"></i> Deploying to Cloudflare
                                </div>
                                <div class="list-group-item" data-step="verify">
                                    <i class="bi bi-circle"></i> Verifying deployment
                                </div>
                            </div>
                            <div id="deploymentLog" class="border rounded p-2 bg-light" 
                                 style="max-height: 300px; overflow-y: auto; display:none;">
                                <small class="font-monospace"></small>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" id="viewProductionBtn" style="display:none;">
                                <i class="bi bi-box-arrow-up-right"></i> View Production
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        this.statusElement = document.getElementById('deploymentStatus');
        this.logContainer = document.getElementById('deploymentLog');
        this.modal = new bootstrap.Modal(document.getElementById('deploymentModal'));
    }

    async startDeployment() {
        if (this.isDeploying) {
            alert('Deployment already in progress');
            return;
        }

        // Show modal
        this.modal.show();
        this.isDeploying = true;

        // Reset UI
        this.statusElement.innerHTML = '<div class="alert alert-info"><i class="bi bi-hourglass-split"></i> Starting deployment...</div>';
        document.getElementById('deploymentProgress').style.display = 'block';
        document.getElementById('deploymentSteps').style.display = 'block';
        document.getElementById('deploymentLog').style.display = 'block';
        document.getElementById('viewProductionBtn').style.display = 'none';

        // Reset steps
        document.querySelectorAll('#deploymentSteps .list-group-item').forEach(item => {
            item.classList.remove('list-group-item-success', 'list-group-item-danger', 'active');
            item.querySelector('i').className = 'bi bi-circle';
        });

        try {
            const response = await fetch('/api/deploy/trigger', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Deployment failed: ${response.statusText}`);
            }

            // Start polling for status
            this.pollDeploymentStatus();

        } catch (error) {
            this.statusElement.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> Deployment failed: ${error.message}
                </div>
            `;
            this.isDeploying = false;
        }
    }

    async pollDeploymentStatus() {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/deploy/status');
                const data = await response.json();

                if (data.status === 'deploying') {
                    // Update progress
                    this.updateProgress(data);
                } else {
                    // Deployment complete
                    clearInterval(pollInterval);
                    this.handleDeploymentComplete(data.last_deployment || data);
                }
            } catch (error) {
                clearInterval(pollInterval);
                this.statusElement.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle"></i> Lost connection to deployment
                    </div>
                `;
                this.isDeploying = false;
            }
        }, 2000); // Poll every 2 seconds
    }

    updateProgress(data) {
        // Update log
        if (data.log && data.log.length > 0) {
            const logHtml = data.log.map(entry => {
                const levelClass = {
                    'error': 'text-danger',
                    'warning': 'text-warning',
                    'success': 'text-success',
                    'info': 'text-info'
                }[entry.level] || '';
                
                return `<div class="${levelClass}">[${entry.level.toUpperCase()}] ${entry.message}</div>`;
            }).join('');
            
            this.logContainer.querySelector('small').innerHTML = logHtml;
            this.logContainer.scrollTop = this.logContainer.scrollHeight;
        }
    }

    handleDeploymentComplete(deployment) {
        this.isDeploying = false;

        // Update progress bar
        const progressBar = document.querySelector('#deploymentProgress .progress-bar');
        progressBar.style.width = '100%';
        progressBar.classList.remove('progress-bar-animated');

        // Update steps based on results
        if (deployment.steps) {
            Object.entries(deployment.steps).forEach(([step, result]) => {
                const stepElement = document.querySelector(`[data-step="${step}"]`);
                if (stepElement) {
                    if (result.success) {
                        stepElement.classList.add('list-group-item-success');
                        stepElement.querySelector('i').className = 'bi bi-check-circle-fill text-success';
                    } else {
                        stepElement.classList.add('list-group-item-danger');
                        stepElement.querySelector('i').className = 'bi bi-x-circle-fill text-danger';
                    }
                }
            });
        }

        // Update status message
        if (deployment.status === 'success') {
            this.statusElement.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle-fill"></i> Deployment completed successfully!
                    <br><small>Duration: ${Math.round(deployment.total_duration)}s</small>
                </div>
            `;
            
            // Show production button
            document.getElementById('viewProductionBtn').style.display = 'inline-block';
            document.getElementById('viewProductionBtn').onclick = () => {
                window.open(deployment.production_url || 'https://courses.jeffsthings.com', '_blank');
            };
        } else if (deployment.status === 'warning') {
            this.statusElement.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i> Deployment completed with warnings
                </div>
            `;
        } else {
            this.statusElement.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-x-circle"></i> Deployment failed: ${deployment.error || 'Unknown error'}
                </div>
            `;
        }

        // Update final log
        if (deployment.log) {
            this.updateProgress({ log: deployment.log });
        }
    }

    async checkStatus() {
        try {
            const response = await fetch('/api/deploy/status');
            const data = await response.json();

            if (data.status === 'deploying') {
                // Show modal and start polling
                this.modal.show();
                this.isDeploying = true;
                this.pollDeploymentStatus();
            }
        } catch (error) {
            console.error('Failed to check deployment status:', error);
        }
    }
}

// Initialize deployment manager when script loads
const deploymentManager = new DeploymentManager();