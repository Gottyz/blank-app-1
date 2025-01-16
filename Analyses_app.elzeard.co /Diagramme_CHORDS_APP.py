import pandas as pd
import numpy as np
import plotly.graph_objects as go
from collections import defaultdict
import os
import math
from typing import Dict, Tuple

class ChordDiagramAnalyzer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.categories = set()
        self.visit_counts = defaultdict(int)
        self.unique_users = set()
        self.unregistered_paths = set()  # Nuevo conjunto para trackear paths no registrados

        # Definir los grupos y colores
        self.groups = {
            'Bienvenue': ['bienvenue', 'Mon Compte','account-confirm','auth','mes-fermes','nan'],
            'Paramètrer': ['Dessiner mes parcelles', 'Paramétrer ma ferme', 'Mes intrants','Semences et plants', 'Mes tâches'],
            'Planifier': ['Mes itinéraires de culture', 'Mes planifications'],
            'Cultiver': ['Plan de Culture', 'Fiches de culture', 'Mes implantations', 'Mon semainier', 'Mon prévisionnel de récoltes', 'mes-observations'],
            'Diffuser': ['Mes semences et plants', 'Ma traçabilité', 'Gestion de stock', 'Consommations intrants', 'Analyse des ventes'],
            'Tutorial': ['tutorial']
            
        }

        # Agregar grupo "Otros" para paths no registrados
        self.groups['Otros'] = []

        self.group_colors = {
              'Bienvenue': '#FF9E9E',
            'Paramètrer': '#FFD580',
            'Planifier': '#A2D5A2',
            'Cultiver': '#90CAF9',
            'Diffuser': '#C1A4D9',
            'Tutorial': '#FF0000',
            'Otros': '#FF0001',    # Color rojo intenso para Tutorial
        }   

        self.category_to_group = {}
        self.category_to_color = {}
        for group_name, categories in self.groups.items():
            for category in categories:
                self.category_to_group[category] = group_name
                self.category_to_color[category] = self.group_colors[group_name]

    def _get_category_group(self, category: str) -> str:
        """Determina el grupo de una categoría, asignando 'Otros' si no está registrada"""
        if category not in self.category_to_group:
            if category not in self.unregistered_paths:
                print(f"Path no registrado: {category}")
                self.unregistered_paths.add(category)
            return 'Otros'
        return self.category_to_group[category]

    def _get_category_color(self, category: str) -> str:
        """Determina el color de una categoría, usando el color de 'Otros' si no está registrada"""
        if category not in self.category_to_color:
            return self.group_colors['Otros']
        return self.category_to_color[category]

    def load_data(self):
        try:
            self.df = pd.read_csv(self.file_path)
            self.df['category'] = self.df['category'].astype(str)
            self.df = self.df.sort_values(['person.properties.email', 'datetime']).reset_index(drop=True)
            self.unique_users = set(self.df['person.properties.email'].unique())
            self.visit_counts = self.df.groupby('category')['person.properties.email'].nunique().to_dict()
            
            # Actualizar el grupo 'Otros' con las categorías no registradas
            unregistered = set(self.df['category'].unique()) - set(self.category_to_group.keys())
            self.groups['Otros'].extend(list(unregistered))
            for category in unregistered:
                self.category_to_group[category] = 'Otros'
                self.category_to_color[category] = self.group_colors['Otros']
                
        except Exception as e:
            print(f"Error al cargar los datos: {str(e)}")
            return None

    def analyze_transitions(self):
        try:
            categories = self.df['category'].tolist()
            emails = self.df['person.properties.email'].tolist()

            for i in range(len(categories) - 1):
                if emails[i] == emails[i + 1]:
                    source = categories[i]
                    target = categories[i + 1]

                    if source != target:
                        self.transitions[source][target] += 1
                        self.categories.add(source)
                        self.categories.add(target)

            print(f"\nAnálisis completado:")
            print(f"Número de categorías únicas: {len(self.categories)}")
            print(f"Número de usuarios únicos identificados: {len(self.unique_users)}")

            
            if self.unregistered_paths:
                print("\nPaths no registrados encontrados:")
                for path in sorted(self.unregistered_paths):
                    print(f"- {path}")
            
        except Exception as e:
            print(f"Error en el análisis de transiciones: {str(e)}")
            raise

    def create_chord_diagram(self, min_value: int = 1): 
        try:
            categories = sorted(list(self.categories))
            n = len(categories)

            node_positions = {}
            current_angle = 0

            grouped_categories = defaultdict(list)
            for cat in categories:
                group = self._get_category_group(cat)
                grouped_categories[group].append(cat)

            # Calcular las posiciones de los nodos
            for group in self.group_colors.keys():  # Usar group_colors para incluir 'Otros'
                if group in grouped_categories:
                    group_cats = grouped_categories[group]
                    angle_slice = 2 * math.pi * len(group_cats) / n
                    for i, cat in enumerate(group_cats):
                        angle = current_angle + (i * angle_slice / len(group_cats))
                        x = math.cos(angle)
                        y = math.sin(angle)
                        node_positions[cat] = (x, y)
                    current_angle += angle_slice

            fig = go.Figure()

            # Agregar las conexiones
            for source in self.transitions:
                for target, value in self.transitions[source].items():
                    if value >= min_value:
                        x0, y0 = node_positions[source]
                        x1, y1 = node_positions[target]
                        source_color = self._get_category_color(source)
                        target_color = self._get_category_color(target)

                        control_scale = 0.5
                        cx = (x0 + x1) * control_scale
                        cy = (y0 + y1) * control_scale

                        t = np.linspace(0, 1, 100)
                        x = (1-t)**2 * x0 + 2*(1-t)*t * cx + t**2 * x1
                        y = (1-t)**2 * y0 + 2*(1-t)*t * cy + t**2 * y1

                        opacity = min(0.8, value / 10)
                        width = 1 + value / 10

                        source_group = self._get_category_group(source)
                        target_group = self._get_category_group(target)

                        fig.add_trace(go.Scatter(
                            x=x, y=y,
                            mode='lines',
                            line=dict(
                                width=width,
                                color=f'rgba{tuple(int(source_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (opacity,)}',
                            ),
                            hoverinfo='text',
                            text=f'{source} ({source_group}) → {target} ({target_group}): {value}' if value > 1 else f'{source} → {target}: {value}',
                            showlegend=False
                        ))

            # Agregar los nodos
            for group_name in self.group_colors.keys():  # Usar group_colors para incluir 'Otros'
                if group_name in grouped_categories:
                    group_cats = grouped_categories[group_name]
                    node_x = []
                    node_y = []
                    node_text = []
                    node_sizes = []

                    for cat in group_cats:
                        pos = node_positions[cat]
                        visits = self.visit_counts.get(cat, 0)
                        node_x.append(pos[0])
                        node_y.append(pos[1])
                        node_text.append(f"{cat}")
                        node_sizes.append(20 + min(30, visits / 50))

                    fig.add_trace(go.Scatter(
                        x=node_x, y=node_y,
                        mode='markers+text',
                        marker=dict(
                            size=node_sizes,
                            color=self.group_colors[group_name],
                            line=dict(color='white', width=2)
                        ),
                        text=node_text,
                        textposition='middle center',
                        name=group_name,
                        hoverinfo='text',
                        showlegend=True
                    ))

            fig.update_layout(
                title=f"Diagramme de Cordes - Transitions entre catégories par groupe<br>{os.path.basename(self.file_path)}",
                showlegend=True,
                legend=dict(
                    title="Groupes",
                    yanchor="top",
                    y=0.99,
                    xanchor="right",
                    x=0.99
                ),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white',
                width=1200,
                height=1000
            )

            return fig
        except Exception as e:
            print(f"Error al crear el diagrama de cuerdas: {str(e)}")
            raise