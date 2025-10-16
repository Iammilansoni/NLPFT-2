(function() {
  'use strict';
  
  if (typeof window === 'undefined') return;
  
  const originalError = console.error;
  
  console.error = function(...args) {
    
    if (
      typeof args[0] === 'string' &&
      (
        args[0].includes('Hydration failed') ||
        args[0].includes('hydrated but some attributes') ||
        args[0].includes('did not match') ||
        args[0].includes('fdprocessedid') ||
        args[0].includes('data-new-gr-c-s-check-loaded') ||
        args[0].includes('data-gr-ext-installed') ||
        args[0].includes('data-lastpass-icon-root')
      )
    ) {
      
      return;
    }
    
    
    originalError.apply(console, args);
  };
})();
