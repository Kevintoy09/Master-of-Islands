from app import app
import logging
import sys
import traceback

# Initialiser les fichiers de données au démarrage
try:
    from init_data_files import init_data_files
    init_data_files()
except Exception as e:
    print(f"⚠️ Erreur lors de l'initialisation des fichiers de données: {e}")

if __name__ == "__main__":
    try:
        # Réduire les logs de développement
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)  # Réduire les logs de routine
        
        print("Démarrage du serveur Flask...")
        print("Serveur en écoute sur http://localhost:5000")
        # Activer debug temporairement pour diagnostiquer les crashes
        # use_reloader=False pour éviter que les ticks auto se désactivent
        app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\nArrêt du serveur demandé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"[ERREUR CRITIQUE] Crash du serveur Flask: {e}")
        print(f"[TRACEBACK] {traceback.format_exc()}")
        print("[INFO] Redémarrez le serveur pour continuer")
        sys.exit(1)
