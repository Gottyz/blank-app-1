import os
from data_extractor_APP import DataExtractor
from Diagramme_CHORDS_APP import ChordDiagramAnalyzer
from Diagramme_TREEMAP_APP import TemporalFlow
from DataCleaner_APP import DataCleaner

def main():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        input_file = os.path.join(current_dir, "input.csv")
        output_dir = os.path.join(current_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        # Step 1: Extract data from database
        print("Starting data extraction...")
        extractor = DataExtractor()
        if not extractor.extract_data('user_navigation', input_file):
            print("Data extraction failed. Stopping process.")
            return
        
        if not os.path.exists(input_file):
            print("No input file was generated. Stopping process.")
            return

        # Step 2: Clean data
        print("\nStarting data cleaning...")
        cleaner = DataCleaner(input_file)
        cleaned_df = cleaner.clean_data()
        if cleaned_df.empty:
            print("Cleaning resulted in empty DataFrame. Stopping process.")
            return
            
        cleaned_file = os.path.join(output_dir, "app.elzeard.co.csv")
        cleaned_df.to_csv(cleaned_file, index=False)
        print(f"Cleaned data saved to: {cleaned_file}")

        # Step 3: Generate temporal flow diagram
        print("\nGenerating temporal flow diagram...")
        try:
            flow = TemporalFlow(cleaned_file)
            flow.load_data()
            flow_fig = flow.create_user_journey()
            flow_output = os.path.join(output_dir, "temporal_flow.html")
            flow_fig.write_html(flow_output)
            flow_fig.show()
            print(f"Temporal flow diagram saved to: {flow_output}")
        except Exception as e:
            print(f"Error generating temporal flow diagram: {e}")

        # Step 4: Generate chord diagram
        print("\nGenerating chord diagram...")
        try:
            analyzer = ChordDiagramAnalyzer(cleaned_file)
            analyzer.load_data()
            analyzer.analyze_transitions()
            chord_fig = analyzer.create_chord_diagram(min_value=1)
            chord_output = os.path.join(output_dir, "chord_diagram.html")
            chord_fig.write_html(chord_output)
            chord_fig.show()
            print(f"Chord diagram saved to: {chord_output}")
        except Exception as e:
            print(f"Error generating chord diagram: {e}")

        print("\nProcess completed successfully!")
        
    except Exception as e:
        print(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    main()