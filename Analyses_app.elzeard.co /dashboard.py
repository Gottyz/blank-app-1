import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from DataCleaner_APP import DataCleaner            
from Diagramme_CHORDS_APP import ChordDiagramAnalyzer  

def main():
    # Configuración de la página
    st.set_page_config(
        page_title="Dashboard Elzeard",
        page_icon="📊",
        layout="wide"
    )
    
    # Obtener rutas absolutas
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "input.csv")
    output_dir = os.path.join(current_dir, "output")
    output_file = os.path.join(output_dir, "app.elzeard.co.csv")
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Título y descripción
    st.title("Dashboard Elzeard - Analyse de Navigation")
    st.markdown("---")
    
    # Sidebar para controles
    with st.sidebar:
        st.header("Configuration")
        
        # Selector de fecha
        date_range = st.date_input(
            "Sélectionner la période",
            value=(datetime.now().date() - timedelta(days=7), datetime.now().date())
        )
        
        # Botón para actualizar
        if st.button("Actualiser les données"):
            st.session_state.update_data = True
        
        min_value = st.slider(
            "Valeur minimum pour les connexions",
            min_value=1,
            max_value=10,
            value=1
        )
    
    # Contenedor principal
    main_container = st.container()
    
    with main_container:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            try:
                # Verificar si el archivo existe
                if not os.path.exists(input_file):
                    st.error(f"Le fichier d'entrée n'existe pas: {input_file}")
                    return
                
                # Limpiar datos
                with st.spinner("Nettoyage des données en cours..."):
                    cleaner = DataCleaner(input_file)
                    df_clean = cleaner.clean_data()
                    
                    # Guardar datos limpios
                    df_clean.to_csv(output_file, index=False)
                    
                # Crear y mostrar diagrama
                with st.spinner("Création du diagramme..."):
                    chord_analyzer = ChordDiagramAnalyzer(output_file)
                    chord_analyzer.load_data()
                    chord_analyzer.analyze_transitions()
                    fig = chord_analyzer.create_chord_diagram(min_value=min_value)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
            except Exception as e:
                st.error(f"Erreur lors du traitement: {str(e)}")
        
        with col2:
            if 'df_clean' in locals() and df_clean is not None:
                # Métricas
                st.subheader("Métriques")
                
                # Asegurarse de que las columnas existan
                email_col = "person.properties.email" if "person.properties.email" in df_clean.columns else None
                
                if email_col:
                    total_users = df_clean[email_col].nunique()
                    total_views = len(df_clean)
                    avg_views_per_user = total_views / total_users if total_users > 0 else 0
                    
                    st.metric("Utilisateurs uniques", total_users)
                    st.metric("Vues totales", total_views)
                    st.metric("Vues moyennes par utilisateur", f"{avg_views_per_user:.2f}")
                
                # Top categorías
                if "category" in df_clean.columns:
                    st.subheader("Top Catégories")
                    top_categories = df_clean["category"].value_counts().head(10)
                    st.bar_chart(top_categories)

if __name__ == "__main__":
    main()