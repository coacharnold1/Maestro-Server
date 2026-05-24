#!/usr/bin/env python3
"""
Translate install-maestro.sh to Italian
"""

# Translation dictionary - English to Italian
translations = {
    # Headers and titles
    "Complete Installation Script": "Script di Installazione Completo",
    "INSTALLER v2.0": "INSTALLATORE v2.0",
    "Complete Music Server with Web UI and Admin Interface": "Server Musicale Completo con Interfaccia Web e Pannello Admin",
    
    # Common messages
    "Cannot detect OS. Unsupported system.": "Impossibile rilevare il sistema operativo. Sistema non supportato.",
    "Please do NOT run this script as root!": "Per favore NON eseguire questo script come root!",
    "Run as normal user. Sudo will be used when needed.": "Esegui come utente normale. Sudo verrà utilizzato quando necessario.",
    
    # MPD Section
    "MPD Installation Check": "Verifica Installazione MPD",
    "Found existing MPD:": "MPD esistente trovato:",
    "Version:": "Versione:",
    "Type:": "Tipo:",
    "System package": "Pacchetto di sistema",
    "Custom/Local build": "Build personalizzata/locale",
    "Use existing MPD": "Usa MPD esistente",
    "Install new MPD from package manager": "Installa nuovo MPD dal package manager",
    "Skip MPD installation": "Salta installazione MPD",
    "Choice": "Scelta",
    "No existing MPD found": "Nessun MPD esistente trovato",
    "Install MPD from package manager?": "Installare MPD dal package manager?",
    "Using existing MPD": "Uso MPD esistente",
    "Will install MPD package": "Verrà installato il pacchetto MPD",
    "MPD installation skipped": "Installazione MPD saltata",
    
    # Directory Configuration
    "Directory Configuration": "Configurazione Directory",
    "Found:": "Trovato:",
    "Use this directory?": "Usare questa directory?",
    "Enter music directory:": "Inserisci directory musica:",
    "Music directory": "Directory musica",
    "default": "predefinito",
    "Recent Albums Directory (Optional)": "Directory Album Recenti (Opzionale)",
    "Enter the FULL PATH to where recent albums are located.": "Inserisci il PERCORSO COMPLETO dove si trovano gli album recenti.",
    "Example:": "Esempio:",
    "This should be the complete path, not relative to music directory": "Questo dovrebbe essere il percorso completo, non relativo alla directory musicale",
    "Note:": "Nota:",
    "will always be included for CD rips": "sarà sempre incluso per i rip dei CD",
    "Recent albums directory:": "Directory album recenti:",
    "Leave empty to skip": "Lascia vuoto per saltare",
    "Press Enter to continue": "Premi Invio per continuare",
    
    # Theme Selection
    "Theme Selection": "Selezione Tema",
    "Available themes:": "Temi disponibili:",
    "Dark (default)": "Scuro (predefinito)",
    "Light": "Chiaro",
    "Ocean": "Oceano",
    "Sunset": "Tramonto",
    "Forest": "Foresta",
    "Midnight": "Mezzanotte",
    "Choose theme": "Scegli tema",
    
    # Installation Steps
    "Installing system dependencies": "Installazione dipendenze di sistema",
    "Installing MPD": "Installazione MPD",
    "Configuring MPD": "Configurazione MPD",
    "Installing Python dependencies": "Installazione dipendenze Python",
    "Creating systemd services": "Creazione servizi systemd",
    "Starting services": "Avvio servizi",
    "Updating package lists": "Aggiornamento elenchi pacchetti",
    "Installing packages": "Installazione pacchetti",
    "Installed": "Installato",
    "Failed to install": "Installazione fallita",
    "Creating directory": "Creazione directory",
    "Directory created": "Directory creata",
    "Directory already exists": "Directory già esistente",
    
    # MPD Configuration
    "Configuring MPD for user": "Configurazione MPD per utente",
    "Created MPD configuration": "Configurazione MPD creata",
    "Configuring audio output": "Configurazione output audio",
    "Found audio device": "Dispositivo audio trovato",
    "No audio devices found, using ALSA default": "Nessun dispositivo audio trovato, uso predefinito ALSA",
    "Starting MPD service": "Avvio servizio MPD",
    "MPD started successfully": "MPD avviato con successo",
    "Waiting for MPD to initialize": "Attesa inizializzazione MPD",
    "Updating MPD database": "Aggiornamento database MPD",
    
    # Web UI Setup
    "Setting up Web UI": "Configurazione Interfaccia Web",
    "Creating virtual environment": "Creazione ambiente virtuale",
    "Installing Python packages": "Installazione pacchetti Python",
    "Creating settings file": "Creazione file impostazioni",
    "Web UI configured": "Interfaccia Web configurata",
    
    # Admin Setup
    "Setting up Admin Interface": "Configurazione Interfaccia Admin",
    "Admin interface configured": "Interfaccia Admin configurata",
    
    # Service Creation
    "Creating systemd service files": "Creazione file servizi systemd",
    "Created": "Creato",
    "Enabling services": "Abilitazione servizi",
    "Starting Web UI service": "Avvio servizio Interfaccia Web",
    "Starting Admin service": "Avvio servizio Admin",
    "Services started successfully": "Servizi avviati con successo",
    
    # CD Ripping Setup
    "Setting up CD ripping": "Configurazione ripping CD",
    "Installing CD ripping tools": "Installazione strumenti ripping CD",
    "Creating CD rip directory": "Creazione directory rip CD",
    "Creating udev rule for automatic CD detection": "Creazione regola udev per rilevamento automatico CD",
    "CD ripping configured": "Ripping CD configurato",
    
    # Sudo Configuration
    "Configuring sudo permissions": "Configurazione permessi sudo",
    "Sudo permissions configured": "Permessi sudo configurati",
    
    # Final Messages
    "MAESTRO INSTALLATION COMPLETE!": "INSTALLAZIONE MAESTRO COMPLETATA!",
    "INSTALLATION COMPLETED SUCCESSFULLY!": "INSTALLAZIONE COMPLETATA CON SUCCESSO!",
    "Installation Summary": "Riepilogo Installazione",
    "Music Directory:": "Directory Musica:",
    "Recent Albums:": "Album Recenti:",
    "Theme:": "Tema:",
    "Web UI:": "Interfaccia Web:",
    "Admin Panel:": "Pannello Admin:",
    "MPD:": "MPD:",
    "running": "in esecuzione",
    "stopped": "fermato",
    "not installed": "non installato",
    "Service Status:": "Stato Servizi:",
    "Running": "In Esecuzione",
    "Not running": "Non in esecuzione",
    "Installation Directory:": "Directory Installazione:",
    "Symlink to:": "Link simbolico a:",
    "Access URLs:": "URL di Accesso:",
    "Service Management:": "Gestione Servizi:",
    "Add Music:": "Aggiungi Musica:",
    "Copy music to:": "Copia musica in:",
    "Subdirectories inside /media/music will appear in Recent Albums": "Le sottodirectory dentro /media/music appariranno in Album Recenti",
    "Or mount network shares inside": "Oppure monta condivisioni di rete dentro",
    "Use FTP to organize ripped CDs:": "Usa FTP per organizzare i CD rippati:",
    "Update MPD library:": "Aggiorna libreria MPD:",
    "Logs:": "Log:",
    "Next Steps:": "Prossimi Passi:",
    "Open": "Apri",
    "to configure system": "per configurare il sistema",
    "Add network shares in Library Management": "Aggiungi condivisioni di rete in Gestione Libreria",
    "Configure audio settings in Audio Tweaks": "Configura impostazioni audio in Regolazioni Audio",
    "to play music!": "per riprodurre musica!",
    "Detected OS:": "Sistema Operativo rilevato:",
    
    # Access Information
    "Access your music server at:": "Accedi al tuo server musicale su:",
    "Web Player:": "Player Web:",
    "Admin Interface:": "Interfaccia Admin:",
    "Default credentials:": "Credenziali predefinite:",
    "Username:": "Nome utente:",
    "Password:": "Password:",
    "CHANGE THE DEFAULT PASSWORD IMMEDIATELY!": "CAMBIA LA PASSWORD PREDEFINITA IMMEDIATAMENTE!",
    
    # Tips
    "Quick Tips:": "Suggerimenti Rapidi:",
    "View logs:": "Visualizza log:",
    "Restart services:": "Riavvia servizi:",
    "Update Maestro:": "Aggiorna Maestro:",
    
    # Common words
    "Yes": "Sì",
    "No": "No",
    "Error": "Errore",
    "Warning": "Avviso",
    "Success": "Successo",
    "Failed": "Fallito",
    "Checking": "Controllo",
    "Installing": "Installazione",
    "Configuring": "Configurazione",
    "Creating": "Creazione",
    "Starting": "Avvio",
    "Stopping": "Arresto",
    "Restarting": "Riavvio",
    "Updating": "Aggiornamento",
    "Completed": "Completato",
    "Skipped": "Saltato",
    "Optional": "Opzionale",
    "Required": "Richiesto",
    "Loading": "Caricamento",
    "Waiting": "Attesa",
}

def translate_file(input_file, output_file):
    """Translate the installer file"""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply translations
    for english, italian in translations.items():
        content = content.replace(english, italian)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Translated {input_file} → {output_file}")
    print(f"  Applied {len(translations)} translations")

if __name__ == '__main__':
    translate_file('install-maestro.sh', 'install-maestro-it.sh')
