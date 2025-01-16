import pandas as pd

class DataCleaner:
    """Classe pour nettoyer et traiter les données de navigation des utilisateurs."""
    
    def __init__(self, input_file: str):
        """
        Initialise le DataCleaner.
        
        Args:
            input_file (str): Chemin vers le fichier CSV d'entrée
        """
        self.input_file = input_file
        self.df = None
        self._setup_excluded_data()
        
    def _setup_excluded_data(self):
        """Configure les listes d'exclusion et les mappings."""
        self.excluded_emails = {
            'gilles.delaporte@gmail.com', 'rakor18295@cashbn.com', 
            'hetipab931@cpaurl.com', 'rehamap774@exoular.com',
            'support.metier@elzeard.co', 'sepesom5@confmin.com',
            'toveri9809@exoular.com', 'rehamap774@exoular.com',
            'hetipab931@cpauri.com', 'rakor18295@cashbn.com',
            'sacovah899@cironex.com', 'bamod43309@gianes.com',
            'loyopi5028@acroins.com', 'doxeyen818@nestivia.com',
            'babaxam809@chainds.com', 'yehemot246@chainds.com',
            'semoke7668@cantozil.com', 'darnala.b@gmail.com',
            'gilles.delaporte@elzeard.co', 'guillaume.caute@elzeard.co'
        }
        
        self.category_mapping = {
            'parametrage': 'Dessiner mes parcelles',
            'settings': 'Paramétrer ma ferme',
            'intrants': 'Mes intrants',
            'mytasks': 'Mes tâches',
            'itk': 'Mes itinéraires de culture',
            'plan': 'Mes planifications',
            'my-farm': 'Plan de Culture',
            'mes-cultures': 'Fiches de culture',
            'implantation': 'Mes implantations',
            'mon-calendrier': 'Mon semainier',
            'harvest': 'Mon prévisionnel de récoltes',
            'seeds': 'Mes semences et plants',
            'tracking': 'Ma traçabilité',
            'supply': 'Gestion de stock',
            'intrantdashboard': 'Consommations intrants',
            'statistics': 'Analyse des ventes',
            'account': 'Mon Compte',
            'cultivars': 'Semences et plants',
            '': 'Mon Compte',
            'mes-fermes': 'mes-fermes'
        }
    
    def _process_emails(self):
        """Traite et nettoie les emails."""
        if "person.properties.email" not in self.df.columns:
            return
            
        initial_users = self.df["person.properties.email"].nunique()
        
        self.df["person.properties.email"] = (
            self.df["person.properties.email"]
            .fillna("")
            .str.strip()
            .str.lower()
        )
        
        self.df = self.df[~self.df["person.properties.email"].isin(self.excluded_emails)]
        self.df = self.df[self.df["person.properties.email"] != ""]
        
        final_users = self.df["person.properties.email"].nunique()
        print(f"Utilisateurs uniques - Initial: {initial_users}, Final: {final_users}")
    
    def _process_datetime(self):
        """Traite les champs de date et heure."""
        if "properties.$sent_at" not in self.df.columns:
            return
            
        sent_at_split = self.df["properties.$sent_at"].str.split("T", expand=True)
        self.df[["properties.$sent_at", "start_time"]] = sent_at_split
        
        self.df["start_time"] = (
            self.df["start_time"]
            .str.split(".")
            .str[0]
            .fillna("")
            .str.replace("Z", "", regex=False)
        )
    
    def _process_categories(self):
        """Traite et mappe les catégories."""
        self.df = self.df.rename(
            columns={
                "properties.$pathname": "category",
                "properties.$sent_at": "start_date"
            }
        )
        
        self.df['category'] = (
            self.df['category']
            .fillna('')
            .apply(lambda x: x.split('/', 2)[1] if '/' in str(x) else x)
        )
        
        # Exclure les motifs spécifiques
        excluded_patterns = [r"ma-ferme"]
        pattern = '|'.join(excluded_patterns)
        self.df = self.df[~self.df["category"].str.contains(pattern, regex=True, na=False)]
        
        self.df["category"] = (
            self.df["category"]
            .map(self.category_mapping)
            .fillna(self.df["category"])
        )
    
    def _create_datetime(self):
        """Crée le champ datetime en combinant la date et l'heure."""
        mask = (
            self.df["start_date"].notna() & 
            self.df["start_time"].notna() & 
            (self.df["start_date"] != "") & 
            (self.df["start_time"] != "")
        )
        
        self.df.loc[mask, "datetime"] = pd.to_datetime(
            self.df.loc[mask, "start_date"] + " " + self.df.loc[mask, "start_time"],
            format="%Y-%m-%d %H:%M:%S",
            errors="coerce"
        )
    
    def clean_data(self) -> pd.DataFrame:
        """
        Nettoie et traite les données.
        
        Returns:
            pd.DataFrame: DataFrame nettoyé et traité
        """
        try:
            # Charger les données
            print(f"Chargement des données depuis {self.input_file}...")
            self.df = pd.read_csv(self.input_file)
            if self.df is None:
                return pd.DataFrame()
                
            lignes_initiales = len(self.df)
            users_initiaux = set(self.df["person.properties.email"].unique())
            print(f"Chargés {lignes_initiales} enregistrements avec {len(users_initiaux)} utilisateurs uniques")
            
            # Traiter les données
            self._process_emails()
            users_apres_emails = set(self.df["person.properties.email"].unique())
            
            self._process_datetime()
            users_apres_datetime = set(self.df["person.properties.email"].unique())
            
            self._process_categories()
            users_apres_categories = set(self.df["person.properties.email"].unique())
            
            self._create_datetime()
            users_apres_create_datetime = set(self.df["person.properties.email"].unique())
            
            # Backup des utilisateurs avant déduplication
            users_avant_dedup = set(self.df["person.properties.email"].unique())
            
            # Eliminer les doublons
            self.df = self.df.drop_duplicates(
                subset=["person.properties.email", "category", "datetime"]
            )
            users_finaux = set(self.df["person.properties.email"].unique())
            
            # Afficher les utilisateurs exclus à chaque étape
            print("\nUtilisateurs exclus par étape:")
            print("-" * 50)
            
            exclus_emails = users_initiaux - users_apres_emails
            if exclus_emails:
                print(f"\nExclus après traitement des emails ({len(exclus_emails)}):")
                for user in exclus_emails:
                    print(f"- {user}")
                    
            exclus_datetime = users_apres_emails - users_apres_datetime
            if exclus_datetime:
                print(f"\nExclus après traitement des dates ({len(exclus_datetime)}):")
                for user in exclus_datetime:
                    print(f"- {user}")
                    
            exclus_categories = users_apres_datetime - users_apres_categories
            if exclus_categories:
                print(f"\nExclus après traitement des catégories ({len(exclus_categories)}):")
                for user in exclus_categories:
                    print(f"- {user}")
                    
            exclus_create_datetime = users_apres_categories - users_apres_create_datetime
            if exclus_create_datetime:
                print(f"\nExclus après création datetime ({len(exclus_create_datetime)}):")
                for user in exclus_create_datetime:
                    print(f"- {user}")
                    
            exclus_dedup = users_avant_dedup - users_finaux
            if exclus_dedup:
                print(f"\nExclus après déduplication ({len(exclus_dedup)}):")
                for user in exclus_dedup:
                    print(f"- {user}")
            
            lignes_finales = len(self.df)
            print(f"\nTraitement terminé: {lignes_finales} enregistrements valides")
            print(f"Total utilisateurs initiaux: {len(users_initiaux)}")
            print(f"Total utilisateurs finaux: {len(users_finaux)}")
            print(f"Total utilisateurs exclus: {len(users_initiaux - users_finaux)}")
            
            return self.df
            
        except Exception as e:
            print(f"Erreur lors du nettoyage des données: {e}")
            return pd.DataFrame()