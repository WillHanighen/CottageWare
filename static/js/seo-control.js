/**
 * SEO Control Script
 * 
 * This script only adds a robots meta tag to prevent indexing on development environments.
 * SEO meta tags should be added manually to pages that need to be indexed.
 */
document.addEventListener('DOMContentLoaded', function() {
  const hostname = window.location.hostname;
  
  // Check if we're in a development or staging environment
  if (hostname.includes('onrender.com') || hostname.includes('localhost') || hostname.includes('127.0.0.1')) {
    // For development/staging environments - prevent indexing
    const meta = document.createElement('meta');
    meta.setAttribute('name', 'robots');
    meta.setAttribute('content', 'noindex, nofollow');
    document.head.appendChild(meta);
    console.log("Added robots meta tag to prevent indexing on non-production domain");
  }
});
