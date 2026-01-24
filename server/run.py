from app import app
import logging
import sys
import traceback

# init_data_files supprimé - plus nécessaire

if __name__ == "__main__":
    try:
        # Réduire les logs de développement
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)  # Réduire les logs de routine
        
        print("Démarrage du serveur Flask...")
        print("Serveur en écoute sur http://localhost:5000")
        # MODE PRODUCTION : pas de debug, pas de reloader
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\nArrêt du serveur demandé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"[ERREUR CRITIQUE] Crash du serveur Flask: {e}")
        print(f"[TRACEBACK] {traceback.format_exc()}")
        print("[INFO] Redémarrez le serveur pour continuer")
        sys.exit(1)
