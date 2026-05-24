// Maestro i18n (Internationalization) Handler
// Hybrid approach: JavaScript-based translation without template changes

class MaestroTranslator {
    constructor() {
        this.translations = {};
        this.currentLang = this.getStoredLanguage() || this.detectBrowserLanguage();
        this.defaultLang = 'en';
    }

    getStoredLanguage() {
        return localStorage.getItem('maestro_language');
    }

    detectBrowserLanguage() {
        const browserLang = navigator.language || navigator.userLanguage;
        const langCode = browserLang.split('-')[0]; // 'it-IT' -> 'it'
        return ['en', 'it'].includes(langCode) ? langCode : 'en';
    }

    async loadTranslations() {
        try {
            const response = await fetch('/static/translations.json');
            this.translations = await response.json();
            return true;
        } catch (error) {
            console.error('Failed to load translations:', error);
            return false;
        }
    }

    translate(key) {
        const lang = this.translations[this.currentLang];
        if (!lang) return key;
        return lang[key] || this.translations[this.defaultLang][key] || key;
    }

    setLanguage(langCode) {
        if (!this.translations[langCode]) {
            console.warn(`Language '${langCode}' not available`);
            return false;
        }
        this.currentLang = langCode;
        localStorage.setItem('maestro_language', langCode);
        this.applyTranslations();
        return true;
    }

    applyTranslations() {
        // Translate elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translated = this.translate(key);
            
            // Preserve emoji icons if present
            const emojiMatch = el.textContent.match(/^(\p{Emoji}+)\s*/u);
            if (emojiMatch) {
                el.textContent = `${emojiMatch[1]} ${translated}`;
            } else {
                el.textContent = translated;
            }
        });

        // Translate placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = this.translate(key);
        });

        // Translate titles/tooltips
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            el.title = this.translate(key);
        });

        // Update language selector if exists
        const langSelector = document.getElementById('language-selector');
        if (langSelector) {
            langSelector.value = this.currentLang;
        }
    }

    createLanguageSelector() {
        // Create language selector HTML
        const selector = document.createElement('div');
        selector.style.cssText = 'text-align: center; margin: 10px 0; padding: 10px; border-top: 1px solid #34495e;';
        selector.innerHTML = `
            <label for="language-selector" style="margin-right: 8px; color: #ecf0f1;">
                🌐 <span data-i18n="language">Language</span>:
            </label>
            <select id="language-selector" style="background-color: #34495e; color: #ecf0f1; border: 1px solid #2c3e50; padding: 5px 10px; border-radius: 5px; cursor: pointer;">
                <option value="en">English</option>
                <option value="it">Italiano</option>
            </select>
        `;
        
        // Insert before footer or at end of container
        const container = document.querySelector('.container');
        const footer = container.querySelector('.mpd-actions-small:last-child');
        if (footer) {
            container.insertBefore(selector, footer);
        } else {
            container.appendChild(selector);
        }

        // Add change event
        document.getElementById('language-selector').addEventListener('change', (e) => {
            this.setLanguage(e.target.value);
        });

        // Set initial value
        document.getElementById('language-selector').value = this.currentLang;
    }

    async initialize() {
        const loaded = await this.loadTranslations();
        if (!loaded) {
            console.error('Translation system failed to initialize');
            return false;
        }

        // Create language selector
        this.createLanguageSelector();

        // Apply initial translations
        this.applyTranslations();

        return true;
    }
}

// Global instance
let maestroTranslator = null;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTranslator);
} else {
    initTranslator();
}

async function initTranslator() {
    maestroTranslator = new MaestroTranslator();
    await maestroTranslator.initialize();
}
