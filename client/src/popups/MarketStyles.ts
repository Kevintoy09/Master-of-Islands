// Styles centralisés pour le marché
export const marketStyles = {
  // En-tête
  header: {
    padding: '15px 20px',
    background: 'linear-gradient(to bottom, #DEB887, #CD853F)',
    borderBottom: '2px solid #8B4513',
    borderTopLeftRadius: '9px',
    borderTopRightRadius: '9px',
    textAlign: 'center' as const
  },

  title: {
    margin: '0 0 10px 0',
    color: '#8B4513',
    fontSize: '20px',
    textShadow: '1px 1px 2px rgba(0, 0, 0, 0.3)'
  },

  infoContainer: {
    display: 'flex',
    justifyContent: 'center',
    gap: '20px',
    marginTop: '8px'
  },

  infoCard: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    padding: '6px 12px',
    background: 'rgba(255, 255, 255, 0.3)',
    borderRadius: '6px',
    border: '1px solid rgba(139, 69, 19, 0.3)'
  },

  infoLabel: {
    fontSize: '10px',
    color: '#8B4513',
    fontWeight: 'bold',
    textTransform: 'uppercase' as const
  },

  infoValue: {
    fontSize: '14px',
    color: '#2C1810',
    fontWeight: 'bold'
  },

  // Onglets
  tabs: {
    display: 'flex',
    background: '#D3D3D3',
    borderBottom: '3px solid #8B4513',
    margin: 0,
    padding: 0,
    position: 'relative' as const
  },

  tab: {
    flex: 1,
    padding: '12px 16px',
    border: '2px solid #8B4513',
    borderBottom: 'none',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 'bold',
    textAlign: 'center' as const,
    outline: 'none',
    borderTopLeftRadius: '8px',
    borderTopRightRadius: '8px',
    marginBottom: '-3px',
    transition: 'all 0.3s ease'
  },

  // Contenu principal
  content: {
    padding: '20px',
    background: 'linear-gradient(135deg, #FFFEF7, #F5F5DC)',
    borderBottomLeftRadius: '9px',
    borderBottomRightRadius: '9px',
    maxHeight: '450px',
    overflowY: 'auto' as const,
    boxShadow: 'inset 0 2px 8px rgba(139, 69, 19, 0.1)'
  },

  // États de chargement et vides
  loading: {
    textAlign: 'center' as const,
    padding: '40px',
    color: '#8B4513'
  },

  empty: {
    textAlign: 'center' as const,
    padding: '40px',
    background: 'linear-gradient(135deg, rgba(220, 220, 220, 0.3), rgba(200, 200, 200, 0.1))',
    borderRadius: '12px',
    border: '2px dashed rgba(139, 69, 19, 0.3)',
    color: '#8B4513',
    fontSize: '16px'
  },

  // Sections de contenu
  sectionTitle: {
    margin: '0 0 20px 0',
    color: '#8B4513',
    fontSize: '20px',
    borderBottom: '3px solid rgba(139, 69, 19, 0.3)',
    paddingBottom: '10px',
    textShadow: '1px 1px 2px rgba(0, 0, 0, 0.1)',
    textTransform: 'uppercase' as const,
    letterSpacing: '1px',
    background: 'linear-gradient(135deg, rgba(139, 69, 19, 0.1), rgba(139, 69, 19, 0.05))',
    padding: '15px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px'
  },

  // Container principal de tab
  tabContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '20px'
  },

  // Liste des offres
  offersList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '15px',
    maxHeight: '300px',
    overflowY: 'auto' as const
  },

  // Carte d'offre (mes offres)
  myOfferCard: {
    background: 'linear-gradient(135deg, #fff 0%, #f8f9fa 100%)',
    border: '3px solid rgba(139, 69, 19, 0.2)',
    borderRadius: '16px',
    padding: '20px',
    transition: 'all 0.3s ease',
    boxShadow: '0 6px 20px rgba(139, 69, 19, 0.15)',
    position: 'relative' as const,
    overflow: 'hidden',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },

  // Barre latérale verte
  offerSidebar: {
    position: 'absolute' as const,
    top: 0,
    left: 0,
    width: '6px',
    height: '100%',
    background: 'linear-gradient(to bottom, #4CAF50, #45a049)'
  },

  // Info d'offre
  offerInfo: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
    flex: 1,
    marginLeft: '15px'
  },

  offerTitle: {
    color: '#8B4513',
    fontSize: '18px',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    gap: '10px'
  },

  offerPrice: {
    color: '#666',
    fontSize: '14px',
    padding: '6px 12px',
    background: 'rgba(139, 69, 19, 0.08)',
    borderRadius: '8px',
    borderLeft: '4px solid rgba(139, 69, 19, 0.3)'
  },

  offerTotal: {
    color: '#28a745',
    fontSize: '16px',
    fontWeight: 'bold',
    padding: '8px 12px',
    background: 'rgba(40, 167, 69, 0.1)',
    borderRadius: '8px',
    borderLeft: '4px solid #28a745'
  },

  offerDate: {
    color: '#999',
    fontSize: '12px',
    fontStyle: 'italic',
    background: 'rgba(153, 153, 153, 0.1)',
    padding: '4px 8px',
    borderRadius: '6px'
  },

  // Bouton annuler
  cancelButton: {
    padding: '12px 20px',
    background: 'linear-gradient(135deg, #DC3545, #C82333)',
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    textTransform: 'uppercase' as const,
    letterSpacing: '1px',
    minWidth: '100px',
    boxShadow: '0 4px 12px rgba(220, 53, 69, 0.4)'
  },

  // Formulaire de vente
  sellForm: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '20px',
    background: 'rgba(255, 255, 255, 0.5)',
    padding: '25px',
    borderRadius: '16px',
    border: '3px solid rgba(139, 69, 19, 0.15)',
    boxShadow: '0 6px 20px rgba(139, 69, 19, 0.1)'
  },

  formField: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '10px'
  },

  label: {
    fontWeight: 'bold',
    color: '#8B4513',
    fontSize: '15px',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },

  input: {
    padding: '14px 18px',
    border: '2px solid rgba(139, 69, 19, 0.2)',
    borderRadius: '10px',
    fontSize: '16px',
    background: 'white',
    transition: 'all 0.3s ease',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)'
  },

  // Résumé de l'offre
  offerSummary: {
    background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(76, 175, 80, 0.05))',
    border: '3px solid rgba(76, 175, 80, 0.3)',
    borderRadius: '16px',
    padding: '20px',
    margin: '15px 0',
    position: 'relative' as const,
    boxShadow: '0 4px 15px rgba(76, 175, 80, 0.2)'
  },

  summaryIcon: {
    position: 'absolute' as const,
    top: '-15px',
    left: '25px',
    background: 'white',
    padding: '8px 15px',
    borderRadius: '20px',
    fontSize: '20px',
    border: '3px solid rgba(76, 175, 80, 0.3)',
    boxShadow: '0 2px 8px rgba(76, 175, 80, 0.3)'
  },

  summaryRow: {
    marginBottom: '10px',
    fontSize: '15px',
    color: '#333',
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px 0',
    borderBottom: '1px solid rgba(76, 175, 80, 0.2)',
    fontWeight: '500'
  },

  summaryTotal: {
    marginBottom: '0',
    fontSize: '18px',
    color: '#2C5530',
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px 0',
    fontWeight: 'bold'
  },

  // Bouton créer offre
  createOfferButton: {
    padding: '18px 30px',
    border: 'none',
    borderRadius: '12px',
    fontSize: '18px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    textTransform: 'uppercase' as const,
    letterSpacing: '2px',
    position: 'relative' as const,
    overflow: 'hidden',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px'
  },

  // Offres d'achat
  buyOfferCard: {
    background: 'linear-gradient(135deg, #fff 0%, #f8f9fa 100%)',
    border: '2px solid rgba(139, 69, 19, 0.2)',
    borderRadius: '12px',
    padding: '30px',
    transition: 'all 0.3s ease',
    boxShadow: '0 4px 12px rgba(139, 69, 19, 0.1)',
    position: 'relative' as const,
    overflow: 'hidden',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },

  buyOfferSidebar: {
    position: 'absolute' as const,
    top: 0,
    left: 0,
    width: '4px',
    height: '100%',
    background: 'linear-gradient(to bottom, #007BFF, #0056B3)'
  },

  buyOfferInfo: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '10px',
    flex: 1,
    marginLeft: '15px'
  },

  buyOfferTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px'
  },

  buyOfferTitleText: {
    color: '#8B4513',
    fontSize: '20px',
    fontWeight: 'bold'
  },

  buyOfferDetails: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '10px',
    fontSize: '16px',
    color: '#666'
  },

  buyOfferTag: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '4px 10px',
    borderRadius: '6px'
  },

  buyOfferSecondary: {
    display: 'flex',
    gap: '15px',
    fontSize: '14px',
    color: '#999',
    marginTop: '5px'
  },

  // Bouton acheter
  buyButton: {
    padding: '15px 25px',
    background: 'linear-gradient(135deg, #28A745, #218838)',
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
    minWidth: '120px',
    boxShadow: '0 3px 8px rgba(40, 167, 69, 0.4)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px'
  },

  // Liste scrollable pour achats
  buyOffersList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
    maxHeight: '350px',
    overflowY: 'auto' as const
  }
};
