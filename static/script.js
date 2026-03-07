// Stock Analyzer Application
const StockAnalyzer = {
    selectedStocks: [],
    allStocks: [],
    chart: null,
    maxStocks: 10,

    // Initialize the application
    async init() {
        this.bindEvents();
        await this.loadAllStocks();
        this.setupEventListeners();
        this.initDateInputs();
    },

    // Bind all event listeners
    bindEvents() {
        // Search input with debounce
        document.getElementById('stock-search').addEventListener('input', 
            this.debounce(this.searchStocks.bind(this), 300));

        // Main buttons
        document.getElementById('analyze-btn').addEventListener('click', this.analyze.bind(this));
        document.getElementById('equal-weights').addEventListener('click', this.setEqualWeights.bind(this));
        document.getElementById('clear-all').addEventListener('click', this.clearAll.bind(this));

        // Close search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-box')) {
                document.getElementById('search-results').style.display = 'none';
            }
        });

        // Handle window resize for chart
        window.addEventListener('resize', this.debounce(() => {
            if (this.chart) {
                this.chart.resize();
            }
        }, 250));
    },

    // Setup additional event listeners
    setupEventListeners() {
        // Weight inputs validation
        document.addEventListener('input', (e) => {
            if (e.target.id && e.target.id.startsWith('weight-')) {
                this.validateWeights();
            }
        });
    },

    // Initialize date inputs with default values
    initDateInputs() {
        const today = new Date();
        const defaultEnd = new Date('2026-01-01');
        const defaultStart = new Date('2010-01-01');
        
        document.getElementById('start-date').value = defaultStart.toISOString().split('T')[0];
        document.getElementById('end-date').value = defaultEnd.toISOString().split('T')[0];
        
        // Set max date to today
        document.getElementById('end-date').max = today.toISOString().split('T')[0];
    },

    // Get current date range values
    getDateRange() {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        // Validate dates
        if (!startDate || !endDate) {
            this.showNotification('Please select both start and end dates', 'warning');
            return null;
        }
        
        if (new Date(startDate) >= new Date(endDate)) {
            this.showNotification('Start date must be before end date', 'error');
            return null;
        }
        
        return { startDate, endDate };
    },

    // Set date preset
    setDatePreset(preset) {
        const endDate = new Date();
        const endDateStr = endDate.toISOString().split('T')[0];
        
        let startDate = new Date();
        
        switch(preset) {
            case '5y':
                startDate.setFullYear(endDate.getFullYear() - 5);
                break;
            case '10y':
                startDate.setFullYear(endDate.getFullYear() - 10);
                break;
            case '15y':
                startDate.setFullYear(endDate.getFullYear() - 15);
                break;
            case 'max':
                startDate = new Date('2010-01-01');
                break;
        }
        
        const startDateStr = startDate.toISOString().split('T')[0];
        
        document.getElementById('start-date').value = startDateStr;
        document.getElementById('end-date').value = endDateStr;
        
        this.showNotification(`Period set to ${preset}`, 'success');
    },

    // Load all stocks from the backend
    async loadAllStocks() {
        try {
            const response = await fetch('/api/stocks');
            this.allStocks = await response.json();
            this.populateStockBrowser();
        } catch (error) {
            console.error('Error loading stocks:', error);
            document.getElementById('stock-browser').innerHTML = 
                '<p class="error">Failed to load stocks. Please refresh the page.</p>';
        }
    },

    // Populate stock browser by sector
    populateStockBrowser() {
        const browserDiv = document.getElementById('stock-browser');
        if (!browserDiv) return;

        // Group stocks by sector
        const stocksBySector = {};
        this.allStocks.forEach(stock => {
            if (!stocksBySector[stock.sector]) {
                stocksBySector[stock.sector] = [];
            }
            stocksBySector[stock.sector].push(stock);
        });

        let html = '<div class="sector-tabs">';
        
        // Sort sectors alphabetically
        Object.keys(stocksBySector).sort().forEach(sector => {
            const sectorId = this.sanitizeId(sector);
            html += `
                <div class="sector-section">
                    <h4 class="sector-title" onclick="StockAnalyzer.toggleSector('${sectorId}')">
                        ${sector} <span class="sector-count">(${stocksBySector[sector].length})</span>
                        <span class="toggle-icon">▼</span>
                    </h4>
                    <div class="sector-stocks" id="sector-${sectorId}">
            `;
            
            // Sort stocks by symbol
            stocksBySector[sector].sort((a, b) => a.symbol.localeCompare(b.symbol)).forEach(stock => {
                html += `
                    <div class="stock-item" onclick="StockAnalyzer.addStock('${stock.symbol}', '${this.escapeString(stock.name)}')">
                        <span class="stock-symbol">${stock.symbol}</span>
                        <span class="stock-name">${this.truncate(stock.name, 35)}</span>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        browserDiv.innerHTML = html;

        // Open first sector by default
        const firstSector = document.querySelector('.sector-stocks');
        if (firstSector) {
            firstSector.style.display = 'grid';
        }
    },

    // Toggle sector visibility
    toggleSector(sectorId) {
        const sectorDiv = document.getElementById(`sector-${sectorId}`);
        const title = event.currentTarget;
        const icon = title.querySelector('.toggle-icon');
        
        if (sectorDiv.style.display === 'none' || !sectorDiv.style.display) {
            sectorDiv.style.display = 'grid';
            icon.textContent = '▼';
        } else {
            sectorDiv.style.display = 'none';
            icon.textContent = '▶';
        }
    },

    // Search stocks
    async searchStocks(event) {
        const query = event.target.value.trim();
        const resultsDiv = document.getElementById('search-results');
        
        if (query.length < 2) {
            resultsDiv.style.display = 'none';
            return;
        }
        
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const stocks = await response.json();
            this.displaySearchResults(stocks);
        } catch (error) {
            console.error('Search error:', error);
        }
    },

    // Display search results
    displaySearchResults(stocks) {
        const resultsDiv = document.getElementById('search-results');
        
        if (stocks.length === 0) {
            resultsDiv.innerHTML = '<div class="search-result-item no-results">No stocks found</div>';
            resultsDiv.style.display = 'block';
            return;
        }
        
        let html = '';
        stocks.forEach(stock => {
            html += `
                <div class="search-result-item" onclick="StockAnalyzer.addStock('${stock.symbol}', '${this.escapeString(stock.name)}')">
                    <div class="result-main">
                        <strong>${stock.symbol}</strong>
                        <span class="stock-name">${this.truncate(stock.name, 40)}</span>
                    </div>
                    <span class="stock-sector">${stock.sector}</span>
                </div>
            `;
        });
        
        resultsDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
    },

    // Add stock to selection
    addStock(symbol, name) {
        if (this.selectedStocks.length >= this.maxStocks) {
            this.showNotification(`You can select up to ${this.maxStocks} stocks`, 'warning');
            return;
        }
        
        if (this.selectedStocks.find(s => s.symbol === symbol)) {
            this.showNotification('Stock already selected', 'info');
            return;
        }
        
        this.selectedStocks.push({ symbol, name });
        this.updateSelectedStocksDisplay();
        this.updateWeightInputs();
        this.updateStockCount();
        
        // Clear search
        document.getElementById('stock-search').value = '';
        document.getElementById('search-results').style.display = 'none';
        
        this.showNotification(`${symbol} added to selection`, 'success');
    },

    // Remove stock from selection
    removeStock(symbol) {
        this.selectedStocks = this.selectedStocks.filter(s => s.symbol !== symbol);
        this.updateSelectedStocksDisplay();
        this.updateWeightInputs();
        this.updateStockCount();
        
        // Hide results if no stocks selected
        if (this.selectedStocks.length === 0) {
            document.getElementById('results-section').style.display = 'none';
        }
    },

    // Update selected stocks display
    updateSelectedStocksDisplay() {
        const listDiv = document.getElementById('stock-list');
        
        if (this.selectedStocks.length === 0) {
            listDiv.innerHTML = '<p class="no-stocks">No stocks selected. Search above or browse by sector.</p>';
            return;
        }
        
        let html = '';
        this.selectedStocks.forEach(stock => {
            html += `
                <div class="stock-tag">
                    <div class="stock-tag-info">
                        <span class="stock-symbol">${stock.symbol}</span>
                        <span class="stock-name">${this.truncate(stock.name, 25)}</span>
                    </div>
                    <button onclick="StockAnalyzer.removeStock('${stock.symbol}')" class="remove-btn" title="Remove">×</button>
                </div>
            `;
        });
        
        listDiv.innerHTML = html;
    },

    // Update stock count display
    updateStockCount() {
        const countSpan = document.getElementById('stock-count');
        if (countSpan) {
            countSpan.textContent = `(${this.selectedStocks.length}/${this.maxStocks})`;
        }
    },

    // Update weight inputs
    updateWeightInputs() {
        const weightDiv = document.getElementById('weight-inputs');
        const weightSection = document.querySelector('.weight-section');
        
        if (this.selectedStocks.length < 2) {
            weightSection.style.display = 'none';
            return;
        }
        
        weightSection.style.display = 'block';
        
        let html = '';
        this.selectedStocks.forEach((stock, index) => {
            const defaultWeight = (100 / this.selectedStocks.length).toFixed(1);
            html += `
                <div class="weight-input-group">
                    <label for="weight-${index}" title="${stock.name}">
                        <span class="weight-symbol">${stock.symbol}</span>
                    </label>
                    <div class="weight-control">
                        <input type="range" 
                               id="slider-${index}" 
                               value="${defaultWeight}" 
                               min="0" 
                               max="100" 
                               step="5"
                               oninput="StockAnalyzer.updateWeightFromSlider(${index}, this.value)">
                        <input type="number" 
                               id="weight-${index}" 
                               value="${defaultWeight}" 
                               min="0" 
                               max="100" 
                               step="5"
                               onchange="StockAnalyzer.updateWeightFromInput(${index}, this.value)">
                        <span class="weight-unit">%</span>
                    </div>
                </div>
            `;
        });
        
        weightDiv.innerHTML = html;
    },

    // Update weight from slider
    updateWeightFromSlider(index, value) {
        const weightInput = document.getElementById(`weight-${index}`);
        if (weightInput) {
            weightInput.value = value;
        }
        this.validateWeights();
    },

    // Update weight from input
    updateWeightFromInput(index, value) {
        const slider = document.getElementById(`slider-${index}`);
        if (slider) {
            slider.value = value;
        }
        this.validateWeights();
    },

    // Set equal weights
    setEqualWeights() {
        if (this.selectedStocks.length < 2) return;
        
        const equalWeight = (100 / this.selectedStocks.length).toFixed(1);
        this.selectedStocks.forEach((_, index) => {
            const weightInput = document.getElementById(`weight-${index}`);
            const slider = document.getElementById(`slider-${index}`);
            if (weightInput) weightInput.value = equalWeight;
            if (slider) slider.value = equalWeight;
        });
        
        this.validateWeights();
    },

    // Validate weights total to 100%
    validateWeights() {
        let total = 0;
        this.selectedStocks.forEach((_, index) => {
            const input = document.getElementById(`weight-${index}`);
            if (input) total += parseFloat(input.value) || 0;
        });
        
        const warning = document.getElementById('weight-warning');
        const analyzeBtn = document.getElementById('analyze-btn');
        
        if (Math.abs(total - 100) > 0.1) {
            if (!warning) {
                const warningDiv = document.createElement('div');
                warningDiv.id = 'weight-warning';
                warningDiv.className = 'warning-message';
                warningDiv.textContent = `⚠️ Total weight is ${total.toFixed(1)}%. Should be 100%`;
                document.querySelector('.weight-section').appendChild(warningDiv);
            }
            analyzeBtn.disabled = true;
            analyzeBtn.title = 'Weights must sum to 100%';
        } else {
            if (warning) warning.remove();
            analyzeBtn.disabled = false;
            analyzeBtn.title = '';
        }
    },

    // Clear all selections
    clearAll() {
        this.selectedStocks = [];
        this.updateSelectedStocksDisplay();
        this.updateWeightInputs();
        this.updateStockCount();
        document.getElementById('results-section').style.display = 'none';
        
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    },

    // Debug response
    debugResponse(data) {
        console.log('Full response data:', data);
        console.log('Is portfolio:', data.is_portfolio);
        console.log('Has portfolio_calculation_steps:', data.portfolio_calculation_steps ? 'YES' : 'NO');
        if (data.portfolio_calculation_steps) {
            console.log('Number of steps:', data.portfolio_calculation_steps.length);
            console.log('Steps content:', data.portfolio_calculation_steps);
        }
    },

    // Analyze selected stocks
    async analyze() {
        if (this.selectedStocks.length < 1) {
            this.showNotification('Please select at least 1 stock to analyze', 'warning');
            return;
        }

        // Get date range
        const dateRange = this.getDateRange();
        if (!dateRange) return;

        let weights = null;
        
        // Only get weights if we have multiple stocks
        if (this.selectedStocks.length > 1) {
            weights = [];
            let totalWeight = 0;
            for (let i = 0; i < this.selectedStocks.length; i++) {
                const weightInput = document.getElementById(`weight-${i}`);
                const weight = weightInput ? parseFloat(weightInput.value) / 100 : 1/this.selectedStocks.length;
                weights.push(weight);
                totalWeight += weight;
            }

            if (Math.abs(totalWeight - 1) > 0.01) {
                this.showNotification('Portfolio weights must sum to 100%', 'error');
                return;
            }
        }

        // Show loading
        this.toggleLoading(true);

        try {
            const response = await fetch('/api/analyze-multiple', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    stocks: this.selectedStocks.map(s => s.symbol),
                    weights: weights,
                    start_date: dateRange.startDate,
                    end_date: dateRange.endDate
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.debugResponse(data);
                this.displayAnalysisResults(data);
                this.showNotification('Analysis complete!', 'success');
            } else {
                let errorMessage = data.error || 'Unknown error';
                if (data.errors && data.errors.length > 0) {
                    errorMessage = 'Some stocks could not be analyzed:\n' + data.errors.join('\n');
                }
                this.showNotification(errorMessage, 'error');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            this.showNotification('Error connecting to server. Please make sure the backend is running.', 'error');
        } finally {
            this.toggleLoading(false);
        }
    },

    // Display analysis results (handles both single and multiple stocks)
    displayAnalysisResults(data) {
        document.getElementById('results-section').style.display = 'block';
        document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
        
        const stocks = data.stocks;
        
        // Display summary based on number of stocks
        this.displayAnalysisSummary(data);
        
        // Display stock cards
        this.displayStockCards(stocks);
        
        // Display metrics table
        this.displayMetricsTable(stocks);
        
        // Create chart
        this.createReturnsChart(stocks);
    },

    // Display analysis summary
    displayAnalysisSummary(data) {
        const summaryDiv = document.getElementById('portfolio-summary');
        const stocks = data.stocks;
        const isPortfolio = stocks.length > 1;
        const period = data.analysis_period || { start: '2010-01-01', end: '2026-01-01' };
        
        // Format dates for display
        const startYear = period.start.split('-')[0];
        const endYear = period.end.split('-')[0];
        
        // Determine return value and class
        let returnValue, returnClass;
        if (isPortfolio) {
            returnValue = data.portfolio_return;
            returnClass = returnValue >= 0 ? 'positive' : 'negative';
        } else {
            returnValue = stocks[0].expected_return;
            returnClass = returnValue >= 0 ? 'positive' : 'negative';
        }
        
        // Build summary HTML
        let summaryHtml = `
            <div class="summary-card">
                <h3>${isPortfolio ? '📊 Portfolio Summary' : '📈 Stock Analysis'}</h3>
                <div class="summary-metrics">
                    <div class="metric">
                        <span class="metric-label">${isPortfolio ? 'Expected Portfolio Return' : 'Expected Return'}:</span>
                        <span class="metric-value ${returnClass}">${returnValue}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Number of Stocks:</span>
                        <span class="metric-value">${stocks.length}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Analysis Period:</span>
                        <span class="metric-value">${startYear} - ${endYear}</span>
                    </div>
                </div>
        `;
        
        // Add weight information for portfolios
        if (isPortfolio && data.weights) {
            summaryHtml += `
                <div class="weight-breakdown" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.2);">
                    <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem; opacity: 0.9;">Portfolio Weights</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 1rem;">
            `;
            
            stocks.forEach((stock, index) => {
                summaryHtml += `
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 0.85rem;">${stock.symbol}:</span>
                        <span style="font-weight: 600;">${data.weights[index]}%</span>
                    </div>
                `;
            });
            
            summaryHtml += `</div>`;
            
            // Add button to show portfolio calculation steps
            summaryHtml += `
                <button class="show-portfolio-steps-btn" onclick="StockAnalyzer.togglePortfolioSteps()">
                    Show Portfolio Return Calculation Steps
                </button>
            `;
            
            summaryHtml += `</div>`;
        }
        
        summaryHtml += `</div>`;
        
        // Add portfolio steps container
        summaryHtml += `
            <div id="portfolio-steps-container" class="steps-container" style="display: none; margin-top: 1rem;">
        `;
        
        // Only add content if we have steps
        if (isPortfolio && data.portfolio_calculation_steps) {
            summaryHtml += this.showPortfolioCalculationSteps(data);
        } else {
            summaryHtml += '<p class="note">No calculation steps available</p>';
        }
        
        summaryHtml += `</div>`;
        
        summaryDiv.innerHTML = summaryHtml;
    },

    // Display portfolio calculation steps
    showPortfolioCalculationSteps(data) {
        console.log('Showing portfolio steps:', data.portfolio_calculation_steps);
        
        if (!data.is_portfolio || !data.portfolio_calculation_steps || data.portfolio_calculation_steps.length === 0) {
            return '<p class="note">Portfolio calculation steps not available</p>';
        }
        
        const steps = data.portfolio_calculation_steps;
        
        let stepsHtml = `
            <div class="portfolio-calculation-steps">
                <h4>📊 Portfolio Expected Return Calculation</h4>
        `;
        
        steps.forEach(step => {
            stepsHtml += `<div class="portfolio-step">`;
            stepsHtml += `<div class="step-header">Step ${step.step}: ${step.description}</div>`;
            
            if (step.formula) {
                stepsHtml += `<div class="formula">${step.formula}</div>`;
            }
            
            if (step.details && step.details.length > 0) {
                stepsHtml += `<div class="step-details">`;
                step.details.forEach(detail => {
                    stepsHtml += `<div class="detail-item">${detail}</div>`;
                });
                stepsHtml += `</div>`;
            }
            
            if (step.calculation) {
                stepsHtml += `<div class="step-calculation">${step.calculation}</div>`;
            }
            
            if (step.result) {
                stepsHtml += `<div class="step-result"><strong>${step.result}</strong></div>`;
            }
            
            stepsHtml += `</div>`;
        });
        
        stepsHtml += `</div>`;
        
        return stepsHtml;
    },

    // Toggle portfolio calculation steps visibility
    togglePortfolioSteps() {
        const stepsDiv = document.getElementById('portfolio-steps-container');
        if (stepsDiv.style.display === 'none') {
            stepsDiv.style.display = 'block';
            stepsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            stepsDiv.style.display = 'none';
        }
    },

    // Display stock cards
    displayStockCards(stocks) {
        const cardsDiv = document.getElementById('stock-cards');
        let html = '';
        
        stocks.forEach(stock => {
            const returnClass = stock.expected_return >= 0 ? 'positive' : 'negative';
            
            html += `
                <div class="stock-card">
                    <div class="stock-header">
                        <h4 title="${stock.name}">${this.truncate(stock.name, 35)}</h4>
                        <span class="stock-symbol">${stock.symbol}</span>
                    </div>
                    <div class="stock-metrics">
                        <div class="metric">
                            <span class="metric-label">Expected Return:</span>
                            <span class="metric-value ${returnClass}">${stock.expected_return}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Risk (Std Dev):</span>
                            <span class="metric-value">${stock.std_deviation}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Variance:</span>
                            <span class="metric-value">${stock.variance}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Data Points:</span>
                            <span class="metric-value">${stock.data_points} years</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Current Price:</span>
                            <span class="metric-value">RM ${stock.current_price?.toFixed(2) || 'N/A'}</span>
                        </div>
                    </div>
                    <button class="show-steps-btn" onclick="StockAnalyzer.toggleSteps('${stock.symbol}')">
                        Show Calculation Steps
                    </button>
                    <div id="steps-${stock.symbol}" class="steps-container" style="display: none;">
                        ${this.showCalculationSteps(stock)}
                    </div>
                </div>
            `;
        });
        
        cardsDiv.innerHTML = html;
    },

    // Display calculation steps for a stock
    showCalculationSteps(stock) {
        const steps = stock.calculation_steps;
        
        let stepsHtml = `
            <div class="calculation-steps">
                <h4>📊 Calculation Steps for ${stock.symbol}</h4>
                
                <div class="step-section">
                    <h5>1. Annual Returns Calculation</h5>
                    <p class="formula">${steps.annual_returns[0].formula}</p>
                    <div class="step-details">
        `;
        
        // Show first few annual return calculations as examples
        steps.annual_returns.slice(0, 3).forEach(calc => {
            stepsHtml += `
                <div class="calculation-example">
                    <div class="year-badge">${calc.year}</div>
                    <div class="calc-detail">
                        <div>${calc.values}</div>
                        <div class="calc-result">${calc.result}</div>
                    </div>
                </div>
            `;
        });
        
        if (steps.annual_returns.length > 3) {
            stepsHtml += `<p class="note">... and ${steps.annual_returns.length - 3} more years</p>`;
        }
        
        stepsHtml += `
                    </div>
                </div>
                
                <div class="step-section">
                    <h5>2. Expected Return Calculation</h5>
                    <p class="formula">${steps.expected_return.formula}</p>
                    <div class="step-details">
        `;
        
        steps.expected_return.components.forEach(comp => {
            if (comp.description) {
                stepsHtml += `<p class="step-description">${comp.description}</p>`;
            }
            if (comp.values) {
                stepsHtml += `<p class="step-values">${comp.values}</p>`;
            }
            if (comp.calculation) {
                stepsHtml += `<p class="step-calculation">${comp.calculation}</p>`;
            }
            if (comp.sum) {
                stepsHtml += `<p class="step-sum">${comp.sum}</p>`;
            }
            if (comp.result) {
                stepsHtml += `<p class="step-result"><strong>${comp.result}</strong></p>`;
            }
        });
        
        stepsHtml += `
                    </div>
                </div>
                
                <div class="step-section">
                    <h5>3. Variance Calculation</h5>
                    <p class="formula">${steps.variance.formula}</p>
                    <div class="step-details">
        `;
        
        steps.variance.components.forEach(comp => {
            if (comp.description) {
                stepsHtml += `<p class="step-description">${comp.description}</p>`;
            }
            if (comp.values) {
                stepsHtml += `<div class="step-values-list">`;
                comp.values.slice(0, 3).forEach(val => {
                    stepsHtml += `<p>${val}</p>`;
                });
                if (comp.values.length > 3) {
                    stepsHtml += `<p class="note">... and ${comp.values.length - 3} more</p>`;
                }
                stepsHtml += `</div>`;
            }
            if (comp.calculation) {
                stepsHtml += `<p class="step-calculation">${comp.calculation}</p>`;
            }
            if (comp.result) {
                stepsHtml += `<p class="step-result"><strong>${comp.result}</strong></p>`;
            }
        });
        
        stepsHtml += `
                    </div>
                </div>
                
                <div class="step-section">
                    <h5>4. Standard Deviation Calculation</h5>
                    <p class="formula">${steps.std_deviation.formula}</p>
                    <div class="step-details">
                        <p class="step-calculation">${steps.std_deviation.calculation}</p>
                        <p class="step-result"><strong>${steps.std_deviation.result}</strong></p>
                    </div>
                </div>
            </div>
        `;
        
        return stepsHtml;
    },

    // Toggle calculation steps visibility
    toggleSteps(symbol) {
        const stepsDiv = document.getElementById(`steps-${symbol}`);
        if (stepsDiv.style.display === 'none') {
            stepsDiv.style.display = 'block';
        } else {
            stepsDiv.style.display = 'none';
        }
    },

    // Display metrics table
    displayMetricsTable(stocks) {
        const tbody = document.getElementById('metrics-body');
        let html = '';
        
        stocks.forEach(stock => {
            const returnClass = stock.expected_return >= 0 ? 'positive' : 'negative';
            
            html += `
                <tr>
                    <td>
                        <strong>${this.truncate(stock.name, 35)}</strong>
                        <br><small class="stock-symbol">${stock.symbol}</small>
                    </td>
                    <td class="${returnClass}"><strong>${stock.expected_return}%</strong></td>
                    <td>${stock.std_deviation}%</td>
                    <td>${stock.variance}</td>
                    <td>${stock.data_points} years</td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
    },

    // Create returns comparison chart
    createReturnsChart(stocks) {
        const ctx = document.getElementById('returns-chart').getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }
        
        const datasets = [];
        const colors = [
            '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
            '#ec4899', '#14b8a6', '#f97316', '#6b7280', '#6366f1'
        ];
        
        stocks.forEach((stock, index) => {
            datasets.push({
                label: `${stock.symbol} - ${this.truncate(stock.name, 20)}`,
                data: stock.annual_returns,
                borderColor: colors[index % colors.length],
                backgroundColor: 'transparent',
                tension: 0.1,
                pointRadius: 4,
                pointHoverRadius: 6,
                borderWidth: 2
            });
        });
        
        const chartTitle = stocks.length === 1 ? 
            `${stocks[0].symbol} Annual Returns Over Time` : 
            'Annual Returns Comparison';
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: stocks[0].years,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            boxWidth: 12,
                            padding: 15,
                            font: { size: 11 }
                        }
                    },
                    title: {
                        display: true,
                        text: chartTitle,
                        font: { size: 14, weight: '500' }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.raw !== null) {
                                    label += context.raw + '%';
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Annual Return (%)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Year'
                        }
                    }
                }
            }
        });
    },

    // Utility Functions
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    truncate(str, length) {
        if (!str) return '';
        return str.length > length ? str.substring(0, length) + '...' : str;
    },

    escapeString(str) {
        return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
    },

    sanitizeId(str) {
        return str.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase();
    },

    toggleLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        const analyzeBtn = document.getElementById('analyze-btn');
        
        if (show) {
            overlay.style.display = 'flex';
            analyzeBtn.disabled = true;
        } else {
            overlay.style.display = 'none';
            analyzeBtn.disabled = false;
        }
    },

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Add to body
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
};

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Make StockAnalyzer globally accessible
    window.StockAnalyzer = StockAnalyzer;
    StockAnalyzer.init();
});