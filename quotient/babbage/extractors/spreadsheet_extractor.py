"""Spreadsheet text extraction for Excel and CSV files."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import openpyxl
from openpyxl.utils import get_column_letter

from ...core.config import QuotientConfig


class SpreadsheetExtractor:
    """Extract text from spreadsheet files (Excel, CSV)."""
    
    def __init__(self, config: QuotientConfig):
        """Initialize the spreadsheet extractor.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text from spreadsheet file.
        
        Args:
            file_path: Path to the spreadsheet file
            
        Returns:
            Extracted text content
        """
        self.logger.info(f"Extracting text from spreadsheet: {file_path}")
        
        try:
            if file_path.suffix.lower() == '.csv':
                return self._extract_csv_text(file_path)
            else:
                return self._extract_excel_text(file_path)
                
        except Exception as e:
            self.logger.error(f"Error extracting text from spreadsheet {file_path}: {str(e)}")
            raise
    
    def _extract_csv_text(self, file_path: Path) -> str:
        """Extract text from CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Extracted text content
        """
        try:
            # Read CSV with pandas
            df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
            
            # Convert DataFrame to text
            text_lines = []
            
            # Add headers
            headers = df.columns.tolist()
            text_lines.append(" | ".join(str(h) for h in headers))
            text_lines.append("-" * len(" | ".join(str(h) for h in headers)))
            
            # Add data rows
            for _, row in df.iterrows():
                row_text = " | ".join(str(val) for val in row.values)
                text_lines.append(row_text)
            
            return "\n".join(text_lines)
            
        except Exception as e:
            self.logger.error(f"Error extracting CSV text: {str(e)}")
            raise
    
    def _extract_excel_text(self, file_path: Path) -> str:
        """Extract text from Excel file.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Extracted text content
        """
        try:
            # Read Excel with pandas
            excel_file = pd.ExcelFile(file_path)
            
            text_parts = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                if not df.empty:
                    # Add sheet name
                    text_parts.append(f"Sheet: {sheet_name}")
                    text_parts.append("=" * 50)
                    
                    # Add headers
                    headers = df.columns.tolist()
                    text_parts.append(" | ".join(str(h) for h in headers))
                    text_parts.append("-" * len(" | ".join(str(h) for h in headers)))
                    
                    # Add data rows
                    for _, row in df.iterrows():
                        row_text = " | ".join(str(val) for val in row.values)
                        text_parts.append(row_text)
                    
                    text_parts.append("")  # Empty line between sheets
            
            return "\n".join(text_parts)
            
        except Exception as e:
            self.logger.error(f"Error extracting Excel text: {str(e)}")
            raise
    
    def extract_tables(self, file_path: Path) -> List[List[List[str]]]:
        """Extract tables from spreadsheet.
        
        Args:
            file_path: Path to the spreadsheet file
            
        Returns:
            List of tables
        """
        tables = []
        
        try:
            if file_path.suffix.lower() == '.csv':
                tables = self._extract_csv_tables(file_path)
            else:
                tables = self._extract_excel_tables(file_path)
                
        except Exception as e:
            self.logger.warning(f"Failed to extract tables: {str(e)}")
        
        return tables
    
    def _extract_csv_tables(self, file_path: Path) -> List[List[List[str]]]:
        """Extract tables from CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            List of tables
        """
        try:
            df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
            
            # Convert DataFrame to table format
            table = []
            
            # Add headers
            table.append([str(col) for col in df.columns])
            
            # Add data rows
            for _, row in df.iterrows():
                table.append([str(val) for val in row.values])
            
            return [table]
            
        except Exception as e:
            self.logger.error(f"Error extracting CSV tables: {str(e)}")
            return []
    
    def _extract_excel_tables(self, file_path: Path) -> List[List[List[str]]]:
        """Extract tables from Excel file.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            List of tables
        """
        tables = []
        
        try:
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                if not df.empty:
                    # Convert DataFrame to table format
                    table = []
                    
                    # Add headers
                    table.append([str(col) for col in df.columns])
                    
                    # Add data rows
                    for _, row in df.iterrows():
                        table.append([str(val) for val in row.values])
                    
                    tables.append(table)
                    
        except Exception as e:
            self.logger.error(f"Error extracting Excel tables: {str(e)}")
        
        return tables
    
    def get_sheet_names(self, file_path: Path) -> List[str]:
        """Get sheet names from Excel file.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            List of sheet names
        """
        try:
            if file_path.suffix.lower() == '.csv':
                return ['Sheet1']  # CSV files have one sheet
            
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
            
        except Exception as e:
            self.logger.error(f"Error getting sheet names: {str(e)}")
            return []
    
    def get_sheet_info(self, file_path: Path) -> Dict[str, Any]:
        """Get information about sheets in the spreadsheet.
        
        Args:
            file_path: Path to the spreadsheet file
            
        Returns:
            Dictionary with sheet information
        """
        info = {}
        
        try:
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
                info['Sheet1'] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'columns_list': df.columns.tolist()
                }
            else:
                excel_file = pd.ExcelFile(file_path)
                
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    info[sheet_name] = {
                        'rows': len(df),
                        'columns': len(df.columns),
                        'columns_list': df.columns.tolist()
                    }
                    
        except Exception as e:
            self.logger.error(f"Error getting sheet info: {str(e)}")
        
        return info 