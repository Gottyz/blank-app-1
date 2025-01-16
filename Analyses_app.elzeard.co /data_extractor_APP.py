import psycopg2
import json
import csv
from datetime import datetime
from tabulate import tabulate

class DataExtractor:
    def __init__(self, db_config_path='Analyses_app.elzeard.co /config/database.json', queries_config_path='Analyses_app.elzeard.co /config/queries.json'):
        self.db_config = self._load_config(db_config_path)
        self.queries_config = self._load_config(queries_config_path)
        self.connection = None
        self.cursor = None

    def _load_config(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except Exception as error:
            print(f"Error loading configuration file {file_path}: {error}")
            return None

    def _parse_date(self, date_str):
        """Convert date string from config to datetime object"""
        return datetime.strptime(date_str, '%Y-%m-%d')

    def connect(self):
        try:
            if not self.db_config:
                raise ValueError("Database configuration is not loaded properly.")
            
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                database=self.db_config['dbname'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                port=self.db_config.get('port')
            )
            self.cursor = self.connection.cursor()
            print("Successfully connected to PostgreSQL database")
            return True
        except Exception as error:
            print(f"Error connecting to PostgreSQL database: {error}")
            return False

    def extract_data(self, query_name, output_path):
        try:
            if not self.connection:
                if not self.connect():
                    return False

            if not self.queries_config:
                print("Queries configuration is not loaded properly.")
                return False

            query_config = self.queries_config.get(query_name)
            if not query_config:
                print(f"Query configuration not found for: {query_name}")
                return False

            start_date = self._parse_date(query_config['date_range']['start_date'])
            end_date = self._parse_date(query_config['date_range']['end_date'])

            print(f"Extracting data from {start_date} to {end_date}")
            if self.cursor:
                self.cursor.execute(query_config['query'], (start_date, end_date))
                results = self.cursor.fetchall()
            else:
                print("Cursor is not initialized.")
                return False

            if results:
                formatted_results = tabulate(results, headers=query_config['headers'], tablefmt="grid")
                print(formatted_results)

                with open(output_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(query_config['headers'])
                    for row in results:
                        writer.writerow(row)

                print(f"Results exported to: {output_path}")
                return True
            else:
                print("No results found for the specified date range.")
                return False

        except Exception as error:
            print(f"Error during execution: {error}")
            return False
        finally:
            self.close()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("PostgreSQL database connection closed...")