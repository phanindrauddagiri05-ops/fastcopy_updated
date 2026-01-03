"""
Sitemap Configuration for FastCopy
Defines URL structure for search engines to crawl public pages
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """
    Sitemap for static/public pages
    Includes: Home, Services, About, Contact, Privacy, Terms
    Excludes: Auth pages, Cart, Checkout, Payments, Dealer Dashboard
    """
    
    # How often pages change (always, hourly, daily, weekly, monthly, yearly, never)
    changefreq = "weekly"
    
    # Default priority (0.0 to 1.0)
    priority = 0.5

    def items(self):
        """Return list of URL names for public pages"""
        return [
            'home',              # Homepage
            'services',          # Services listing
            'about',             # About page
            'contact',           # Contact page
            'privacy_policy',    # Privacy Policy
            'terms_conditions',  # Terms & Conditions
        ]

    def location(self, item):
        """Generate URL path for each item"""
        return reverse(item)
    
    def priority(self, item):
        """Set priority based on page importance"""
        priorities = {
            'home': 1.0,           # Highest priority for homepage
            'services': 0.9,       # High priority for main service page
            'about': 0.6,          # Medium priority
            'contact': 0.6,        # Medium priority
            'privacy_policy': 0.4, # Lower priority
            'terms_conditions': 0.4, # Lower priority
        }
        return priorities.get(item, 0.5)
    
    def changefreq(self, item):
        """Set change frequency based on page type"""
        frequencies = {
            'home': 'daily',           # Homepage updates frequently
            'services': 'weekly',      # Services may change weekly
            'about': 'monthly',        # About page rarely changes
            'contact': 'monthly',      # Contact info rarely changes
            'privacy_policy': 'yearly', # Legal docs change rarely
            'terms_conditions': 'yearly', # Legal docs change rarely
        }
        return frequencies.get(item, 'monthly')
