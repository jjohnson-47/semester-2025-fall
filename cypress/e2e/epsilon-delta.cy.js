// Cypress E2E tests for epsilon-delta tool
// Tests KaTeX rendering, mode switching, slider interactions, and graph updates

describe('Epsilon-Delta Tool', () => {
  beforeEach(() => {
    cy.visit('http://localhost:8002/math251/epsilon-delta.html');
  });

  describe('Initial Load', () => {
    it('should display the correct title', () => {
      cy.get('h1').should('contain', 'A δ for your ε');
    });

    it('should render math expressions with KaTeX', () => {
      // Check that function display contains rendered math (not raw LaTeX)
      cy.get('#functionDisplay').should('be.visible');
      cy.get('#functionDisplay').should('not.contain', '\\(');
      cy.get('#functionDisplay').should('contain', 'f(x)');
      
      // Check for KaTeX elements
      cy.get('#functionDisplay .katex').should('exist');
    });

    it('should display canvas graph', () => {
      cy.get('#graphCanvas').should('be.visible');
      cy.get('#graphCanvas').should('have.attr', 'width');
      cy.get('#graphCanvas').should('have.attr', 'height');
    });

    it('should show Learn mode as active by default', () => {
      cy.get('.mode-btn[data-mode="learn"]').should('have.class', 'active');
      cy.get('#learnContent').should('be.visible');
      cy.get('#practiceContent').should('not.be.visible');
      cy.get('#challengeContent').should('not.be.visible');
    });
  });

  describe('Mode Switching', () => {
    it('should switch between modes when clicking buttons', () => {
      // Switch to Practice mode
      cy.get('.mode-btn[data-mode="practice"]').click();
      cy.get('.mode-btn[data-mode="practice"]').should('have.class', 'active');
      cy.get('.mode-btn[data-mode="learn"]').should('not.have.class', 'active');
      cy.get('#practiceContent').should('be.visible');
      cy.get('#learnContent').should('not.be.visible');

      // Switch to Challenge mode
      cy.get('.mode-btn[data-mode="challenge"]').click();
      cy.get('.mode-btn[data-mode="challenge"]').should('have.class', 'active');
      cy.get('#challengeContent').should('be.visible');
      cy.get('#practiceContent').should('not.be.visible');
    });

    it('should support keyboard navigation for mode tabs', () => {
      // Focus first tab
      cy.get('.mode-btn[data-mode="learn"]').focus();
      
      // Press right arrow to go to Practice
      cy.get('.mode-btn[data-mode="learn"]').type('{rightarrow}');
      cy.get('.mode-btn[data-mode="practice"]').should('have.focus');
      cy.get('.mode-btn[data-mode="practice"]').should('have.class', 'active');
      
      // Press right arrow again to go to Challenge
      cy.get('.mode-btn[data-mode="practice"]').type('{rightarrow}');
      cy.get('.mode-btn[data-mode="challenge"]').should('have.focus');
      cy.get('.mode-btn[data-mode="challenge"]').should('have.class', 'active');
      
      // Press left arrow to go back
      cy.get('.mode-btn[data-mode="challenge"]').type('{leftarrow}');
      cy.get('.mode-btn[data-mode="practice"]').should('have.focus');
    });
  });

  describe('Slider Interactions', () => {
    it('should update epsilon value when slider changes', () => {
      // Get initial value
      cy.get('#epsilonValue').invoke('text').then((initialValue) => {
        // Change slider
        cy.get('#epsilonSlider').invoke('val', 1.0).trigger('input');
        
        // Check value updated
        cy.get('#epsilonValue').should('contain', '1.00');
        cy.get('#epsilonValue').should('not.contain', initialValue);
      });
    });

    it('should update delta value when slider changes', () => {
      // Get initial value
      cy.get('#deltaValue').invoke('text').then((initialValue) => {
        // Change slider
        cy.get('#deltaSlider').invoke('val', 0.5).trigger('input');
        
        // Check value updated
        cy.get('#deltaValue').should('contain', '0.50');
        cy.get('#deltaValue').should('not.contain', initialValue);
      });
    });

    it('should trigger graph redraw when sliders change', () => {
      // Spy on canvas context to detect drawing
      cy.window().then((win) => {
        const canvas = win.document.getElementById('graphCanvas');
        const ctx = canvas.getContext('2d');
        cy.spy(ctx, 'clearRect');
        
        // Change epsilon slider
        cy.get('#epsilonSlider').invoke('val', 0.8).trigger('input');
        
        // Wait a bit for requestAnimationFrame
        cy.wait(100);
        
        // Check that canvas was cleared (part of redraw)
        cy.wrap(ctx.clearRect).should('have.been.called');
      });
    });
  });

  describe('Feedback System', () => {
    it('should show thinking emoji by default', () => {
      cy.get('#feedbackEmoji').should('contain', '🤔');
    });

    it('should update feedback when delta changes', () => {
      // Set delta to a larger value
      cy.get('#deltaSlider').invoke('val', 0.8).trigger('input');
      cy.wait(100);
      
      // Should show error state
      cy.get('#feedbackCircle').should('have.class', 'error');
      cy.get('#feedbackEmoji').should('contain', '❌');
    });

    it('should show success when answer is correct', () => {
      // This would need knowledge of the correct delta for current epsilon
      // For the default linear function, delta should be <= epsilon/2
      cy.get('#epsilonSlider').invoke('val', 1.0).trigger('input');
      cy.get('#deltaSlider').invoke('val', 0.4).trigger('input');
      cy.wait(100);
      
      cy.get('#feedbackCircle').should('have.class', 'success');
      cy.get('#feedbackEmoji').should('contain', '✅');
    });
  });

  describe('Level Navigation', () => {
    it('should display level indicators', () => {
      cy.get('#levelIndicator .level-dot').should('have.length.at.least', 5);
      cy.get('#levelIndicator .level-dot.active').should('have.length', 1);
    });

    it('should allow jumping to different levels', () => {
      // Click on second level dot
      cy.get('#levelIndicator .level-dot').eq(1).click();
      
      // Check that function display updated (quadratic function)
      cy.get('#functionDisplay').should('contain', 'x');
      cy.get('#functionDisplay .katex').should('exist');
    });

    it('should update level display', () => {
      cy.get('#levelValue').should('contain', '1');
      
      // Jump to level 3
      cy.get('#levelIndicator .level-dot').eq(2).click();
      cy.get('#levelValue').should('contain', '3');
    });
  });

  describe('Debug Mode', () => {
    it('should show debug overlay when ?debug=1', () => {
      cy.visit('http://localhost:8002/math251/epsilon-delta.html?debug=1');
      cy.get('#debug-overlay').should('be.visible');
      cy.get('#debug-overlay').should('contain', 'DEBUG MODE');
      cy.get('#debug-math').should('contain', 'KaTeX');
    });

    it('should not show debug overlay by default', () => {
      cy.get('#debug-overlay').should('not.exist');
    });
  });

  describe('Accessibility', () => {
    it('should have skip link', () => {
      cy.get('a.visually-hidden-focusable').should('exist');
      cy.get('a.visually-hidden-focusable').should('have.attr', 'href', '#main');
    });

    it('should have proper ARIA attributes on mode tabs', () => {
      cy.get('.mode-btn[data-mode="learn"]').should('have.attr', 'role', 'tab');
      cy.get('.mode-btn[data-mode="learn"]').should('have.attr', 'aria-selected', 'true');
      cy.get('.mode-btn[data-mode="practice"]').should('have.attr', 'aria-selected', 'false');
      
      cy.get('#learnContent').should('have.attr', 'role', 'tabpanel');
    });
  });
});