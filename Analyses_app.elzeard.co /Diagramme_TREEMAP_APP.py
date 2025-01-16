import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict
import plotly.io as pio
import os

pio.renderers.default = "browser"

class TemporalFlow:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None
        self.transitions = defaultdict(int)
        self.categories = set()

    def load_data(self):
        try:
            self.df = pd.read_csv(self.file_path)
            self.df['datetime'] = pd.to_datetime(self.df['datetime'], errors='coerce')
            self.df['category'] = self.df['category'].astype(str)
            self.df = self.df.sort_values(['person.properties.email', 'datetime']).reset_index(drop=True)
            self.categories = set(self.df['category'].unique())
        except Exception as e:
            print(f"Error loading data: {str(e)}")

    def create_user_journey(self):
        if self.df is None:
            raise ValueError("Dataframe is not loaded. Please call load_data() before create_user_journey().")
        try:
            self.transitions = defaultdict(int)
            for _, user_data in self.df.groupby('person.properties.email'):
                user_data = user_data.sort_values('datetime')
                for i in range(len(user_data) - 1):
                    category_from = user_data.iloc[i]['category']
                    category_to = user_data.iloc[i + 1]['category']
                    if category_from != category_to:
                        self.transitions[(category_from, category_to)] += 1

            groups = {
             'Bienvenue': ['bienvenue', 'mes-fermes', 'Mon Compte', 'account-confirm'],
                'Paramètrer': ['Dessiner mes parcelles', 'Paramétrer ma ferme', 'Mes intrants', 'Semences et plants', 'Mes tâches'],
                'Planifier': ['Mes itinéraires de culture', 'Mes planifications'],
                'Cultiver': ['Plan de Culture', 'Fiches de culture', 'Mes implantations', 'Mon semainier', 'Mon prévisionnel de récoltes', 'mes-observations'],
                'Diffuser': ['Mes semences et plants', 'Ma traçabilité', 'Gestion de stock', 'Consommations intrants', 'Analyse des ventes'],
                'Tutorial': ['tutorial']
            }

            labels = []
            parents = []
            values = []
            hover_texts = []
            colors = []

            group_colors = {
                'Bienvenue': '#FF9E9E',        # Rojo claro apagado
                'Paramètrer': '#FFD580',  # Naranja claro apagado
                'Planifier': '#A2D5A2',         # Verde suave pastel
                'Cultiver': '#90CAF9',         # Azul claro apagado
                'Diffuser': '#C1A4D9',            # Lila claro
                'Tutorial': '#FFFF99'            # Amarillo claro
            }

            for group_name in groups.keys():
                labels.append(group_name)
                parents.append('')
                total_visits = len(self.df[self.df['category'].isin(groups[group_name])])
                values.append(total_visits)
                hover_texts.append(f"{group_name}<br>Total Visits: {total_visits}")
                colors.append(group_colors.get(group_name, '#000000'))  # Default to black if not found

            # Agregar las categorías dentro de cada grupo
            for group_name, categories in groups.items():
                for category in categories:
                    if category in self.df['category'].unique():
                        labels.append(category)
                        parents.append(group_name)
                        total_visits = len(self.df[self.df['category'] == category])
                        unique_users = len(self.df[self.df['category'] == category]['person.properties.email'].unique())
                        transitions_out = sum(self.transitions.get((category, cat), 0) for cat in self.categories if cat != category)
                        transitions_in = sum(self.transitions.get((cat, category), 0) for cat in self.categories if cat != category)
                        
                        hover_text = (f"Category: {category}<br>"
                                      f"Total Visits: {total_visits}<br>"
                                      f"Unique Users: {unique_users}<br>"
                                      f"Transitions Out: {transitions_out}<br>"
                                      f"Transitions In: {transitions_in}")
                        hover_texts.append(hover_text)
                        colors.append(group_colors.get(group_name, '#000000'))

            fig = go.Figure(data=[go.Treemap(
                labels=labels,
                parents=parents,
                values=values,
                branchvalues="total",
                hovertemplate="%{text}<extra></extra>",
                text=hover_texts,
                texttemplate="%{label}<br>%{value}",
                textposition="middle center",
                marker=dict(colors=colors)
            )])

            fig.update_layout(
                title={
                    'text': f"Parcours utilisateur par groupes : PageViews<br>{os.path.basename(self.file_path)}",
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'size': 24}
                },
                width=1000,
                height=800,
                margin=dict(t=100, b=100)
            )

            return fig

        except Exception as e:
            print(f"Error in create_user_journey: {str(e)}")
            raise


pass